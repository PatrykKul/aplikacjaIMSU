# ruff: noqa: E501  (narration texts are content, not code)
"""Generate the two demo videos (MP4) in `app/demo/assets/` from lesson slides and a narrator.

One-off tool: every video starts with a title slide (so the player shows it before playing
instead of a black frame), then lesson slides narrated by pl-PL-ZofiaNeural (the same voice
as the audio blocks, see `generate_audio.py`). The generated files are committed, so the
seed needs nothing extra. Requires `edge-tts`, `imageio-ffmpeg` and Pillow, which are NOT
project dependencies (install them in a separate tools venv), then from `backend/`:

    <tools-venv>\\Scripts\\python -m app.demo.generate_videos
"""

import re
import subprocess
import tempfile
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

from app.demo.generate_audio import synthesize

ASSETS = Path(__file__).resolve().parent / "assets"
FONTS = Path("C:/Windows/Fonts")
PAUSE = 0.6  # seconds of silence after each slide

# file -> (title, subtitle, [(slide image, narration), ...])
VIDEOS: dict[str, tuple[str, str, list[tuple[str, str]]]] = {
    "m_film.mp4": (
        "Funkcja liniowa w skrócie",
        "Wzór, wykres, nachylenie i miejsce zerowe",
        [
            (
                "m1_schemat.png",
                "Funkcja liniowa ma wzór: y równa się a razy x plus b. Litera b to wyraz wolny, a litera a to współczynnik kierunkowy.",
            ),
            (
                "m1_wykres.png",
                "Na wykresie liczba b pokazuje, gdzie prosta przecina oś y. Tutaj b równa się jeden. Współczynnik a równa się dwa, więc krok w prawo o jeden to krok w górę o dwa.",
            ),
            (
                "m2_nachylenie.png",
                "Gdy a jest dodatnie, funkcja rośnie. Gdy a jest ujemne, funkcja maleje. Im większe a, tym bardziej stroma prosta.",
            ),
            (
                "m3_miejsce_zerowe.png",
                "Miejsce zerowe to punkt, w którym wykres przecina oś x. Dla funkcji y równa się dwa x minus cztery jest to x równa się dwa.",
            ),
        ],
    ),
    "p_film.mp4": (
        "Pętla for krok po kroku",
        "Jak działa pętla for i czym różni się while",
        [
            (
                "p1_schemat_for.png",
                "Pętla for powtarza ten sam kod dla kolejnych wartości. Najpierw i równa się jeden. Program sprawdza, czy i jest nie większe niż pięć.",
            ),
            (
                "p1_kod.png",
                "Jeśli tak, wykonuje ciało pętli i zwiększa i o jeden. Ten program dodaje kolejne liczby do sumy. Po pięciu obrotach suma wynosi piętnaście.",
            ),
            (
                "p2_schemat_while.png",
                "Pętla while też sprawdza warunek przed każdym obrotem, ale zmienną z warunku trzeba zmieniać samodzielnie. Inaczej pętla nigdy się nie skończy.",
            ),
        ],
    ),
}


def title_slide(title: str, subtitle: str, target: Path) -> None:
    image = Image.new("RGB", (1200, 750), "#1e3a8a")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 690, 1200, 750], fill="#2563eb")
    draw.text(
        (600, 330),
        title,
        font=ImageFont.truetype(str(FONTS / "segoeuib.ttf"), 64),
        fill="white",
        anchor="mm",
    )
    draw.text(
        (600, 420),
        subtitle,
        font=ImageFont.truetype(str(FONTS / "segoeui.ttf"), 32),
        fill="#bfdbfe",
        anchor="mm",
    )
    draw.text((600, 720), "IMSU · materiał wideo z lektorem", font=ImageFont.truetype(str(FONTS / "segoeui.ttf"), 22),
              fill="white", anchor="mm")  # fmt: skip
    image.save(target)


def duration(ffmpeg: str, path: Path) -> float:
    out = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)], capture_output=True,
                         text=True, encoding="utf-8", errors="replace").stderr  # fmt: skip
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def build(name: str, title: str, subtitle: str, slides: list[tuple[str, str]], ffmpeg: str,
          work: Path) -> None:  # fmt: skip
    stem = Path(name).stem
    cover = work / f"{stem}_title.png"
    title_slide(title, subtitle, cover)
    parts = [(cover, f"{title}. {subtitle}."), *((ASSETS / img, text) for img, text in slides)]
    segments = []
    for index, (image, text) in enumerate(parts):
        speech = work / f"{stem}_{index}.mp3"
        synthesize(text, speech, bitrate="96k")
        length = duration(ffmpeg, speech) + PAUSE
        segment = work / f"{stem}_{index}.mp4"
        subprocess.run(
            [
                ffmpeg, "-y", "-loglevel", "error",
                "-loop", "1", "-framerate", "25", "-i", str(image),
                "-i", str(speech),
                "-t", f"{length:.2f}",
                "-vf", "scale=1152:720,pad=1280:720:64:0:white,format=yuv420p",
                "-c:v", "libx264", "-tune", "stillimage", "-r", "25",
                "-af", "apad", "-c:a", "aac", "-b:a", "96k", "-ar", "44100", "-ac", "1",
                str(segment),
            ],
            check=True,
        )  # fmt: skip
        segments.append(segment)
    listing = work / f"{stem}.txt"
    listing.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    subprocess.run(
        [ffmpeg, "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(listing),
         "-c", "copy", "-movflags", "+faststart", str(ASSETS / name)],
        check=True,
    )  # fmt: skip
    print("ok", name, f"{duration(ffmpeg, ASSETS / name):.1f}s")


def main() -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        for name, (title, subtitle, slides) in VIDEOS.items():
            build(name, title, subtitle, slides, ffmpeg, Path(tmp))


if __name__ == "__main__":
    main()
