# ruff: noqa: E501  (narration texts are content, not code)
"""Generate the two demo videos (MP4) in `app/demo/assets/` from lesson slides and a narrator.

One-off tool (Windows): the narrator is the Polish system voice "Microsoft Paulina Desktop"
(System.Speech through PowerShell) and the video is assembled with ffmpeg. The generated
files are committed, so the seed needs nothing extra. Requires the `imageio-ffmpeg` package
(bundled ffmpeg), which is NOT a project dependency:

    %TEMP%\\assets-venv\\Scripts\\pip install imageio-ffmpeg
    %TEMP%\\assets-venv\\Scripts\\python app/demo/generate_videos.py
"""

import subprocess
import tempfile
import wave
from pathlib import Path

import imageio_ffmpeg

ASSETS = Path(__file__).resolve().parent / "assets"
VOICE = "Microsoft Paulina Desktop"
PAUSE = 0.7  # seconds of silence after each slide

VIDEOS: dict[str, list[tuple[str, str]]] = {
    "m_film.mp4": [
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
    "p_film.mp4": [
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
}

SPEAK = """
Add-Type -AssemblyName System.Speech
$s = New-Object System.Speech.Synthesis.SpeechSynthesizer
$s.SelectVoice('{voice}')
$s.SetOutputToWaveFile('{wav}')
$s.Speak((Get-Content -Raw -Encoding UTF8 '{text}'))
$s.Dispose()
"""


def speak(text: str, wav: Path, work: Path) -> float:
    """Synthesize `text` to `wav`; returns its length in seconds."""
    text_file = work / f"{wav.stem}.txt"
    text_file.write_text(text, encoding="utf-8")
    script = SPEAK.format(voice=VOICE, wav=wav, text=text_file)
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True)
    with wave.open(str(wav)) as audio:
        return audio.getnframes() / audio.getframerate()


def build(name: str, slides: list[tuple[str, str]], ffmpeg: str, work: Path) -> None:
    segments = []
    for index, (image, text) in enumerate(slides):
        wav = work / f"{Path(name).stem}_{index}.wav"
        duration = speak(text, wav, work) + PAUSE
        segment = work / f"{Path(name).stem}_{index}.mp4"
        subprocess.run(
            [
                ffmpeg,
                "-y",
                "-loglevel",
                "error",
                "-loop",
                "1",
                "-framerate",
                "25",
                "-i",
                str(ASSETS / image),
                "-i",
                str(wav),
                "-t",
                f"{duration:.2f}",
                "-vf",
                "scale=1152:720,pad=1280:720:64:0:white,format=yuv420p",
                "-c:v",
                "libx264",
                "-tune",
                "stillimage",
                "-r",
                "25",
                "-af",
                "apad",
                "-c:a",
                "aac",
                "-b:a",
                "96k",
                "-ar",
                "44100",
                "-ac",
                "1",
                str(segment),
            ],
            check=True,
        )
        segments.append(segment)
    listing = work / f"{Path(name).stem}.txt"
    listing.write_text("".join(f"file '{s.as_posix()}'\n" for s in segments), encoding="utf-8")
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listing),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(ASSETS / name),
        ],
        check=True,
    )
    print("ok", name)


def main() -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    with tempfile.TemporaryDirectory() as tmp:
        for name, slides in VIDEOS.items():
            build(name, slides, ffmpeg, Path(tmp))


if __name__ == "__main__":
    main()
