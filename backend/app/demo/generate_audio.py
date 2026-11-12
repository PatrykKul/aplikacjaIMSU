"""Record the A-version recordings of the demo courses as MP3 files in `app/demo/assets/`.

One-off tool: every `Audio` block in `courses.py` has a `script` of turns; each part of a turn
is spoken by a neural voice (edge-tts, online), trimmed of silence and joined with short gaps
(between parts of one turn) or longer ones (between turns). The result is mono MP3, 24 kHz.
The generated files are committed, so the seed needs nothing extra. Requires `edge-tts` and
`imageio-ffmpeg`, which are NOT project dependencies (install them in a separate tools venv),
then from `backend/`:

    <tools-venv>\\Scripts\\python -m app.demo.generate_audio          # all recordings
    <tools-venv>\\Scripts\\python -m app.demo.generate_audio m1 e2    # only matching files

Synthesized parts are cached in %TEMP%/imsu-tts-cache, so editing one line re-records only it.
"""

import asyncio
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import edge_tts
import imageio_ffmpeg

from app.demo.courses import ASSETS_DIR as ASSETS
from app.demo.courses import COURSES, Audio, audio_blocks

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
PART_GAP = 0.15  # seconds between parts of one turn (e.g. before an English example)
TURN_GAP = 0.5  # seconds between turns
SAMPLE_RATE = 24000
BITRATE = "32k"
TRIM = "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.03"


def ffmpeg(*args: str) -> None:
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", *args], check=True)


def part_wav(voice: str, text: str) -> Path:
    """Spoken `text` as WAV without silence at either end (cached)."""
    key = hashlib.sha1(f"{VOICES[voice]}|{RATES[voice]}|{text}".encode()).hexdigest()[:16]
    target = CACHE / f"{key}.wav"
    if target.exists():
        return target
    raw = CACHE / f"{key}.mp3"
    for attempt in range(3):
        try:
            asyncio.run(edge_tts.Communicate(text, VOICES[voice], rate=RATES[voice]).save(str(raw)))
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
    return target


def silence(seconds: float, folder: Path) -> Path:
    target = folder / f"silence_{seconds}.wav"
    if not target.exists():
        ffmpeg(
            "-f", "lavfi", "-i", f"anullsrc=r={SAMPLE_RATE}:cl=mono",
            "-t", str(seconds), str(target),
        )  # fmt: skip
    return target


def record(block: Audio) -> float:
    """Write the MP3 of `block`; returns its length in seconds."""
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        pieces: list[Path] = []
        for turn_index, turn in enumerate(block.script):
            if turn_index:
                pieces.append(silence(TURN_GAP, folder))
            for part_index, (voice, text) in enumerate(turn):
                if part_index:
                    pieces.append(silence(PART_GAP, folder))
                pieces.append(part_wav(voice, text))
        listing = folder / "list.txt"
        listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in pieces), encoding="utf-8")
        target = ASSETS / block.file
        ffmpeg(
            "-f", "concat", "-safe", "0", "-i", str(listing),
            "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "libmp3lame", "-b:a", BITRATE,
            str(target),
        )  # fmt: skip
    return duration(target)


def duration(path: Path) -> float:
    result = subprocess.run([FFMPEG, "-i", str(path)], capture_output=True, text=True)
    match = re.search(r"Duration: (\d+):(\d+):([\d.]+)", result.stderr)
    if not match:
        return 0.0
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def main() -> None:
    CACHE.mkdir(exist_ok=True)
    only = sys.argv[1:]
    for block in audio_blocks(COURSES):
        if only and not any(block.file.startswith(prefix) for prefix in only):
            continue
        seconds = record(block)
        size = (ASSETS / block.file).stat().st_size // 1024
        print(f"ok {block.file}  {int(seconds // 60)}:{int(seconds % 60):02d}  {size} KB")


if __name__ == "__main__":
    main()
