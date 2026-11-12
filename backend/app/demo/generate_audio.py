"""Record the A-version recordings of the demo courses as MP3 files in `app/demo/assets/`.

One-off tool: every `Audio` block in `courses.py` has a `script` of turns; each line of a turn
is spoken by a neural voice (edge-tts, online), trimmed of silence and joined with short gaps
(between lines of one turn) or longer ones (between turns). The result is mono MP3, 24 kHz.
The generated files are committed, so the seed needs nothing extra. Requires `edge-tts` and
`imageio-ffmpeg`, which are NOT project dependencies (install them in a separate tools venv),
then from `backend/`:

    <tools-venv>\\Scripts\\python -m app.demo.generate_audio          # all recordings
    <tools-venv>\\Scripts\\python -m app.demo.generate_audio m1 e2    # only matching files

Completeness check: edge-tts reports every word it has read (`WordBoundary`); the words of
each line must match the words of its spoken text exactly, otherwise the run fails. Lengths are
checked against D58 (sections 30-50 s, recap 20-30 s). A full run (no arguments) also deletes
MP3 files in `assets/` that no recording uses. Synthesized lines are cached in
%TEMP%/imsu-tts-cache (audio and heard words), so editing one line re-records only it.
"""

import asyncio
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import imageio_ffmpeg

from app.demo.courses import ASSETS_DIR as ASSETS
from app.demo.courses import COURSES, Audio, Line, audio_blocks

CACHE = Path(tempfile.gettempdir()) / "imsu-tts-cache"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

VOICES = {
    "Z": "pl-PL-ZofiaNeural",  # teacher
    "M": "pl-PL-MarekNeural",  # student
    "EN": "en-GB-SoniaNeural",  # English examples
    "EN2": "en-GB-RyanNeural",
}
# A little slower than default: easier to follow while learning
RATES = {"Z": "-4%", "M": "-2%", "EN": "-8%", "EN2": "-8%"}
PART_GAP = 0.15  # seconds between lines of one turn (e.g. before an English example)
TURN_GAP = 0.5  # seconds between turns
SAMPLE_RATE = 24000
BITRATE = "32k"
TRIM = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.03"
# Lengths from D58, in seconds
SECTION = (30.0, 50.0)
RECAP = (20.0, 30.0)

WORD = re.compile(r"[\w']+")


def words(text: str) -> list[str]:
    return [word.lower() for word in WORD.findall(text.replace("’", "'"))]


def ffmpeg(*args: str) -> None:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


async def _synthesize(text: str, voice: str, target: Path) -> list[str]:
    """MP3 of `text` and the words edge-tts reports as read."""
    communicate = edge_tts.Communicate(
        text, VOICES[voice], rate=RATES[voice], boundary="WordBoundary"
    )
    heard: list[str] = []
    with target.open("wb") as stream:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                stream.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                heard.append(chunk["text"])
    return heard


def line_wav(line: Line) -> tuple[Path, list[str]]:
    """Spoken line as WAV without silence at either end, and the words heard (cached)."""
    text = line.spoken
    key = hashlib.sha1(f"wb|{VOICES[line.voice]}|{RATES[line.voice]}|{text}".encode()).hexdigest()
    target = CACHE / f"{key[:16]}.wav"
    heard_file = CACHE / f"{key[:16]}.json"
    if target.exists() and heard_file.exists():
        return target, json.loads(heard_file.read_text(encoding="utf-8"))
    raw = CACHE / f"{key[:16]}.mp3"
    heard: list[str] = []
    for attempt in range(3):
        try:
            heard = asyncio.run(_synthesize(text, line.voice, raw))
            break
        except Exception:  # network hiccups of the online service
            if attempt == 2:
                raise
    # trim the start, reverse, trim the (former) end, reverse back
    ffmpeg(
        "-i", str(raw), "-af", f"{TRIM},areverse,{TRIM},areverse",
        "-ac", "1", "-ar", str(SAMPLE_RATE), str(target),
    )  # fmt: skip
    raw.unlink()
    heard_file.write_text(json.dumps(heard, ensure_ascii=False), encoding="utf-8")
    return target, heard


def silence(seconds: float, folder: Path) -> Path:
    target = folder / f"silence_{seconds}.wav"
    if not target.exists():
        ffmpeg(
            "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
            "-t", str(seconds), str(target),
        )  # fmt: skip
    return target


@dataclass
class Report:
    file: str
    seconds: float
    lines: int
    expected: int  # words in the spoken text
    heard: int  # words edge-tts reported as read
    problems: list[str]


def record(block: Audio) -> Report:
    """Write the MP3 of `block` and check that every line was read in full."""
    problems: list[str] = []
    expected = heard_total = lines = 0
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        pieces: list[Path] = []
        for turn_index, turn in enumerate(block.script):
            if turn_index:
                pieces.append(silence(TURN_GAP, folder))
            for line_index, line in enumerate(turn.lines):
                if line_index:
                    pieces.append(silence(PART_GAP, folder))
                wav, heard = line_wav(line)
                pieces.append(wav)
                want, got = words(line.spoken), words(" ".join(heard))
                lines += 1
                expected += len(want)
                heard_total += len(got)
                if want != got:
                    problems.append(f"{line.voice}: oczekiwano {want}, przeczytano {got}")
        listing = folder / "list.txt"
        listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
        target = ASSETS / block.file
        ffmpeg(
            "-f", "concat", "-safe", "0", "-i", str(listing),
            "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "libmp3lame", "-b:a", BITRATE,
            str(target),
        )  # fmt: skip
    seconds = duration(target)
    low, high = RECAP if block.recap else SECTION
    if not low <= seconds <= high:
        problems.append(f"długość {seconds:.1f} s poza zakresem {low:.0f}–{high:.0f} s")
    return Report(block.file, seconds, lines, expected, heard_total, problems)


def duration(path: Path) -> float:
    result = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", result.stderr)
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def remove_unused(used: set[str]) -> None:
    for path in sorted(ASSETS.glob("*.mp3")):
        if path.name not in used:
            path.unlink()
            print(f"usunięto nieużywany plik {path.name}")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    CACHE.mkdir(exist_ok=True)
    only = sys.argv[1:]
    blocks = audio_blocks(COURSES)
    failed = 0
    total = 0
    for block in blocks:
        if only and not any(block.file.startswith(prefix) for prefix in only):
            continue
        report = record(block)
        size = (ASSETS / block.file).stat().st_size // 1024
        total += size
        status = "ok" if not report.problems else "BŁĄD"
        print(
            f"{status:4} {report.file:28} {report.seconds:5.1f} s  {size:4} KB  "
            f"fragmenty {report.lines:2}  słowa {report.heard}/{report.expected}"
        )
        for problem in report.problems:
            print(f"     {problem}")
        failed += bool(report.problems)
    if not only:
        remove_unused({block.file for block in blocks})
    print(f"razem {total} KB, z problemami: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
