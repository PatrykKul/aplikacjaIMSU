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


# --- Worksheets (PDF) ----------------------------------------------------------------------------

A4 = (1240, 1754)  # 150 dpi
MARGIN = 90
CONTENT = A4[0] - 2 * MARGIN
BOTTOM = A4[1] - 120
GRID_CELL = 40


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
        # keep the task text together with its first answer space
        self.ensure(len(lines) * 42 + 10 + (self.height(task.work[0]) if task.work else 0))
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
        first.save(ASSETS / name, "PDF", resolution=150, save_all=True, append_images=rest)
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
                "Dwie wypożyczalnie: A – y = 4x + 5, B – y = 6x + 1 (x – godziny, y – zł). Narysuj oba wykresy dla x od 0 do 4 (1 kratka = 1 h w poziomie i 2 zł w pionie) i odczytaj, przy ilu godzinach koszt jest równy.",
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
)
WORKSHEETS: tuple[Callable[[], None], ...] = (math_worksheets,)


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    for make in (*IMAGES, *WORKSHEETS):
        make()


if __name__ == "__main__":
    main()
