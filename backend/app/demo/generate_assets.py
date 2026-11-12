# ruff: noqa: E501  (worksheet texts are content, not code; keeping sentences whole)
"""Generate the demo images (PNG, V versions) and worksheets (PDF, K versions) in `app/demo/assets/`.

One-off tool: the generated files are committed, so the seed (`python -m app.demo.seed`)
needs nothing extra. Regenerating requires Pillow, which is NOT a project dependency
(install it in a separate tools venv), then from `backend/`:

    <tools-venv>\\Scripts\\python -m app.demo.generate_assets

Fonts: Segoe UI and Consolas from Windows (Polish letters). Worksheets are A4 pages at 150 dpi
with the answers on the last page.
"""

import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont

from app.demo.courses import ASSETS_DIR as ASSETS

FONTS = "C:/Windows/Fonts"

W, H = 1200, 750
BG = "#ffffff"
INK = "#1e293b"
MUTED = "#64748b"
LINE = "#cbd5e1"
GRID = "#e2e8f0"
AXIS = "#334155"
BLUE = "#2563eb"
ORANGE = "#ea580c"
GREEN = "#15803d"
PURPLE = "#7c3aed"
RED = "#dc2626"
SOFT = {
    BLUE: "#eff6ff",
    ORANGE: "#fff7ed",
    GREEN: "#f0fdf4",
    PURPLE: "#f5f3ff",
    RED: "#fef2f2",
    MUTED: "#f8fafc",
}
CODE_BG = "#0f172a"


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    name = (
        ("consolab.ttf" if bold else "consola.ttf")
        if mono
        else ("segoeuib.ttf" if bold else "segoeui.ttf")
    )
    return ImageFont.truetype(f"{FONTS}/{name}", size)


def canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw.text((48, 30), title, font=font(38, bold=True), fill=INK)
    if subtitle:
        draw.text((48, 82), subtitle, font=font(23), fill=MUTED)
    return image, draw


def save(image: Image.Image, name: str) -> None:
    image.save(ASSETS / name, optimize=True)
    print("ok", name)


def wrap(text: str, typeface: ImageFont.FreeTypeFont, width: float) -> list[str]:
    lines: list[str] = []
    for paragraph in text.split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = f"{current} {word}" if current else word
            if typeface.getlength(candidate) <= width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def note(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    lines: Sequence[str],
    color: str,
    width: int = 500,
    size: int = 25,
    title: str = "",
) -> int:
    """Light panel with a colored bar on the left; returns its bottom edge."""
    step = size + 13
    height = 26 + step * len(lines) + (step if title else 0)
    draw.rectangle([x, y, x + width, y + height], fill=SOFT[color])
    draw.rectangle([x, y, x + 6, y + height], fill=color)
    top = y + 14
    if title:
        draw.text((x + 24, top), title, font=font(size, bold=True), fill=color)
        top += step
    for i, text in enumerate(lines):
        draw.text((x + 24, top + i * step), text, font=font(size), fill=INK)
    return y + height


def arrow(
    draw: ImageDraw.ImageDraw,
    points: Sequence[tuple[float, float]],
    color: str = AXIS,
    width: int = 4,
) -> None:
    draw.line(list(points), fill=color, width=width, joint="curve")
    (x1, y1), (x2, y2) = points[-2], points[-1]
    angle = math.atan2(y2 - y1, x2 - x1)
    tip = [
        (x2, y2),
        (x2 - 18 * math.cos(angle - 0.4), y2 - 18 * math.sin(angle - 0.4)),
        (x2 - 18 * math.cos(angle + 0.4), y2 - 18 * math.sin(angle + 0.4)),
    ]
    draw.polygon(tip, fill=color)


def minus(value: float) -> str:
    """Number with a typographic minus and a decimal comma."""
    text = f"{value:g}".replace(".", ",")
    return text.replace("-", "−")


# --- Coordinate plots ----------------------------------------------------------------------------


class Plot:
    """Grid for x in [x0, x1], y in [y0, y1] inside `box`; equal units keep slopes true."""

    def __init__(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        xs: tuple[float, float],
        ys: tuple[float, float],
        step: tuple[float, float] = (1, 1),
        equal: bool = True,
        labels: tuple[str, str] = ("x", "y"),
    ) -> None:
        self.draw, self.xs, self.ys, self.step, self.labels = draw, xs, ys, step, labels
        left, top, right, bottom = box
        ux = (right - left) / (xs[1] - xs[0])
        uy = (bottom - top) / (ys[1] - ys[0])
        if equal:
            ux = uy = min(ux, uy)
        self.ux, self.uy = ux, uy
        # center the grid in the box
        self.left = left + ((right - left) - ux * (xs[1] - xs[0])) / 2
        self.top = top + ((bottom - top) - uy * (ys[1] - ys[0])) / 2

    def p(self, x: float, y: float) -> tuple[float, float]:
        return self.left + (x - self.xs[0]) * self.ux, self.top + (self.ys[1] - y) * self.uy

    def grid(self, every: tuple[int, int] = (1, 1), tick_size: int = 18) -> None:
        d, (x0, x1), (y0, y1), (sx, sy) = self.draw, self.xs, self.ys, self.step
        xs = [x0 + i * sx for i in range(round((x1 - x0) / sx) + 1)]
        ys = [y0 + i * sy for i in range(round((y1 - y0) / sy) + 1)]
        for x in xs:
            d.line([self.p(x, y0), self.p(x, y1)], fill=GRID, width=1)
        for y in ys:
            d.line([self.p(x0, y), self.p(x1, y)], fill=GRID, width=1)
        ax = 0 if x0 <= 0 <= x1 else x0
        ay = 0 if y0 <= 0 <= y1 else y0
        arrow(d, [self.p(x0, ay), (self.p(x1, ay)[0] + 18, self.p(x1, ay)[1])], AXIS, 3)
        arrow(d, [self.p(ax, y0), (self.p(ax, y1)[0], self.p(ax, y1)[1] - 18)], AXIS, 3)
        small = font(tick_size)
        for i, x in enumerate(xs):
            if x != ax and i % every[0] == 0:
                px, py = self.p(x, ay)
                d.text((px, py + 6), minus(x), font=small, fill=MUTED, anchor="ma")
        for i, y in enumerate(ys):
            if y != ay and i % every[1] == 0:
                px, py = self.p(ax, y)
                d.text((px - 8, py), minus(y), font=small, fill=MUTED, anchor="rm")
        px, py = self.p(ax, ay)
        d.text((px - 8, py + 6), "0", font=small, fill=MUTED, anchor="ra")
        px, py = self.p(x1, ay)
        d.text((px + 8, py - 12), self.labels[0], font=font(22, bold=True), fill=AXIS, anchor="rb")
        px, py = self.p(ax, y1)
        d.text((px + 12, py - 14), self.labels[1], font=font(22, bold=True), fill=AXIS, anchor="la")

    def line(
        self,
        f: Callable[[float], float],
        color: str,
        width: int = 5,
        x_from: float | None = None,
        x_to: float | None = None,
    ) -> None:
        start = self.xs[0] if x_from is None else x_from
        end = self.xs[1] if x_to is None else x_to
        n = 400
        points = [
            (start + (end - start) * i / n, f(start + (end - start) * i / n)) for i in range(n + 1)
        ]
        points = [(x, y) for x, y in points if self.ys[0] <= y <= self.ys[1]]
        self.draw.line([self.p(x, y) for x, y in points], fill=color, width=width)

    def dot(
        self,
        x: float,
        y: float,
        color: str,
        label: str = "",
        offset: tuple[int, int] = (14, -34),
        hollow: bool = False,
        size: int = 22,
    ) -> None:
        px, py = self.p(x, y)
        if hollow:
            self.draw.ellipse(
                [px - 9, py - 9, px + 9, py + 9], fill="white", outline=color, width=4
            )
        else:
            self.draw.ellipse(
                [px - 9, py - 9, px + 9, py + 9], fill=color, outline="white", width=3
            )
        if label:
            self.draw.text(
                (px + offset[0], py + offset[1]), label, font=font(size, bold=True), fill=color
            )

    def label(
        self, x: float, y: float, text: str, color: str, size: int = 22, anchor: str = "la"
    ) -> None:
        self.draw.text(self.p(x, y), text, font=font(size, bold=True), fill=color, anchor=anchor)


def mini_table(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    rows: Sequence[Sequence[str]],
    widths: Sequence[int],
    height: int = 54,
    size: int = 26,
    accent: str = BLUE,
) -> int:
    """Simple table; the first column is the header column. Returns the bottom edge."""
    for r, row in enumerate(rows):
        left = x
        for c, cell in enumerate(row):
            box = [left, y + r * height, left + widths[c], y + (r + 1) * height]
            draw.rectangle(box, fill=SOFT[accent] if c == 0 else "white", outline=LINE, width=2)
            draw.text(
                ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2),
                cell,
                font=font(size, bold=c == 0),
                fill=accent if c == 0 else INK,
                anchor="mm",
            )
            left += widths[c]
    return y + len(rows) * height


# --- Math images ---------------------------------------------------------------------------------


def m1_graph() -> None:
    image, draw = canvas("Wykres funkcji y = 2x + 1", "Punkty z tabeli leżą na jednej prostej")
    plot = Plot(draw, (40, 140, 640, 728), (-5, 5), (-5, 5))
    plot.grid()
    plot.line(lambda x: 2 * x + 1, BLUE)
    for x in (-1, 1, 2):
        plot.dot(
            x,
            2 * x + 1,
            BLUE,
            f"({minus(x)}, {minus(2 * x + 1)})",
            offset=(16, -10) if x > 0 else (-120, -14),
        )
    plot.dot(0, 1, GREEN, "(0, 1) = (0, b)", offset=(-190, -36))
    plot.dot(1, 4, RED, "(1, 4) – poza prostą", offset=(70, -14), hollow=True, size=20)
    draw.text((690, 140), "Tabela wartości", font=font(26, bold=True), fill=INK)
    bottom = mini_table(
        draw,
        690,
        185,
        [("x", "−1", "0", "1", "2"), ("y", "−1", "1", "3", "5")],
        (110, 90, 90, 90, 90),
    )
    note(
        draw,
        690,
        bottom + 34,
        ["a = 2, b = 1", "dla x = 0 zostaje y = b = 1"],
        GREEN,
        width=470,
        title="Przecięcie z osią y",
    )
    note(
        draw,
        690,
        bottom + 230,
        ["(1, 4): 2 · 1 + 1 = 3 ≠ 4", "punkt nie należy do wykresu"],
        RED,
        width=470,
        title="Sprawdzanie punktu",
    )
    save(image, "m1_v_wykres.png")


def m1_scheme() -> None:
    image, draw = canvas("Od wzoru do wykresu", "Co oznaczają litery i jak narysować prostą")
    formula, big = "y = a · x + b", font(88, bold=True)
    start = W / 2 - big.getlength(formula) / 2
    draw.text((start, 190), formula, font=big, fill=INK, anchor="lm")

    def letter_x(letter: str) -> float:
        index = formula.index(letter)
        return start + big.getlength(formula[:index]) + big.getlength(letter) / 2

    columns = [
        (70, ORANGE, "a", ["współczynnik kierunkowy:", "o ile rośnie y,", "gdy x rośnie o 1"]),
        (450, BLUE, "x", ["argument:", "liczba, którą", "wstawiasz do wzoru"]),
        (830, GREEN, "b", ["wyraz wolny:", "prosta przecina", "oś y w punkcie (0, b)"]),
    ]
    for left, color, letter, lines in columns:
        draw.rectangle([left, 300, left + 300, 470], fill=SOFT[color])
        draw.rectangle([left, 300, left + 300, 306], fill=color)
        draw.text((left + 150, 336), letter, font=font(40, bold=True), fill=color, anchor="mm")
        for i, text in enumerate(lines):
            draw.text((left + 150, 380 + i * 30), text, font=font(23), fill=INK, anchor="mm")
        draw.line([(letter_x(letter), 245), (left + 150, 298)], fill=color, width=3)
    steps = [
        ("1", "Tabela", "wybierz 2–3 liczby x", "i policz y ze wzoru"),
        ("2", "Punkty", "zaznacz pary (x, y)", "w układzie współrzędnych"),
        ("3", "Prosta", "połącz punkty linijką", "i przedłuż – to wykres"),
    ]
    for i, (number, title, line1, line2) in enumerate(steps):
        left = 70 + i * 380
        draw.ellipse([left, 540, left + 56, 596], fill=INK)
        draw.text((left + 28, 568), number, font=font(28, bold=True), fill="white", anchor="mm")
        draw.text((left + 74, 542), title, font=font(28, bold=True), fill=INK)
        draw.text((left + 74, 586), line1, font=font(22), fill=MUTED)
        draw.text((left + 74, 616), line2, font=font(22), fill=MUTED)
        if i < 2:
            arrow(draw, [(left + 330, 568), (left + 365, 568)], LINE, 3)
    draw.text(
        (W / 2, 690),
        "Przykład: y = 2x + 1 → (0, 1), (1, 3), (2, 5)",
        font=font(26, bold=True),
        fill=BLUE,
        anchor="mm",
    )
    save(image, "m1_v_schemat.png")


def m2_direction() -> None:
    image, draw = canvas(
        "Rosnąca, malejąca, stała", "Znak liczby a mówi, w którą stronę biegnie prosta"
    )
    plot = Plot(draw, (40, 140, 640, 728), (-5, 5), (-5, 5))
    plot.grid()
    plot.line(lambda x: 2 * x, BLUE)
    plot.line(lambda x: -x + 2, ORANGE)
    plot.line(lambda x: 4, GREEN)
    plot.label(-4.8, 4.75, "y = 4", GREEN)
    plot.label(2.6, 4.75, "y = 2x", BLUE)
    plot.label(1.0, -1.7, "y = −x + 2", ORANGE)
    y = 140
    for color, title, lines in [
        (
            BLUE,
            "a > 0 – funkcja rosnąca",
            ["y = 2x: prosta idzie w górę", "(patrząc od lewej do prawej)"],
        ),
        (ORANGE, "a < 0 – funkcja malejąca", ["y = −x + 2: prosta opada"]),
        (GREEN, "a = 0 – funkcja stała", ["y = 4: pozioma prosta y = b"]),
    ]:
        y = note(draw, 680, y, lines, color, width=480, size=23, title=title) + 22
    note(
        draw,
        680,
        y,
        [
            "im większe a bez znaku, tym",
            "bardziej stromo: y = −5x jest",
            "bardziej stroma niż y = 3x",
        ],
        MUTED,
        width=480,
        size=23,
        title="Stromość",
    )
    save(image, "m2_v_kierunek.png")


def m2_slope() -> None:
    image, draw = canvas("Jak obliczyć a z dwóch punktów", "Prosta przez punkty (0, 1) i (2, 7)")
    plot = Plot(draw, (40, 140, 600, 728), (-2, 5), (-1, 9))
    plot.grid()
    plot.line(lambda x: 3 * x + 1, BLUE)
    draw.line([plot.p(0, 1), plot.p(2, 1)], fill=ORANGE, width=5)
    draw.line([plot.p(2, 1), plot.p(2, 7)], fill=PURPLE, width=5)
    plot.label(1.25, 0.85, "zmiana x = 2", ORANGE, anchor="ma")
    plot.label(2.15, 4, "zmiana y = 6", PURPLE, anchor="lm")
    plot.dot(0, 1, BLUE, "(0, 1)", offset=(-92, -36))
    plot.dot(2, 7, BLUE, "(2, 7)", offset=(-92, -30))
    note(draw, 650, 150, ["a = (y₂ − y₁) : (x₂ − x₁)"], BLUE, width=500, size=28, title="Wzór")
    draw.text((650, 300), "a = (7 − 1) : (2 − 0)", font=font(32), fill=INK)
    draw.text((650, 350), "a = 6 : 2 = 3", font=font(40, bold=True), fill=INK)
    draw.text((650, 410), "wzór prostej: y = 3x + 1", font=font(26), fill=MUTED)
    note(
        draw,
        650,
        480,
        ["w prawo o 2, w górę o 6:", "na każdy krok w prawo y rośnie o 3"],
        ORANGE,
        width=500,
        size=24,
        title="Schodek",
    )
    save(image, "m2_v_obliczanie_a.png")


def m3_zero() -> None:
    image, draw = canvas("Miejsce zerowe funkcji y = 2x − 4", "Gdzie wykres przecina oś x?")
    plot = Plot(draw, (40, 140, 640, 728), (-3, 6), (-6, 6))
    plot.grid()
    plot.line(lambda x: 2 * x - 4, ORANGE, width=6, x_to=2)
    plot.line(lambda x: 2 * x - 4, GREEN, width=6, x_from=2)
    plot.dot(2, 0, INK, "x₀ = 2", offset=(16, 30), size=26)
    plot.dot(0, -4, MUTED, "(0, −4) = (0, b)", offset=(16, -14), size=20)
    plot.label(4.1, 3.3, "y > 0", GREEN, size=26)
    plot.label(-2.6, -1.4, "y < 0", ORANGE, size=26)
    bottom = note(
        draw,
        680,
        140,
        ["2x − 4 = 0", "2x = 4", "x = 2"],
        BLUE,
        width=480,
        size=28,
        title="Wstaw y = 0",
    )
    bottom = note(
        draw,
        680,
        bottom + 24,
        ["x₀ = −b : a = −(−4) : 2 = 2"],
        PURPLE,
        width=480,
        size=24,
        title="Wzór (a ≠ 0)",
    )
    note(
        draw,
        680,
        bottom + 24,
        ["na lewo od 2: wartości ujemne", "na prawo od 2: wartości dodatnie"],
        GREEN,
        width=480,
        size=24,
        title="Znak wartości",
    )
    save(image, "m3_v_miejsce_zerowe.png")


def m3_cases() -> None:
    image, draw = canvas(
        "Ile miejsc zerowych?",
        "Funkcja liniowa ma jedno miejsce zerowe, żadnego albo nieskończenie wiele",
    )
    panels = [
        ("y = 2x − 4", "jedno: x₀ = 2", lambda x: 2 * x - 4, BLUE),
        ("y = 5", "brak – prosta nie przecina osi x", lambda x: 5, ORANGE),
        ("y = 0", "nieskończenie wiele – każdy x", lambda x: 0, GREEN),
    ]
    for i, (formula, caption, f, color) in enumerate(panels):
        left = 50 + i * 380
        plot = Plot(draw, (left, 190, left + 340, 560), (-6, 6), (-6, 6), step=(2, 2))
        plot.grid(tick_size=15)
        plot.line(f, color, width=7 if formula == "y = 0" else 5)
        if formula == "y = 2x − 4":
            plot.dot(2, 0, INK)
        draw.text((left + 170, 155), formula, font=font(30, bold=True), fill=color, anchor="mm")
        for j, text in enumerate(wrap(caption, font(23), 330)):
            draw.text((left + 170, 600 + j * 34), text, font=font(23), fill=INK, anchor="mm")
    save(image, "m3_v_przypadki.png")


def m4_taxis() -> None:
    image, draw = canvas(
        "Dwie taksówki: kiedy koszt jest równy?", "x – długość kursu w km, y – koszt w zł"
    )
    plot = Plot(
        draw, (70, 150, 680, 690), (0, 10), (0, 45), step=(1, 5), equal=False, labels=("km", "zł")
    )
    plot.grid()
    plot.line(lambda x: 3 * x + 8, BLUE)
    plot.line(lambda x: 4 * x + 2, ORANGE)
    x, y = plot.p(6, 26)
    for start in range(int(y), int(plot.p(6, 0)[1]), 16):
        draw.line([(x, start), (x, start + 8)], fill=MUTED, width=2)
    plot.dot(6, 26, INK, "(6, 26)", offset=(-104, -22), size=24)
    plot.dot(10, 38, BLUE, "38 zł", offset=(14, -8))
    plot.dot(10, 42, ORANGE, "42 zł", offset=(14, -26))
    plot.label(0.3, 41, "do 6 km: tańsza B", ORANGE, size=24)
    plot.label(6.3, 9, "powyżej 6 km:", BLUE, size=24)
    plot.label(6.3, 5.5, "tańsza A", BLUE, size=24)
    bottom = note(
        draw,
        770,
        150,
        ["start 8 zł + 3 zł za km", "y = 3x + 8"],
        BLUE,
        width=390,
        size=24,
        title="Firma A",
    )
    bottom = note(
        draw,
        770,
        bottom + 20,
        ["start 2 zł + 4 zł za km", "y = 4x + 2"],
        ORANGE,
        width=390,
        size=24,
        title="Firma B",
    )
    note(
        draw,
        770,
        bottom + 20,
        ["3x + 8 = 4x + 2", "x = 6 km, obie po 26 zł"],
        MUTED,
        width=390,
        size=24,
        title="Tyle samo",
    )
    save(image, "m4_v_taksowki.png")


def m4_candle() -> None:
    image, draw = canvas("Świeca: y = −2x + 20", "x – czas w godzinach, y – wysokość świecy w cm")
    plot = Plot(
        draw, (70, 150, 700, 690), (0, 11), (0, 22), step=(1, 2), equal=False, labels=("h", "cm")
    )
    plot.grid()
    plot.line(lambda x: -2 * x + 20, ORANGE, x_from=0, x_to=10)
    plot.dot(0, 20, ORANGE, "start: 20 cm", offset=(16, -40))
    plot.dot(3, 14, ORANGE, "po 3 h: 14 cm", offset=(16, -40))
    plot.dot(10, 0, INK, "po 10 h: 0 cm", offset=(-60, -100))
    # candle: three heights side by side
    base = 650
    for i, (hours, height) in enumerate([(0, 20), (3, 14), (10, 0)]):
        cx = 860 + i * 115
        px_height = height * 18
        if height:
            draw.rectangle(
                [cx - 24, base - px_height, cx + 24, base],
                fill="#fde68a",
                outline="#d97706",
                width=3,
            )
            top = base - px_height
            draw.line([(cx, top), (cx, top - 14)], fill=INK, width=3)
            draw.ellipse([cx - 11, top - 46, cx + 11, top - 12], fill="#f97316")
            draw.ellipse([cx - 5, top - 34, cx + 5, top - 16], fill="#fde047")
        else:
            draw.rectangle([cx - 30, base - 6, cx + 30, base], fill="#d97706")
        draw.text((cx, base + 18), f"{hours} h", font=font(24, bold=True), fill=INK, anchor="ma")
        draw.text((cx, base + 50), f"{height} cm", font=font(22), fill=MUTED, anchor="ma")
    draw.text(
        (970, 140),
        "a = −2: ubywa 2 cm na godzinę",
        font=font(22, bold=True),
        fill=ORANGE,
        anchor="ma",
    )
    draw.text((970, 172), "miejsce zerowe x = 10", font=font(22), fill=INK, anchor="ma")
    save(image, "m4_v_swieca.png")


# --- English images ------------------------------------------------------------------------------


def chips(
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    words: Sequence[tuple[str, str | None]],
    size: int = 28,
    height: int = 58,
    gap: int = 10,
) -> float:
    """Words in boxes; (word, color) – color None is a neutral box. Returns the right edge."""
    for word, color in words:
        typeface = font(size, bold=color is not None)
        width = typeface.getlength(word) + 34
        fill = SOFT[color] if color else "#f8fafc"
        outline = color if color else LINE
        draw.rectangle(
            [x, y, x + width, y + height], fill=fill, outline=outline, width=3 if color else 2
        )
        draw.text(
            (x + width / 2, y + height / 2), word, font=typeface, fill=color or INK, anchor="mm"
        )
        x += width + gap
    return x


def e1_structure() -> None:
    image, draw = canvas(
        "Present Perfect: budowa zdania", "osoba + have / has + trzecia forma czasownika (V3)"
    )
    # legend: colors of the sentence parts
    x = 150.0
    for text, color in (
        ("osoba", PURPLE),
        ("have / has", BLUE),
        ("V3", ORANGE),
        ("reszta zdania", MUTED),
    ):
        draw.rectangle([x, 134, x + 16, 150], fill=color)
        draw.text((x + 24, 142), text, font=font(21, bold=True), fill=color, anchor="lm")
        x += 24 + font(21, bold=True).getlength(text) + 28
    rows = [
        (
            "+",
            [
                ("I / You / We / They", PURPLE),
                ("have", BLUE),
                ("finished", ORANGE),
                ("my homework.", None),
            ],
        ),
        (
            "+",
            [("He / She / It", PURPLE), ("has", BLUE), ("finished", ORANGE), ("the test.", None)],
        ),
        ("−", [("She", PURPLE), ("hasn't", BLUE), ("called", ORANGE), ("me.", None)]),
        ("?", [("Have", BLUE), ("you", PURPLE), ("finished", ORANGE), ("your homework?", None)]),
    ]
    for r, (sign, words) in enumerate(rows):
        top = 170 + r * 92
        draw.text((90, top + 29), sign, font=font(44, bold=True), fill=INK, anchor="mm")
        chips(draw, 150, top, words)
    note(
        draw,
        90,
        552,
        ["Yes, I have.  /  No, I haven't.", "Yes, she has.  /  No, she hasn't."],
        BLUE,
        width=520,
        size=25,
        title="Krótkie odpowiedzi",
    )
    note(
        draw,
        650,
        552,
        ["I've = I have,  she's = she has", "(gdy dalej stoi V3: She's visited Rome)"],
        ORANGE,
        width=500,
        size=23,
        title="Skróty",
    )
    save(image, "e1_v_budowa.png")


def e1_forms() -> None:
    image, draw = canvas("Trzecia forma czasownika (V3)", "W Present Perfect zawsze V3 – nie V2")
    left, top, widths, height = 130, 140, (300, 300, 340), 54
    header = ("forma podstawowa", "V2 (Past Simple)", "V3 (Present Perfect)")
    x = left
    for i, text in enumerate(header):
        fill = SOFT[ORANGE] if i == 2 else "#f1f5f9"
        draw.rectangle([x, top, x + widths[i], top + height], fill=fill, outline=LINE, width=2)
        draw.text(
            (x + widths[i] / 2, top + height / 2),
            text,
            font=font(24, bold=True),
            fill=ORANGE if i == 2 else INK,
            anchor="mm",
        )
        x += widths[i]
    groups = [
        (
            "regularne: + -ed",
            [
                ("work", "worked", "worked"),
                ("play", "played", "played"),
                ("stop", "stopped", "stopped"),
            ],
        ),
        (
            "nieregularne: z tabeli",
            [
                ("go", "went", "gone"),
                ("see", "saw", "seen"),
                ("eat", "ate", "eaten"),
                ("write", "wrote", "written"),
                ("be", "was / were", "been"),
            ],
        ),
    ]
    y = top + height
    for title, rows in groups:
        draw.rectangle([left, y, left + sum(widths), y + 40], fill="white")
        draw.text((left + 12, y + 8), title, font=font(22, bold=True), fill=MUTED)
        y += 40
        for row in rows:
            x = left
            for i, text in enumerate(row):
                fill = SOFT[ORANGE] if i == 2 else "white"
                draw.rectangle([x, y, x + widths[i], y + 46], fill=fill, outline=LINE, width=2)
                draw.text(
                    (x + widths[i] / 2, y + 23),
                    text,
                    font=font(26, bold=i == 2),
                    fill=INK,
                    anchor="mm",
                )
                x += widths[i]
            y += 46
    draw.text(
        (left, y + 18),
        "I have written a letter.   (nie: I have wrote a letter.)",
        font=font(26, bold=True),
        fill=INK,
    )
    save(image, "e1_v_formy.png")


def e2_words() -> None:
    image, draw = canvas("ever, never, already, yet", "Gdzie stoją w zdaniu i co znaczą")
    rows = [
        (
            [("Have", None), ("you", None), ("ever", BLUE), ("been", None), ("to London?", None)],
            "ever = kiedykolwiek",
            "pytanie, przed V3",
            BLUE,
        ),
        (
            [("I", None), ("have", None), ("never", RED), ("eaten", None), ("sushi.", None)],
            "never = nigdy",
            "bez not!",
            RED,
        ),
        (
            [
                ("We", None),
                ("have", None),
                ("already", GREEN),
                ("bought", None),
                ("the tickets.", None),
            ],
            "already = już",
            "między have a V3",
            GREEN,
        ),
        (
            [("Have", None), ("you", None), ("finished", None), ("yet?", ORANGE)],
            "yet = już (pytanie)",
            "na końcu",
            ORANGE,
        ),
        (
            [("I", None), ("haven't", None), ("finished", None), ("yet.", ORANGE)],
            "yet = jeszcze (przeczenie)",
            "na końcu",
            ORANGE,
        ),
    ]
    for r, (words, meaning, place, color) in enumerate(rows):
        top = 140 + r * 104
        chips(draw, 60, top, words, size=27, height=56)
        draw.text((790, top + 2), meaning, font=font(25, bold=True), fill=color)
        draw.text((790, top + 34), place, font=font(22), fill=MUTED)
    save(image, "e2_v_slowka.png")


def e3_for_since() -> None:
    image, draw = canvas("for czy since?", "Coś trwa od przeszłości do teraz → Present Perfect")
    y = 300
    arrow(draw, [(80, y), (1120, y)], AXIS, 4)
    start, now = 300, 960
    draw.ellipse([start - 12, y - 12, start + 12, y + 12], fill=ORANGE)
    draw.text((start, y + 22), "March", font=font(26, bold=True), fill=ORANGE, anchor="ma")
    draw.text((start, y - 92), "since March", font=font(30, bold=True), fill=ORANGE, anchor="ma")
    draw.text((start, y - 52), "od kiedy? – początek", font=font(22), fill=MUTED, anchor="ma")
    draw.ellipse([now - 12, y - 12, now + 12, y + 12], fill=INK)
    draw.text((now, y + 22), "NOW (June)", font=font(26, bold=True), fill=INK, anchor="ma")
    # bracket for the period
    by = y + 80
    draw.line([(start, by), (now, by)], fill=BLUE, width=4)
    draw.line([(start, by - 14), (start, by)], fill=BLUE, width=4)
    draw.line([(now, by - 14), (now, by)], fill=BLUE, width=4)
    draw.text(
        ((start + now) / 2, by + 12),
        "for three months",
        font=font(30, bold=True),
        fill=BLUE,
        anchor="ma",
    )
    draw.text(
        ((start + now) / 2, by + 52), "ile czasu? – okres", font=font(22), fill=MUTED, anchor="ma"
    )
    draw.text(
        (W / 2, 160),
        "Tom has had this job since March / for three months.",
        font=font(28, bold=True),
        fill=INK,
        anchor="ma",
    )
    note(
        draw,
        90,
        540,
        ["five years, two weeks,", "an hour, ages"],
        BLUE,
        width=480,
        size=25,
        title="for + okres",
    )
    note(
        draw,
        630,
        540,
        ["2019, Monday, 8 o'clock,", "I was six"],
        ORANGE,
        width=480,
        size=25,
        title="since + początek",
    )
    save(image, "e3_v_for_since.png")


def e4_timeline() -> None:
    image, draw = canvas(
        "Present Perfect czy Past Simple?", "Czy podajesz konkretny, zakończony czas?"
    )
    y = 380
    arrow(draw, [(80, y), (1120, y)], AXIS, 4)
    draw.text((80, y + 20), "przeszłość", font=font(22), fill=MUTED)
    now = 980
    draw.ellipse([now - 13, y - 13, now + 13, y + 13], fill=INK)
    draw.text((now, y + 22), "TERAZ", font=font(24, bold=True), fill=INK, anchor="ma")
    # Past Simple: a finished point with a date
    past = 290
    draw.ellipse([past - 13, y - 13, past + 13, y + 13], fill=ORANGE)
    draw.text((past, y + 22), "yesterday", font=font(22, bold=True), fill=ORANGE, anchor="ma")
    draw.text((past, y - 130), "Past Simple", font=font(30, bold=True), fill=ORANGE, anchor="ma")
    draw.text((past, y - 88), "I lost my keys yesterday.", font=font(24), fill=INK, anchor="ma")
    draw.text((past, y - 54), "konkretny, zakończony czas", font=font(20), fill=MUTED, anchor="ma")
    # Present Perfect: from the past to now
    draw.arc([560, y - 150, now, y + 150], start=180, end=360, fill=BLUE, width=6)
    draw.text((770, y - 205), "Present Perfect", font=font(30, bold=True), fill=BLUE, anchor="ma")
    draw.text((770, y - 128), "I have lost my keys.", font=font(24), fill=INK, anchor="ma")
    draw.text(
        (770, y - 94),
        "skutek teraz: I can't open the door!",
        font=font(20),
        fill=MUTED,
        anchor="ma",
    )
    note(
        draw,
        90,
        500,
        ["yesterday, last week, in 2019,", "two years ago, When…?"],
        ORANGE,
        width=490,
        size=24,
        title="Past Simple (V2)",
    )
    note(
        draw,
        620,
        500,
        ["ever, never, already, yet, for, since,", "today, this week, so far"],
        BLUE,
        width=500,
        size=24,
        title="Present Perfect (have/has + V3)",
    )
    draw.text(
        (W / 2, 690),
        "Have you ever been to Italy?  –  Yes, I went there last summer.",
        font=font(24, bold=True),
        fill=INK,
        anchor="ma",
    )
    save(image, "e4_v_os_czasu.png")


# --- Python images -------------------------------------------------------------------------------

KEYWORDS = {"for", "in", "while", "if", "break", "continue", "True", "print", "range", "input"}
CODE_COLORS = {
    "keyword": "#93c5fd",
    "string": "#86efac",
    "number": "#fdba74",
    "comment": "#94a3b8",
    "text": "#e2e8f0",
}


def code_tokens(line: str) -> list[tuple[str, str]]:
    """Very small highlighter: keywords, strings, numbers, comments."""
    tokens: list[tuple[str, str]] = []
    i = 0
    while i < len(line):
        ch = line[i]
        if ch == "#":
            tokens.append((line[i:], "comment"))
            break
        if ch == '"':
            end = line.index('"', i + 1) + 1
            tokens.append((line[i:end], "string"))
            i = end
        elif ch.isalpha() or ch == "_":
            end = i
            while end < len(line) and (line[end].isalnum() or line[end] == "_"):
                end += 1
            word = line[i:end]
            tokens.append((word, "keyword" if word in KEYWORDS else "text"))
            i = end
        elif ch.isdigit():
            end = i
            while end < len(line) and line[end].isdigit():
                end += 1
            tokens.append((line[i:end], "number"))
            i = end
        else:
            tokens.append((ch, "text"))
            i += 1
    return tokens


def code_panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    lines: Sequence[str],
    size: int = 28,
    step: int = 46,
    title: str = "",
) -> None:
    left, top, right, bottom = box
    draw.rectangle(box, fill=CODE_BG)
    typeface = font(size, mono=True)
    y = top + 22
    if title:
        draw.text((left + 24, y), title, font=font(20, bold=True), fill="#94a3b8")
        y += 40
    for line in lines:
        x = left + 24
        for text, kind in code_tokens(line):
            draw.text((x, y), text, font=typeface, fill=CODE_COLORS[kind])
            x += typeface.getlength(text)
        y += step


def flow_box(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    text: str,
    color: str,
    w: int = 360,
    h: int = 76,
    diamond: bool = False,
    mono: bool = False,
) -> None:
    cx, cy = center
    if diamond:
        draw.polygon(
            [(cx, cy - h), (cx + w / 2, cy), (cx, cy + h), (cx - w / 2, cy)],
            fill=SOFT[color],
            outline=color,
            width=4,
        )
    else:
        draw.rectangle(
            [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
            fill=SOFT[color],
            outline=color,
            width=4,
        )
    draw.multiline_text(
        (cx, cy),
        text,
        font=font(24, bold=not mono, mono=mono),
        fill=INK,
        anchor="mm",
        align="center",
        spacing=6,
    )


def loop_flowchart(
    name: str, title: str, subtitle: str, steps: Sequence[str], code_lines: Sequence[str]
) -> None:
    """Start, condition (diamond), body, update, end – with the matching code on the right."""
    image, draw = canvas(title, subtitle)
    x = 330
    start, check, body, update, end = (x, 180), (x, 330), (x, 490), (x, 615), (x + 380, 330)
    flow_box(draw, start, steps[0], PURPLE, mono=True)
    flow_box(draw, check, steps[1], ORANGE, w=400, h=86, diamond=True)
    flow_box(draw, body, steps[2], BLUE, mono=True)
    flow_box(draw, update, steps[3], BLUE, mono=True)
    flow_box(draw, end, steps[4], GREEN, w=220)
    arrow(draw, [(x, 218), (x, 242)])
    arrow(draw, [(x, 416), (x, 450)])
    draw.text((x + 14, 422), "tak", font=font(22, bold=True), fill=AXIS)
    arrow(draw, [(x, 528), (x, 575)])
    # back to the condition on the left side
    arrow(draw, [(x - 180, 615), (x - 260, 615), (x - 260, 262), (x, 262), (x, 242)])
    draw.line([(x + 200, 330), (x + 270, 330)], fill=AXIS, width=4)
    arrow(draw, [(x + 240, 330), (x + 270, 330)])
    draw.text((x + 236, 318), "nie", font=font(22, bold=True), fill=AXIS, anchor="mb")
    draw.text((x - 250, 372), "następny\nobrót", font=font(20, bold=True), fill=MUTED, spacing=4)
    code_panel(
        draw,
        (620, 440, 1160, 440 + 40 * len(code_lines) + 84),
        code_lines,
        size=24,
        step=40,
        title="KOD",
    )
    save(image, name)


def p1_flowchart() -> None:
    loop_flowchart(
        "p1_v_schemat.png",
        "Jak działa pętla for",
        'for owoc in ["jabłko", "gruszka", "śliwka"]:',
        [
            "owoce = [...]",
            "czy jest kolejny\nelement listy?",
            "owoc = kolejny element",
            "print(owoc)",
            "koniec pętli",
        ],
        ["for owoc in owoce:", "    print(owoc)"],
    )


def trace_table(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    header: Sequence[str],
    rows: Sequence[Sequence[str]],
    widths: Sequence[int],
    highlight_last: bool = False,
) -> int:
    height = 50
    for r, row in enumerate([header, *rows]):
        left = x
        for c, cell in enumerate(row):
            fill = (
                "#f1f5f9"
                if r == 0
                else (SOFT[GREEN] if highlight_last and r == len(rows) else "white")
            )
            draw.rectangle(
                [left, y, left + widths[c], y + height], fill=fill, outline=LINE, width=2
            )
            draw.text(
                (left + widths[c] / 2, y + height / 2),
                cell,
                font=font(24, bold=r == 0, mono=r > 0),
                fill=INK,
                anchor="mm",
            )
            left += widths[c]
        y += height
    return y


def p1_code() -> None:
    image, draw = canvas("Suma krok po kroku", "Co dzieje się w każdym obrocie pętli")
    code_panel(
        draw,
        (48, 140, 600, 372),
        ["suma = 0", "for liczba in [2, 4, 6]:", "    suma = suma + liczba", "print(suma)"],
    )
    bottom = trace_table(
        draw,
        660,
        140,
        ("obrót", "liczba", "suma"),
        [("start", "–", "0"), ("1", "2", "2"), ("2", "4", "6"), ("3", "6", "12")],
        (150, 150, 180),
        highlight_last=True,
    )
    draw.text((660, bottom + 24), "Program wypisze: 12", font=font(28, bold=True), fill=GREEN)
    note(
        draw,
        48,
        470,
        ["linia z wcięciem wykonuje się w każdym obrocie,", "linia bez wcięcia – raz, po pętli"],
        BLUE,
        width=552,
        size=23,
        title="Wcięcie decyduje",
    )
    note(
        draw,
        660,
        470,
        ['for litera in "kot": print(litera)', "wypisze k, o, t – każdą w osobnej linii"],
        PURPLE,
        width=490,
        size=23,
        title="Pętla po napisie",
    )
    save(image, "p1_v_kod.png")


def p2_range() -> None:
    image, draw = canvas("Co daje range()?", "Liczba stop nigdy nie należy do ciągu")
    rows = [
        ("range(4)", [0, 1, 2, 3], 4),
        ("range(2, 6)", [2, 3, 4, 5], 6),
        ("range(0, 10, 3)", [0, 3, 6, 9], 10),
        ("range(5, 0, -1)", [5, 4, 3, 2, 1], 0),
    ]
    left, unit = 360, 74
    for r, (label, values, stop) in enumerate(rows):
        y = 175 + r * 130
        draw.text((48, y), label, font=font(28, bold=True, mono=True), fill=INK, anchor="lm")
        draw.line([(left - 20, y), (left + 10 * unit + 20, y)], fill=LINE, width=3)
        for n in range(11):
            x = left + n * unit
            draw.line([(x, y - 8), (x, y + 8)], fill=LINE, width=2)
            draw.text((x, y + 30), str(n), font=font(20), fill=MUTED, anchor="mm")
        for value in values:
            x = left + value * unit
            draw.ellipse([x - 17, y - 17, x + 17, y + 17], fill=BLUE)
            draw.text((x, y), str(value), font=font(20, bold=True), fill="white", anchor="mm")
        x = left + stop * unit
        draw.ellipse([x - 17, y - 17, x + 17, y + 17], fill="white", outline=RED, width=3)
        draw.line([(x - 12, y - 12), (x + 12, y + 12)], fill=RED, width=3)
        draw.text((x, y - 44), "stop", font=font(18, bold=True), fill=RED, anchor="mm")
        if label == "range(5, 0, -1)":
            arrow(draw, [(left + 5 * unit + 40, y - 40), (left + 1 * unit + 10, y - 40)], BLUE, 3)
            draw.text(
                (left + 3 * unit, y - 62),
                "krok −1: w dół",
                font=font(18, bold=True),
                fill=BLUE,
                anchor="mm",
            )
    note(
        draw,
        48,
        660,
        ["range(n): od 0, n liczb   ·   range(start, stop, krok)   ·   1–10: range(1, 11)"],
        MUTED,
        width=1104,
        size=23,
    )
    save(image, "p2_v_range.png")


def p3_flowchart() -> None:
    loop_flowchart(
        "p3_v_schemat.png",
        "Jak działa pętla while",
        "while warunek: – powtarzaj, dopóki warunek jest prawdziwy",
        [
            "licznik = 1",
            "czy licznik <= 5?",
            "print(licznik)",
            "licznik = licznik + 1",
            "koniec pętli",
        ],
        ["licznik = 1", "while licznik <= 5:", "    print(licznik)", "    licznik = licznik + 1"],
    )


def p3_code() -> None:
    image, draw = canvas(
        "Pętla while krok po kroku", "Warunek jest sprawdzany przed każdym obrotem"
    )
    code_panel(
        draw,
        (48, 140, 600, 372),
        ["licznik = 1", "while licznik <= 5:", "    print(licznik)", "    licznik = licznik + 1"],
    )
    trace_table(
        draw,
        660,
        140,
        ("licznik", "licznik <= 5?", "wypisze"),
        [
            ("1", "tak", "1"),
            ("2", "tak", "2"),
            ("3", "tak", "3"),
            ("4", "tak", "4"),
            ("5", "tak", "5"),
            ("6", "nie", "koniec"),
        ],
        (150, 200, 150),
    )
    note(
        draw,
        48,
        430,
        [
            "bez linii licznik = licznik + 1",
            "warunek jest zawsze prawdziwy –",
            "pętla nieskończona (Ctrl+C)",
        ],
        RED,
        width=552,
        size=23,
        title="Uwaga",
    )
    note(
        draw,
        660,
        530,
        ["x = 10, while x > 10:", "ciało nie wykona się ani razu"],
        MUTED,
        width=500,
        size=23,
        title="Warunek fałszywy od razu",
    )
    save(image, "p3_v_kod.png")


def p4_break_continue() -> None:
    image, draw = canvas(
        "break i continue", "break kończy całą pętlę, continue pomija tylko bieżący obrót"
    )
    panels = [
        (
            48,
            "break",
            RED,
            [
                "for n in [3, 8, -1, 5]:",
                "    if n < 0:",
                "        break",
                "    print(n)",
                'print("koniec")',
            ],
            "3, 8, koniec",
            "przy −1 wyjście z pętli – 5 już nie",
        ),
        (
            620,
            "continue",
            BLUE,
            ["for n in range(1, 7):", "    if n % 2 == 0:", "        continue", "    print(n)"],
            "1, 3, 5",
            "parzyste (n % 2 == 0) pominięte",
        ),
    ]
    for left, name, color, lines, output, comment in panels:
        draw.text((left, 128), name, font=font(32, bold=True, mono=True), fill=color)
        code_panel(draw, (left, 180, left + 532, 180 + 46 * 5 + 44), lines, size=26, step=46)
        y = 180 + 46 * 5 + 70
        note(draw, left, y, [output, comment], color, width=532, size=24, title="Wypisze")
    draw.text(
        (W / 2, 690),
        "% to reszta z dzielenia: 7 % 2 = 1, 6 % 2 = 0",
        font=font(24, bold=True),
        fill=MUTED,
        anchor="mm",
    )
    save(image, "p4_v_break_continue.png")


# --- Worksheets (PDF) ----------------------------------------------------------------------------

A4 = (1240, 1754)  # 150 dpi
MARGIN = 90
CONTENT = A4[0] - 2 * MARGIN
BOTTOM = A4[1] - 120
GRID_CELL = 40
PDF_DATE = time.strptime("2026-11-12", "%Y-%m-%d")


@dataclass(frozen=True)
class Lines:
    """Lined space for written answers."""

    count: int


@dataclass(frozen=True)
class Grid:
    """Squared space for drawing; axes "full" (−n..n), "corner" (first quadrant) or "none"."""

    cols: int
    rows: int
    axes: str = "full"


@dataclass(frozen=True)
class FillTable:
    """Table to fill in: rows of cells, empty strings are blanks."""

    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Listing:
    """Program code shown in a monospace box."""

    lines: tuple[str, ...]


Work = Lines | Grid | FillTable | Listing


@dataclass(frozen=True)
class Task:
    text: str
    work: tuple[Work, ...] = ()
    answer: tuple[str | Listing, ...] = field(default_factory=tuple)


class Pages:
    """A4 pages drawn top to bottom; a block that does not fit starts a new page."""

    def __init__(self, course: str, title: str) -> None:
        self.course, self.title = course, title
        self.pages: list[Image.Image] = []
        self.new_page()

    def new_page(self) -> None:
        page = Image.new("RGB", A4, "white")
        self.pages.append(page)
        self.draw = ImageDraw.Draw(page)
        self.draw.rectangle([0, 0, A4[0], 14], fill=INK)
        self.draw.text(
            (MARGIN, 52), f"KARTA ZADANIA · {self.course}", font=font(22, bold=True), fill=MUTED
        )
        self.draw.text(
            (A4[0] - MARGIN, A4[1] - 70),
            f"{len(self.pages)}",
            font=font(22),
            fill=MUTED,
            anchor="ra",
        )
        self.y = 110

    def ensure(self, height: int) -> None:
        if self.y + height > BOTTOM:
            self.new_page()

    def text(
        self,
        text: str,
        size: int = 28,
        bold: bool = False,
        color: str = INK,
        indent: int = 0,
        gap: int = 12,
    ) -> None:
        typeface = font(size, bold=bold)
        lines = wrap(text, typeface, CONTENT - indent)
        self.ensure(len(lines) * (size + 14))
        for line in lines:
            self.draw.text((MARGIN + indent, self.y), line, font=typeface, fill=color)
            self.y += size + 14
        self.y += gap

    @staticmethod
    def height(item: Work) -> int:
        if isinstance(item, Lines):
            return item.count * 58 + 26
        if isinstance(item, Grid):
            return item.rows * GRID_CELL + 60
        if isinstance(item, FillTable):
            return len(item.rows) * 60 + 30
        return len(item.lines) * 40 + 54

    def work(self, item: Work, indent: int = 60) -> None:
        left = MARGIN + indent
        right = A4[0] - MARGIN
        self.ensure(self.height(item))
        d = self.draw  # after `ensure`: the block may start a new page
        if isinstance(item, Lines):
            for _ in range(item.count):
                self.y += 58
                d.line([(left, self.y), (right, self.y)], fill=LINE, width=2)
            self.y += 26
        elif isinstance(item, Grid):
            cell = GRID_CELL
            self.y += 22  # room for the arrow of the y axis
            for c in range(item.cols + 1):
                d.line(
                    [(left + c * cell, self.y), (left + c * cell, self.y + item.rows * cell)],
                    fill=GRID,
                    width=2,
                )
            for r in range(item.rows + 1):
                d.line(
                    [(left, self.y + r * cell), (left + item.cols * cell, self.y + r * cell)],
                    fill=GRID,
                    width=2,
                )
            if item.axes == "full":
                cx, cy = left + item.cols // 2 * cell, self.y + item.rows // 2 * cell
                arrow(d, [(left, cy), (left + item.cols * cell + 14, cy)], AXIS, 3)
                arrow(d, [(cx, self.y + item.rows * cell), (cx, self.y - 14)], AXIS, 3)
                d.text(
                    (left + item.cols * cell + 4, cy - 34), "x", font=font(24, bold=True), fill=AXIS
                )
                d.text((cx + 10, self.y - 16), "y", font=font(24, bold=True), fill=AXIS)
            elif item.axes == "corner":
                ox, oy = left + cell, self.y + (item.rows - 1) * cell
                arrow(d, [(ox, oy), (left + item.cols * cell + 14, oy)], AXIS, 3)
                arrow(d, [(ox, self.y + item.rows * cell), (ox, self.y - 14)], AXIS, 3)
            self.y += item.rows * cell + 38
        elif isinstance(item, FillTable):
            columns = len(item.rows[0])
            first = 200
            other = min(130, (right - left - first) // max(1, columns - 1))
            height = 60
            for r, row in enumerate(item.rows):
                x = left
                for c, cell_text in enumerate(row):
                    width = first if c == 0 else other
                    box = [x, self.y, x + width, self.y + height]
                    d.rectangle(
                        box,
                        fill="#f1f5f9" if c == 0 or r == 0 and cell_text else "white",
                        outline=AXIS,
                        width=2,
                    )
                    if cell_text:
                        d.text(
                            ((box[0] + box[2]) / 2, self.y + height / 2),
                            cell_text,
                            font=font(26, bold=c == 0),
                            fill=INK,
                            anchor="mm",
                        )
                    x += width
                self.y += height
            self.y += 30
        elif isinstance(item, Listing):
            self.listing(item.lines, left)

    def listing(self, lines: Sequence[str], left: int) -> None:
        size, step = 26, 40
        height = len(lines) * step + 30
        self.ensure(height + 20)
        d = self.draw
        d.rectangle(
            [left, self.y, A4[0] - MARGIN, self.y + height], fill="#f8fafc", outline=LINE, width=2
        )
        for i, line in enumerate(lines):
            d.text((left + 22, self.y + 16 + i * step), line, font=font(size, mono=True), fill=INK)
        self.y += height + 24

    def task(self, number: int, task: Task) -> None:
        typeface = font(28)
        lines = wrap(task.text, typeface, CONTENT - 60)
        # keep the whole task on one page when it fits, else at least the text with its first space
        text_height = len(lines) * 42 + 10
        whole = text_height + sum(self.height(item) for item in task.work)
        if whole <= BOTTOM - 110:
            self.ensure(whole)
        else:
            self.ensure(text_height + (self.height(task.work[0]) if task.work else 0))
        d = self.draw
        d.text((MARGIN, self.y), f"{number}.", font=font(28, bold=True), fill=BLUE)
        for line in lines:
            d.text((MARGIN + 60, self.y), line, font=typeface, fill=INK)
            self.y += 42
        self.y += 10
        for item in task.work:
            self.work(item)
        self.y += 18

    def save(self, name: str) -> None:
        first, *rest = self.pages
        first.save(
            ASSETS / name,
            "PDF",
            resolution=150,
            save_all=True,
            append_images=rest,
            title=self.title,
            # fixed dates: regenerating gives identical files (no noise in git)
            creationDate=PDF_DATE,
            modDate=PDF_DATE,
        )
        print("ok", name, f"({len(self.pages)} str.)")


def worksheet(name: str, course: str, title: str, intro: str, tasks: Sequence[Task]) -> None:
    pages = Pages(course, title)
    pages.text(title, size=48, bold=True, gap=8)
    pages.text(
        "Imię: ______________________________     Data: ______________",
        size=24,
        color=MUTED,
        gap=18,
    )
    pages.text(intro, size=27, gap=26)
    for number, task in enumerate(tasks, start=1):
        pages.task(number, task)
    # Answers on their own page
    pages.new_page()
    pages.text("Odpowiedzi", size=44, bold=True, gap=4)
    pages.text(
        "Sprawdź dopiero po samodzielnym rozwiązaniu. Błąd? Wróć do instrukcji i policz jeszcze raz.",
        size=24,
        color=MUTED,
        gap=24,
    )
    for number, task in enumerate(tasks, start=1):
        pages.ensure(60)
        pages.draw.text((MARGIN, pages.y), f"{number}.", font=font(26, bold=True), fill=BLUE)
        for part in task.answer:
            if isinstance(part, Listing):
                pages.listing(part.lines, MARGIN + 60)
            else:
                pages.text(part, size=26, indent=60, gap=2)
        pages.y += 14
    pages.save(name)


def math_worksheets() -> None:
    course = "Matematyka: funkcja liniowa"
    worksheet(
        "m1_k_karta.pdf",
        f"{course} · lekcja 1",
        "Tabela i wykres",
        "Potrzebujesz ołówka i linijki. Rób zadania po kolei – wyniki jednego przydadzą się w następnym.",
        [
            Task(
                "Uzupełnij tabelę wartości funkcji y = −x + 3.",
                (
                    FillTable(
                        (("x", "−2", "−1", "0", "1", "2", "3"), ("y", "", "", "", "", "", ""))
                    ),
                ),
                ("y: 5, 4, 3, 2, 1, 0 (np. dla x = −2: −(−2) + 3 = 5).",),
            ),
            Task(
                "Narysuj wykres funkcji y = −x + 3 w układzie poniżej. Użyj punktów z tabeli.",
                (Grid(12, 12),),
                ("Prosta przechodząca m.in. przez (0, 3) i (3, 0), opadająca w prawo.",),
            ),
            Task(
                "Odczytaj z wykresu, w jakim punkcie prosta przecina oś y. Porównaj go z liczbą b we wzorze.",
                (Lines(1),),
                ("(0, 3) – to b = 3 ze wzoru y = −x + 3.",),
            ),
            Task(
                "Sprawdź rachunkiem, czy punkty należą do wykresu y = −x + 3: A = (4, −1), B = (−3, 5).",
                (Lines(2),),
                ("A: −4 + 3 = −1 – należy.", "B: −(−3) + 3 = 6 ≠ 5 – nie należy."),
            ),
            Task(
                "Dla jakiego x funkcja y = −x + 3 ma wartość 7?",
                (Lines(2),),
                ("−x + 3 = 7, więc −x = 4 i x = −4.",),
            ),
            Task(
                "Ułóż własną funkcję liniową y = ax + b, narysuj jej wykres w zeszycie i zaznacz kolorem punkt (0, b).",
                (Lines(1),),
                (
                    "Dowolna funkcja, np. y = 3x − 2: prosta musi przechodzić przez (0, b), tu (0, −2).",
                ),
            ),
        ],
    )
    worksheet(
        "m2_k_karta.pdf",
        f"{course} · lekcja 2",
        "Współczynnik kierunkowy a",
        "Patrz na liczbę a: jej znak mówi, czy funkcja rośnie, a wartość bez znaku – jak stroma jest prosta.",
        [
            Task(
                "Bez rysowania napisz, czy funkcja jest rosnąca, malejąca czy stała: a) y = 4x − 7, b) y = −0,5x + 1, c) y = −2, d) y = x.",
                (Lines(2),),
                (
                    "a) rosnąca (a = 4), b) malejąca (a = −0,5), c) stała (a = 0), d) rosnąca (a = 1).",
                ),
            ),
            Task(
                "Uporządkuj proste od najmniej do najbardziej stromej: y = 3x, y = −4x + 1, y = 0,5x, y = −x.",
                (Lines(1),),
                ("y = 0,5x; y = −x; y = 3x; y = −4x + 1 (a bez znaku: 0,5; 1; 3; 4).",),
            ),
            Task(
                "Oblicz a dla prostej przechodzącej przez punkty (1, 2) i (3, 8).",
                (Lines(2),),
                ("a = (8 − 2) : (3 − 1) = 6 : 2 = 3.",),
            ),
            Task(
                "Oblicz a dla prostej przechodzącej przez punkty (0, 5) i (2, 1). Czy ta funkcja rośnie, czy maleje?",
                (Lines(2),),
                ("a = (1 − 5) : (2 − 0) = −4 : 2 = −2; a < 0, więc funkcja maleje.",),
            ),
            Task(
                "Narysuj w jednym układzie prostą y = x + 1 i prostą do niej równoległą, która przechodzi przez punkt (0, −2). Zapisz jej wzór.",
                (Grid(12, 12), Lines(1)),
                ("y = x − 2 (to samo a = 1, przecięcie z osią y w (0, −2)).",),
            ),
            Task(
                "Ułóż wzór funkcji malejącej, której wykres przecina oś y w punkcie (0, 3).",
                (Lines(1),),
                ("Np. y = −2x + 3 – dowolne a < 0 i b = 3.",),
            ),
        ],
    )
    worksheet(
        "m3_k_karta.pdf",
        f"{course} · lekcja 3",
        "Miejsce zerowe",
        "Miejsce zerowe to x, dla którego y = 0. Wpisz 0 zamiast y, rozwiąż równanie i sprawdź na wykresie.",
        [
            Task(
                "Oblicz miejsca zerowe funkcji: a) y = 3x − 6, b) y = −2x + 8, c) y = x + 5, d) y = 0,5x − 2.",
                (Lines(3),),
                (
                    "a) 3x − 6 = 0, x = 2; b) −2x + 8 = 0, x = 4; c) x + 5 = 0, x = −5; d) 0,5x − 2 = 0, x = 4.",
                ),
            ),
            Task(
                "Narysuj wykres funkcji y = −x + 2 i odczytaj z niego miejsce zerowe. Sprawdź je rachunkiem.",
                (Grid(12, 12), Lines(1)),
                ("Prosta przecina oś x w (2, 0); rachunek: −x + 2 = 0, więc x = 2.",),
            ),
            Task(
                "Dla funkcji y = −x + 2 zapisz, dla jakich x wartości są dodatnie, a dla jakich ujemne.",
                (Lines(2),),
                ("Funkcja maleje (a = −1): dodatnie dla x < 2, ujemne dla x > 2.",),
            ),
            Task(
                "Czy funkcja y = −3 ma miejsce zerowe? Uzasadnij jednym zdaniem.",
                (Lines(1),),
                (
                    "Nie – y jest zawsze równe −3, pozioma prosta biegnie pod osią x i jej nie przecina.",
                ),
            ),
            Task(
                "Ułóż wzór funkcji liniowej, której miejscem zerowym jest x = 3.",
                (Lines(1),),
                ("Np. y = x − 3 albo y = 2x − 6 (sprawdź: dla x = 3 wychodzi 0).",),
            ),
        ],
    )
    worksheet(
        "m4_k_karta.pdf",
        f"{course} · lekcja 4",
        "Funkcja liniowa w życiu",
        "W każdym zadaniu najpierw ustal wartość na starcie (b) i zmianę na jednostkę (a), potem zapisz wzór y = ax + b.",
        [
            Task(
                "Wypożyczalnia rowerów: 5 zł za wypożyczenie i 4 zł za każdą godzinę jazdy. Zapisz wzór kosztu y za x godzin.",
                (Lines(1),),
                ("y = 4x + 5.",),
            ),
            Task(
                "Ile zapłacisz za 3 godziny? Ile godzin możesz jeździć za 29 zł?",
                (Lines(2),),
                ("3 godziny: 4 · 3 + 5 = 17 zł.", "29 zł: 4x + 5 = 29, 4x = 24, x = 6 godzin."),
            ),
            Task(
                "W baku jest 40 litrów paliwa, a samochód zużywa 5 litrów na każde 100 km. Zapisz wzór na ilość paliwa y po przejechaniu x setek kilometrów i oblicz, po ilu kilometrach bak będzie pusty.",
                (Lines(3),),
                ("y = −5x + 40; −5x + 40 = 0, x = 8 setek, czyli bak będzie pusty po 800 km.",),
            ),
            Task(
                "Dwie wypożyczalnie: A – y = 4x + 5, B – y = 6x + 1 (x – godziny, y – zł). Narysuj oba wykresy dla x od 0 do 4 (w poziomie 2 kratki = 1 h, w pionie 1 kratka = 2 zł) i odczytaj, przy ilu godzinach koszt jest równy.",
                (Grid(16, 14, axes="corner"), Lines(1)),
                ("4x + 5 = 6x + 1, więc x = 2 – po 2 godzinach obie wypożyczalnie biorą 13 zł.",),
            ),
            Task(
                "Która wypożyczalnia jest tańsza na 1 godzinę, a która na 4 godziny?",
                (Lines(2),),
                ("1 h: A 9 zł, B 7 zł – tańsza B.", "4 h: A 21 zł, B 25 zł – tańsza A."),
            ),
        ],
    )


def english_worksheets() -> None:
    course = "Angielski: Present Perfect"
    worksheet(
        "e1_k_karta.pdf",
        f"{course} · lekcja 1",
        "Budowa zdania",
        "Pamiętaj: osoba + have/has + V3. Has tylko z he, she, it. Każde gotowe zdanie przeczytaj na głos.",
        [
            Task(
                "Uzupełnij have albo has: a) I ___ cleaned my room. b) My brother ___ broken his phone. c) We ___ visited Gdańsk. d) It ___ stopped raining.",
                (Lines(2),),
                ("a) have, b) has, c) have, d) has.",),
            ),
            Task(
                "Wpisz trzecią formę (V3): go, see, eat, write, play, stop, be, do.",
                (
                    FillTable(
                        (
                            ("forma", "go", "see", "eat", "write", "play", "stop", "be", "do"),
                            ("V3", "", "", "", "", "", "", "", ""),
                        )
                    ),
                ),
                ("gone, seen, eaten, written, played, stopped, been, done.",),
            ),
            Task(
                "Zamień na przeczenia: a) She has finished the test. b) They have bought a car.",
                (Lines(2),),
                ("a) She hasn't finished the test.", "b) They haven't bought a car."),
            ),
            Task(
                "Ułóż pytania i krótkie odpowiedzi: a) you / see / my keys? (No) b) he / do / his homework? (Yes)",
                (Lines(2),),
                (
                    "a) Have you seen my keys? – No, I haven't.",
                    "b) Has he done his homework? – Yes, he has.",
                ),
            ),
            Task(
                "Znajdź i popraw błąd: a) I have wrote an email. b) She have lost her bag. c) Has you eaten?",
                (Lines(3),),
                ("a) I have written an email.", "b) She has lost her bag.", "c) Have you eaten?"),
            ),
            Task(
                "Napisz 3 zdania o tym, co udało Ci się w tym tygodniu, np. I have read a book. I have learnt ten new words.",
                (Lines(3),),
                ("Sprawdź każde zdanie: have/has + V3, np. I have cleaned my room.",),
            ),
        ],
    )
    worksheet(
        "e2_k_karta.pdf",
        f"{course} · lekcja 2",
        "ever, never, already, yet",
        "ever i never stoją przed V3, already – między have/has a V3, yet – na końcu pytania albo przeczenia.",
        [
            Task(
                "Wstaw ever, never, already albo yet: a) Have you ___ seen a whale? b) I have ___ been to Japan – maybe one day! c) Hurry up! The film has ___ started. d) She hasn't called ___.",
                (Lines(2),),
                ("a) ever, b) never, c) already, d) yet.",),
            ),
            Task(
                "Ułóż słowa we właściwej kolejności: a) finished / have / I / already / my project b) they / arrived / yet / have / ? c) has / never / he / flown / a plane",
                (Lines(3),),
                (
                    "a) I have already finished my project.",
                    "b) Have they arrived yet?",
                    "c) He has never flown a plane.",
                ),
            ),
            Task(
                "Przetłumacz: a) Czy kiedykolwiek grałeś w szachy? b) Jeszcze nie odrobiłam lekcji. c) Już zjedliśmy obiad.",
                (Lines(3),),
                (
                    "a) Have you ever played chess?",
                    "b) I haven't done my homework yet.",
                    "c) We have already had (eaten) lunch / dinner.",
                ),
            ),
            Task(
                "Popraw błędy: a) I haven't never seen snow. b) Have you finished already yet? c) She has yet finished.",
                (Lines(3),),
                (
                    "a) I have never seen snow.",
                    "b) Have you finished yet?",
                    "c) She has already finished. (albo: She hasn't finished yet.)",
                ),
            ),
            Task(
                "Zrób mini-wywiad z kimś z rodziny: zadaj 3 pytania Have you ever…? i zapisz odpowiedzi (Yes, I have. / No, I've never…).",
                (Lines(3),),
                ("Sprawdź: ever stoi przed V3, odpowiedź z have / haven't albo never (bez not).",),
            ),
        ],
    )
    worksheet(
        "e3_k_karta.pdf",
        f"{course} · lekcja 3",
        "for i since",
        "Zapytaj siebie: ile czasu? → for. Od kiedy? → since. Coś trwa do teraz → Present Perfect.",
        [
            Task(
                "Wpisz for albo since: a) ___ three days b) ___ last summer c) ___ 2015 d) ___ a long time e) ___ my birthday f) ___ ten minutes",
                (Lines(2),),
                ("a) for, b) since, c) since, d) for, e) since, f) for.",),
            ),
            Task(
                "Uzupełnij czasownikiem w Present Perfect oraz for albo since: a) I ___ (know) Ola ___ we were five. b) They ___ (live) in Poznań ___ two years. c) She ___ (be) ill ___ Monday.",
                (Lines(3),),
                ("a) have known, since", "b) have lived, for", "c) has been, since"),
            ),
            Task(
                "Kuba started playing the guitar when he was eight. Now he is twelve. Napisz jedno zdanie z since i jedno z for.",
                (Lines(2),),
                (
                    "He has played the guitar since he was eight.",
                    "He has played the guitar for four years.",
                ),
            ),
            Task(
                "Ułóż pytania z How long i odpowiedz: a) you / have / your bike? (two years) b) she / be / in the team? (September)",
                (Lines(4),),
                (
                    "a) How long have you had your bike? – I've had it for two years.",
                    "b) How long has she been in the team? – She has been in the team since September.",
                ),
            ),
            Task(
                "Popraw błędy: a) I live in Kraków for five years. b) We have been here since two hours. c) He has worked here for 2020.",
                (Lines(3),),
                (
                    "a) I have lived in Kraków for five years.",
                    "b) We have been here for two hours.",
                    "c) He has worked here since 2020.",
                ),
            ),
        ],
    )
    worksheet(
        "e4_k_karta.pdf",
        f"{course} · lekcja 4",
        "Present Perfect czy Past Simple?",
        "Pytanie-klucz: czy podajesz konkretny, zakończony czas? Tak → Past Simple (V2). Nie → Present Perfect (have/has + V3).",
        [
            Task(
                "Podkreśl właściwą formę: a) I (saw / have seen) this film last week. b) I (never saw / have never seen) a real tiger. c) She (lost / has lost) her phone, so she can't call you now. d) We (went / have gone) to the cinema two days ago.",
                (Lines(1),),
                ("a) saw, b) have never seen, c) has lost, d) went.",),
            ),
            Task(
                "Uzupełnij w Past Simple albo Present Perfect: a) ___ you ever ___ (eat) Indian food? b) When ___ you ___ (start) school? c) They ___ (already / arrive). d) I ___ (be) to Berlin in 2022.",
                (Lines(3),),
                ("a) Have … eaten, b) did … start, c) have already arrived, d) was.",),
            ),
            Task(
                "Dokończ rozmowę: A: Have you ever been to the mountains? B: Yes, I ___. I ___ (go) to Zakopane last winter.",
                (Lines(2),),
                ("have; went (last winter = konkretny czas, więc Past Simple).",),
            ),
            Task(
                "Popraw błędy: a) I have seen him yesterday. b) When have you bought this bike? c) We have moved here two years ago.",
                (Lines(3),),
                (
                    "a) I saw him yesterday.",
                    "b) When did you buy this bike?",
                    "c) We moved here two years ago.",
                ),
            ),
            Task(
                "Napisz 2 zdania o sobie: jedno w Present Perfect (doświadczenie bez podawania czasu) i jedno w Past Simple z określeniem czasu.",
                (Lines(2),),
                ("Np. I have been to the sea. I went to the sea last July.",),
            ),
        ],
    )


def python_worksheets() -> None:
    course = "Programowanie: pętle w Pythonie"
    worksheet(
        "p1_k_karta.pdf",
        f"{course} · lekcja 1",
        "Pętla for",
        "Najpierw przewiduj na kartce, potem uruchom program na komputerze i porównaj. Pamiętaj o dwukropku i wcięciu.",
        [
            Task(
                "Przewidź, co wypisze program, i zapisz wynik. Potem sprawdź na komputerze.",
                (
                    Listing(
                        (
                            'for kolor in ["czerwony", "zielony", "niebieski"]:',
                            '    print("Lubię", kolor)',
                        )
                    ),
                    Lines(3),
                ),
                ("Lubię czerwony", "Lubię zielony", "Lubię niebieski"),
            ),
            Task(
                "Uzupełnij tabelkę obrotów: jaka jest wartość n i suma po każdym obrocie? Co wypisze program?",
                (
                    Listing(
                        ("suma = 0", "for n in [5, 1, 4]:", "    suma = suma + n", "print(suma)")
                    ),
                    FillTable((("obrót", "1", "2", "3"), ("n", "", "", ""), ("suma", "", "", ""))),
                ),
                ("n: 5, 1, 4; suma: 5, 6, 10. Program wypisze 10.",),
            ),
            Task(
                "Ile razy pojawi się słowo Hej, a ile razy Pa? Uzasadnij jednym zdaniem.",
                (Listing(("for x in [1, 2, 3, 4]:", '    print("Hej")', 'print("Pa")')), Lines(2)),
                (
                    "Hej – 4 razy (lista ma 4 elementy), Pa – 1 raz (linia bez wcięcia jest poza pętlą).",
                ),
            ),
            Task(
                "Napisz program, który wypisze każdą literę Twojego imienia w osobnej linii.",
                (Lines(3),),
                (Listing(('imie = "Ola"', "for litera in imie:", "    print(litera)")),),
            ),
            Task(
                "Napisz program, który policzy sumę liczb z listy [10, 20, 30, 40] i ją wypisze. Jaki wynik wyszedł?",
                (Lines(4),),
                (
                    Listing(
                        (
                            "suma = 0",
                            "for liczba in [10, 20, 30, 40]:",
                            "    suma = suma + liczba",
                            "print(suma)",
                        )
                    ),
                    "Wynik: 100.",
                ),
            ),
            Task(
                "Znajdź dwa błędy w programie i zapisz poprawną wersję.",
                (Listing(("for liczba in [1, 2, 3]", "print(liczba)")), Lines(2)),
                (
                    "Brakuje dwukropka na końcu linii for i wcięcia przed print:",
                    Listing(("for liczba in [1, 2, 3]:", "    print(liczba)")),
                ),
            ),
        ],
    )
    worksheet(
        "p2_k_karta.pdf",
        f"{course} · lekcja 2",
        "range()",
        "Zasada: range(start, stop, krok) – liczba stop nie należy do ciągu. Sprawdzaj ciągi poleceniem print(list(range(…))).",
        [
            Task(
                "Wypisz liczby, które daje: a) range(6) b) range(3, 8) c) range(1, 10, 2) d) range(10, 0, -2).",
                (Lines(4),),
                (
                    "a) 0, 1, 2, 3, 4, 5",
                    "b) 3, 4, 5, 6, 7",
                    "c) 1, 3, 5, 7, 9",
                    "d) 10, 8, 6, 4, 2",
                ),
            ),
            Task(
                "Dobierz zapis range do opisu: a) liczby od 1 do 5, b) 0, 5, 10, 15, 20, c) 3, 2, 1, 0.",
                (Lines(3),),
                ("a) range(1, 6)", "b) range(0, 21, 5)", "c) range(3, -1, -1)"),
            ),
            Task(
                "Ile razy program wypisze słowo Python?",
                (Listing(("for i in range(3, 9):", '    print("Python")')), Lines(1)),
                ("6 razy (i = 3, 4, 5, 6, 7, 8).",),
            ),
            Task(
                "Napisz program, który wypisze tabliczkę mnożenia przez 7: 7, 14, …, 70.",
                (Lines(3),),
                (
                    Listing(("for i in range(1, 11):", "    print(7 * i)")),
                    "albo: for i in range(7, 71, 7): print(i)",
                ),
            ),
            Task(
                "Napisz program, który policzy sumę liczb od 1 do 100. Jaki wynik wyszedł?",
                (Lines(4),),
                (
                    Listing(
                        (
                            "suma = 0",
                            "for i in range(1, 101):",
                            "    suma = suma + i",
                            "print(suma)",
                        )
                    ),
                    "Wynik: 5050.",
                ),
            ),
            Task(
                "Odliczanie: wypisz 10, 9, …, 1, a potem napis Start!",
                (Lines(3),),
                (Listing(("for i in range(10, 0, -1):", "    print(i)", 'print("Start!")')),),
            ),
        ],
    )
    worksheet(
        "p3_k_karta.pdf",
        f"{course} · lekcja 3",
        "Pętla while",
        "while sprawdza warunek przed każdym obrotem. W ciele zmieniaj zmienną z warunku, inaczej pętla się nie skończy.",
        [
            Task(
                "Uzupełnij tabelkę obrotów i zapisz, co wypisze program.",
                (
                    Listing(("x = 2", "while x < 20:", "    print(x)", "    x = x * 3")),
                    FillTable(
                        (
                            ("x", "2", "", "", ""),
                            ("x < 20?", "", "", "", ""),
                            ("wypisze", "", "", "", ""),
                        )
                    ),
                ),
                ("x: 2, 6, 18, 54; x < 20: tak, tak, tak, nie.", "Program wypisze 2, 6, 18."),
            ),
            Task(
                "Napisz odliczanie 5, 4, 3, 2, 1, a po nim napis Start! – użyj pętli while.",
                (Lines(5),),
                (
                    Listing(
                        (
                            "i = 5",
                            "while i > 0:",
                            "    print(i)",
                            "    i = i - 1",
                            'print("Start!")',
                        )
                    ),
                ),
            ),
            Task(
                "Dlaczego ten program nigdy się nie kończy? Popraw go.",
                (Listing(("k = 0", "while k < 3:", '    print("Hej")')), Lines(2)),
                (
                    "k się nie zmienia, więc warunek k < 3 jest zawsze prawdziwy. Dopisz w ciele (z wcięciem): k = k + 1.",
                ),
            ),
            Task(
                "Napisz program, który pyta o hasło (input), dopóki użytkownik nie wpisze słowa python, a potem wypisuje Witaj! (warunek „różne od” zapisujemy !=).",
                (Lines(4),),
                (
                    Listing(
                        (
                            'haslo = ""',
                            'while haslo != "python":',
                            '    haslo = input("Hasło: ")',
                            'print("Witaj!")',
                        )
                    ),
                ),
            ),
            Task(
                "Ile razy wykona się ciało pętli? k = 0, potem while k < 10: z wciętym k = k + 2.",
                (Lines(1),),
                (
                    "5 razy (k przed obrotami: 0, 2, 4, 6, 8; potem k = 10 i warunek jest fałszywy).",
                ),
            ),
        ],
    )
    worksheet(
        "p4_k_karta.pdf",
        f"{course} · lekcja 4",
        "break i continue",
        "break kończy całą pętlę, continue pomija resztę bieżącego obrotu. % to reszta z dzielenia.",
        [
            Task(
                "Co wypisze program?",
                (
                    Listing(
                        (
                            'for litera in "python":',
                            '    if litera == "h":',
                            "        break",
                            "    print(litera)",
                        )
                    ),
                    Lines(1),
                ),
                ("p, y, t (przy literze h pętla się kończy).",),
            ),
            Task(
                "Co wypisze program? (!= znaczy „różne od”)",
                (
                    Listing(
                        (
                            "for n in range(1, 11):",
                            "    if n % 3 != 0:",
                            "        continue",
                            "    print(n)",
                        )
                    ),
                    Lines(1),
                ),
                ("3, 6, 9 (liczby niepodzielne przez 3 są pomijane).",),
            ),
            Task(
                "Ile wynosi: a) 10 % 3, b) 15 % 5, c) 9 % 2?",
                (Lines(1),),
                ("a) 1, b) 0, c) 1.",),
            ),
            Task(
                "Napisz program, który przechodzi po liście [4, 7, 12, 9, 20], wypisuje pierwszą liczbę większą od 10 i kończy pętlę.",
                (Lines(4),),
                (
                    Listing(
                        (
                            "for n in [4, 7, 12, 9, 20]:",
                            "    if n > 10:",
                            "        print(n)",
                            "        break",
                        )
                    ),
                    "Wypisze 12.",
                ),
            ),
            Task(
                "Napisz program, który wypisuje liczby od 1 do 20 z pominięciem liczb podzielnych przez 5 (użyj continue).",
                (Lines(4),),
                (
                    Listing(
                        (
                            "for n in range(1, 21):",
                            "    if n % 5 == 0:",
                            "        continue",
                            "    print(n)",
                        )
                    ),
                ),
            ),
            Task(
                "Mała gra: napisz pętlę while True, która prosi o liczbę (int(input())) i kończy się, gdy użytkownik wpisze 0. Na końcu wypisz Koniec gry.",
                (Lines(5),),
                (
                    Listing(
                        (
                            "while True:",
                            '    liczba = int(input("Podaj liczbę: "))',
                            "    if liczba == 0:",
                            "        break",
                            'print("Koniec gry")',
                        )
                    ),
                ),
            ),
        ],
    )


# --- Main ----------------------------------------------------------------------------------------

IMAGES: tuple[Callable[[], None], ...] = (
    m1_graph,
    m1_scheme,
    m2_direction,
    m2_slope,
    m3_zero,
    m3_cases,
    m4_taxis,
    m4_candle,
    e1_structure,
    e1_forms,
    e2_words,
    e3_for_since,
    e4_timeline,
    p1_flowchart,
    p1_code,
    p2_range,
    p3_flowchart,
    p3_code,
    p4_break_continue,
)
WORKSHEETS: tuple[Callable[[], None], ...] = (
    math_worksheets,
    english_worksheets,
    python_worksheets,
)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for make in (*IMAGES, *WORKSHEETS):
        make()


if __name__ == "__main__":
    main()
