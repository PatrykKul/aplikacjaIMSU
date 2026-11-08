"""Record the audio blocks of the demo courses as MP3 files in `app/demo/assets/`.

One-off tool: the voice is the neural Polish voice pl-PL-ZofiaNeural (edge-tts, online),
leading silence is trimmed with ffmpeg. The generated files are committed, so the seed
needs nothing extra. Requires `edge-tts` and `imageio-ffmpeg`, which are NOT project
dependencies (install them in a separate tools venv), then from `backend/`:

    <tools-venv>\\Scripts\\python -m app.demo.generate_audio
"""

import asyncio
import subprocess
import tempfile
from pathlib import Path

import edge_tts
import imageio_ffmpeg

from app.demo.courses import COURSES, speech_blocks, speech_file

ASSETS = Path(__file__).resolve().parent / "assets"
VOICE = "pl-PL-ZofiaNeural"
RATE = "-5%"  # a little slower than default: easier to follow while learning


def synthesize(text: str, target: Path, *, bitrate: str = "64k") -> None:
    """Speak `text` into an MP3 without leading silence (mono, 24 kHz)."""
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.mp3"
        asyncio.run(edge_tts.Communicate(text, VOICE, rate=RATE).save(str(raw)))
        subprocess.run(
            [
                ffmpeg, "-y", "-loglevel", "error", "-i", str(raw),
                # drop silence at the start (anything quieter than -45 dB)
                "-af", "silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.05",
                "-ac", "1", "-ar", "24000", "-c:a", "libmp3lame", "-b:a", bitrate,
                str(target),
            ],
            check=True,
        )  # fmt: skip


def main() -> None:
    for course in COURSES:
        for lesson_index, block in speech_blocks(course):
            name = speech_file(course, lesson_index, block)
            synthesize(block.transcript, ASSETS / name)
            print("ok", name)


if __name__ == "__main__":
    main()
