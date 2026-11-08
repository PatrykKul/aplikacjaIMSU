# ruff: noqa: E501  (worksheet texts are content, not code; keeping sentences whole)
"""Generate the demo images (PNG) and worksheets (PDF) in `app/demo/assets/`.

One-off tool: the generated files are committed, so the seed (`python -m app.demo.seed`)
needs nothing extra. Regenerating requires Pillow, which is NOT a project dependency:

    python -m venv %TEMP%\\assets-venv && %TEMP%\\assets-venv\\Scripts\\pip install pillow
    %TEMP%\\assets-venv\\Scripts\\python app/demo/generate_assets.py

Fonts: Segoe UI and Consolas from Windows (Polish letters).
"""

import math
from collections.abc import Callable, Sequence
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ASSETS = Path(__file__).resolve().parent / "assets"
FONTS = Path("C:/Windows/Fonts")

W, H = 1200, 750
BG = "#ffffff"
INK = "#1e293b"
MUTED = "#64748b"
GRID = "#e2e8f0"
AXIS = "#334155"
BLUE = "#2563eb"
ORANGE = "#ea580c"
GREEN = "#16a34a"
PURPLE = "#7c3aed"
SOFT = {BLUE: "#dbeafe", ORANGE: "#ffedd5", GREEN: "#dcfce7", PURPLE: "#ede9fe"}


def font(size: int, bold: bool = False, mono: bool = False) -> ImageFont.FreeTypeFont:
    name = "consola.ttf" if mono else ("segoeuib.ttf" if bold else "segoeui.ttf")
    return ImageFont.truetype(str(FONTS / name), size)


def canvas(title: str, subtitle: str = "") -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw.text((48, 32), title, font=font(40, bold=True), fill=INK)
    if subtitle:
        draw.text((48, 86), subtitle, font=font(24), fill=MUTED)
    return image, draw


def save(image: Image.Image, name: str) -> None:
    image.save(ASSETS / name, optimize=True)
    print("ok", name)


# --- Function plots ----------------------------------------------------------------------------


class Plot:
    """Square grid in [-xr, xr] x [-yr, yr] placed in a box of the canvas."""

    def __init__(self, draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], r: int) -> None:
        self.draw, self.box, self.r = draw, box, r
        left, top, right, bottom = box
        self.unit = min(right - left, bottom - top) / (2 * r)
        self.cx = (left + right) / 2
        self.cy = (top + bottom) / 2

    def p(self, x: float, y: float) -> tuple[float, float]:
        return self.cx + x * self.unit, self.cy - y * self.unit

    def grid(self) -> None:
        r, d = self.r, self.draw
        for i in range(-r, r + 1):
            d.line([self.p(i, -r), self.p(i, r)], fill=GRID, width=1)
            d.line([self.p(-r, i), self.p(r, i)], fill=GRID, width=1)
        d.line([self.p(-r, 0), self.p(r, 0)], fill=AXIS, width=3)
        d.line([self.p(0, -r), self.p(0, r)], fill=AXIS, width=3)
        small = font(18)
        for i in range(-r, r + 1):
            if i == 0:
                continue
            x, y = self.p(i, 0)
            d.text((x, y + 6), str(i), font=small, fill=MUTED, anchor="ma")
            x, y = self.p(0, i)
            d.text((x - 8, y), str(i), font=small, fill=MUTED, anchor="rm")
        x, y = self.p(r, 0)
        d.text((x - 4, y - 10), "x", font=font(24, bold=True), fill=AXIS, anchor="rb")
        x, y = self.p(0, r)
        d.text((x + 10, y + 4), "y", font=font(24, bold=True), fill=AXIS, anchor="la")

    def line(self, f: Callable[[float], float], color: str, width: int = 5) -> None:
        r = self.r
        points = [(x / 10, f(x / 10)) for x in range(-r * 10, r * 10 + 1)]
        points = [(x, y) for x, y in points if -r <= y <= r]
        self.draw.line([self.p(x, y) for x, y in points], fill=color, width=width)

    def dot(self, x: float, y: float, color: str, label: str = "", dx: int = 14) -> None:
        px, py = self.p(x, y)
        self.draw.ellipse([px - 9, py - 9, px + 9, py + 9], fill=color, outline="white", width=3)
        if label:
            self.draw.text((px + dx, py - 34), label, font=font(22, bold=True), fill=color)


def legend(draw: ImageDraw.ImageDraw, x: int, y: int, items: Sequence[tuple[str, str]]) -> None:
    for i, (color, text) in enumerate(items):
        top = y + i * 52
        draw.rounded_rectangle([x, top, x + 36, top + 10], radius=5, fill=color)
        draw.text((x + 52, top + 5), text, font=font(26), fill=INK, anchor="lm")


def note(draw: ImageDraw.ImageDraw, x: int, y: int, lines: Sequence[str], color: str) -> None:
    height = 24 + 40 * len(lines)
    draw.rounded_rectangle([x, y, x + 520, y + height], radius=16, fill=SOFT[color])
    for i, text in enumerate(lines):
        draw.text((x + 22, y + 16 + i * 40), text, font=font(26), fill=INK)


def math_plot_basic() -> None:
    image, draw = canvas("Wykres funkcji y = 2x + 1", "Funkcja liniowa: wykres to prosta")
    plot = Plot(draw, (60, 140, 620, 730), 5)
    plot.grid()
    plot.line(lambda x: 2 * x + 1, BLUE)
    # Step triangle: 1 right, 2 up
    draw.line([plot.p(0, 1), plot.p(1, 1)], fill=ORANGE, width=4)
    draw.line([plot.p(1, 1), plot.p(1, 3)], fill=ORANGE, width=4)
    x, y = plot.p(0.5, 1)
    draw.text((x, y + 8), "1", font=font(22, bold=True), fill=ORANGE, anchor="ma")
    x, y = plot.p(1, 2)
    draw.text((x + 10, y), "2", font=font(22, bold=True), fill=ORANGE, anchor="lm")
    plot.dot(0, 1, GREEN, "(0, 1)", dx=-90)
    plot.dot(1, 3, BLUE, "(1, 3)")
    note(draw, 650, 170, ["b = 1", "prosta przecina oś y", "w punkcie (0, 1)"], GREEN)
    note(draw, 650, 360, ["a = 2", "krok w prawo o 1", "= krok w górę o 2"], ORANGE)
    draw.text((650, 560), "y = a·x + b", font=font(44, bold=True), fill=INK)
    draw.text((650, 620), "a – nachylenie, b – wyraz wolny", font=font(24), fill=MUTED)
    save(image, "m1_wykres.png")


def math_formula_map() -> None:
    image, draw = canvas("Wzór funkcji liniowej krok po kroku", "Jak z wzoru odczytać wykres")
    formula, big = "y = a · x + b", font(96, bold=True)
    start = W / 2 - big.getlength(formula) / 2
    draw.text((start, 230), formula, font=big, fill=INK, anchor="lm")

    def letter_x(letter: str) -> float:
        index = formula.index(letter)
        return start + big.getlength(formula[:index]) + big.getlength(letter) / 2

    boxes = [
        (90, ORANGE, "a", ["współczynnik", "kierunkowy:", "o ile rośnie y,", "gdy x rośnie o 1"]),
        (470, BLUE, "x", ["argument:", "liczba, którą", "wstawiamy", "do wzoru"]),
        (850, GREEN, "b", ["wyraz wolny:", "gdzie prosta", "przecina", "oś y"]),
    ]
    for left, color, letter, lines in boxes:
        draw.rounded_rectangle([left, 360, left + 260, 690], radius=20, fill=SOFT[color])
        draw.text((left + 130, 405), letter, font=font(56, bold=True), fill=color, anchor="mm")
        for i, text in enumerate(lines):
            draw.text((left + 130, 480 + i * 44), text, font=font(26), fill=INK, anchor="mm")
    for left, color, letter, _ in boxes:
        draw.line([(letter_x(letter), 290), (left + 130, 355)], fill=color, width=4)
    save(image, "m1_schemat.png")


def math_slopes() -> None:
    image, draw = canvas("Jak a zmienia wykres", "Trzy proste o wyrazie wolnym b = 0")
    plot = Plot(draw, (60, 140, 620, 730), 5)
    plot.grid()
    plot.line(lambda x: 2 * x, BLUE)
    plot.line(lambda x: 0.5 * x, GREEN)
    plot.line(lambda x: -x, ORANGE)
    legend(
        draw,
        660,
        190,
        [
            (BLUE, "y = 2x  (a = 2, stromo w górę)"),
            (GREEN, "y = 0,5x  (a = 0,5, łagodnie)"),
            (ORANGE, "y = −x  (a = −1, w dół)"),
        ],
    )
    note(
        draw,
        650,
        400,
        ["a > 0  →  funkcja rośnie", "a < 0  →  funkcja maleje", "a = 0  →  prosta pozioma"],
        PURPLE,
    )
    save(image, "m2_nachylenie.png")


def math_values_table() -> None:
    image, draw = canvas("Tabela wartości: y = −x + 3", "Wstaw x, policz y, zaznacz punkty")
    xs = [-1, 0, 1, 2, 3]
    left, top, cell = 120, 180, 150
    for row, label in enumerate(["x", "y"]):
        draw.rectangle(
            [left, top + row * 90, left + cell, top + (row + 1) * 90],
            fill=SOFT[PURPLE],
            outline=AXIS,
            width=2,
        )
        draw.text(
            (left + cell / 2, top + row * 90 + 45),
            label,
            font=font(40, bold=True),
            fill=PURPLE,
            anchor="mm",
        )
        for i, x in enumerate(xs):
            value = x if row == 0 else -x + 3
            x0 = left + cell * (i + 1)
            draw.rectangle(
                [x0, top + row * 90, x0 + cell, top + (row + 1) * 90], outline=AXIS, width=2
            )
            draw.text(
                (x0 + cell / 2, top + row * 90 + 45),
                str(value).replace("-", "−"),
                font=font(36),
                fill=INK,
                anchor="mm",
            )
    steps = [
        "1. Wybierz kilka x (np. od −1 do 3).",
        "2. Wstaw każdy do wzoru: y = −x + 3.",
        "3. Zaznacz punkty (x, y) w układzie.",
        "4. Połącz je linijką – to wykres.",
    ]
    for i, text in enumerate(steps):
        draw.text((120, 420 + i * 62), text, font=font(30), fill=INK)
    save(image, "m2_tabela.png")


def math_zero() -> None:
    image, draw = canvas("Miejsce zerowe funkcji y = 2x − 4", "Gdzie wykres przecina oś x?")
    plot = Plot(draw, (60, 140, 620, 730), 5)
    plot.grid()
    plot.line(lambda x: 2 * x - 4, BLUE)
    plot.dot(2, 0, ORANGE, "x₀ = 2")
    plot.dot(0, -4, GREEN, "(0, −4)")
    note(draw, 650, 170, ["Miejsce zerowe: y = 0", "2x − 4 = 0", "2x = 4", "x = 2"], ORANGE)
    note(draw, 650, 430, ["Wzór ogólny:", "x₀ = −b / a"], PURPLE)
    save(image, "m3_miejsce_zerowe.png")


# --- English -------------------------------------------------------------------------------------


def english_structure() -> None:
    image, draw = canvas(
        "Present Perfect: budowa zdania", "have / has + trzecia forma czasownika (V3)"
    )
    rows = [
        ("+", ["I / you / we / they", "have", "seen", "this film."]),
        ("+", ["he / she / it", "has", "finished", "the test."]),
        ("−", ["she", "hasn't", "called", "yet."]),
        ("?", ["Have", "you", "ever been", "to London?"]),
    ]
    colors = [PURPLE, BLUE, ORANGE, GREEN]
    widths = [300, 180, 220, 300]
    for r, (sign, parts) in enumerate(rows):
        top = 170 + r * 130
        draw.text((70, top + 40), sign, font=font(48, bold=True), fill=INK, anchor="mm")
        left = 120
        for i, part in enumerate(parts):
            color = colors[i] if sign != "?" else [BLUE, PURPLE, ORANGE, GREEN][i]
            draw.rounded_rectangle(
                [left, top, left + widths[i] - 14, top + 84], radius=16, fill=SOFT[color]
            )
            draw.text(
                (left + (widths[i] - 14) / 2, top + 42),
                part,
                font=font(30, bold=i == 1),
                fill=INK,
                anchor="mm",
            )
            left += widths[i]
    labels = [(120, "osoba"), (420, "have/has"), (600, "V3"), (820, "reszta")]
    for x, text in labels:
        draw.text((x, 700), text, font=font(22), fill=MUTED)
    save(image, "e1_budowa.png")


def english_timeline() -> None:
    image, draw = canvas("Present Perfect czy Past Simple?", "Oś czasu: przeszłość → teraz")
    y = 380
    draw.line([(80, y), (1110, y)], fill=AXIS, width=5)
    draw.polygon([(1120, y), (1095, y - 14), (1095, y + 14)], fill=AXIS)
    draw.text((80, y + 24), "przeszłość", font=font(24), fill=MUTED)
    draw.ellipse([960, y - 14, 988, y + 14], fill=INK)
    draw.text((974, y + 24), "TERAZ", font=font(26, bold=True), fill=INK, anchor="ma")
    # Past Simple: a finished point in the past
    draw.ellipse([300, y - 14, 328, y + 14], fill=ORANGE)
    draw.text((314, y - 110), "Past Simple", font=font(30, bold=True), fill=ORANGE, anchor="ma")
    draw.text((314, y - 70), "I saw it yesterday.", font=font(26), fill=INK, anchor="ma")
    note(draw, 90, 470, ["zakończone, wiemy kiedy:", "yesterday, last week, in 2020"], ORANGE)
    # Present Perfect: arc to now
    draw.arc([520, y - 170, 980, y + 170], start=180, end=360, fill=BLUE, width=6)
    draw.text((750, y - 120), "Present Perfect", font=font(30, bold=True), fill=BLUE, anchor="ma")
    draw.text((750, y - 78), "I have seen it.", font=font(26), fill=INK, anchor="ma")
    note(
        draw,
        620,
        470,
        ["ważny skutek teraz, czas nieważny:", "ever, never, already, yet, just"],
        BLUE,
    )
    save(image, "e2_os_czasu.png")


# --- Python --------------------------------------------------------------------------------------


def box(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    text: str,
    color: str,
    diamond: bool = False,
    w: int = 380,
    h: int = 90,
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
        draw.rounded_rectangle(
            [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2],
            radius=18,
            fill=SOFT[color],
            outline=color,
            width=4,
        )
    draw.multiline_text(
        (cx, cy), text, font=font(26, bold=True), fill=INK, anchor="mm", align="center", spacing=6
    )


def arrow(
    draw: ImageDraw.ImageDraw, points: Sequence[tuple[float, float]], label: str = ""
) -> None:
    draw.line(list(points), fill=AXIS, width=4, joint="curve")
    (x1, y1), (x2, y2) = points[-2], points[-1]
    angle = math.atan2(y2 - y1, x2 - x1)
    tip = [
        (x2, y2),
        (x2 - 18 * math.cos(angle - 0.4), y2 - 18 * math.sin(angle - 0.4)),
        (x2 - 18 * math.cos(angle + 0.4), y2 - 18 * math.sin(angle + 0.4)),
    ]
    draw.polygon(tip, fill=AXIS)
    if label:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        draw.text((mx + 12, my), label, font=font(24, bold=True), fill=AXIS, anchor="lm")


def loop_flowchart(name: str, title: str, subtitle: str, steps: Sequence[str]) -> None:
    image, draw = canvas(title, subtitle)
    start, check, body, after, end = (420, 175), (420, 335), (420, 520), (420, 665), (900, 335)
    box(draw, start, steps[0], PURPLE)
    box(draw, check, steps[1], ORANGE, diamond=True, w=420, h=85)
    box(draw, body, steps[2], BLUE, h=110)
    box(draw, after, steps[3], BLUE, h=70)
    box(draw, end, steps[4], GREEN, w=300)
    arrow(draw, [(420, 220), (420, 250)])
    arrow(draw, [(420, 420), (420, 465)], "tak")
    arrow(draw, [(420, 575), (420, 630)])
    # Back from the body to the check, on the left; the exit goes right
    arrow(draw, [(230, 665), (130, 665), (130, 232), (420, 232), (420, 250)])
    draw.line([(630, 335), (750, 335)], fill=AXIS, width=4)
    arrow(draw, [(700, 335), (750, 335)])
    draw.text((680, 325), "nie", font=font(24, bold=True), fill=AXIS, anchor="mb")
    save(image, name)


def code_snippet() -> None:
    image, draw = canvas("Pętla for w praktyce", "Kod i to, co wypisze program")
    draw.rounded_rectangle([48, 140, 700, 700], radius=18, fill="#0f172a")
    code = [
        ("# suma liczb od 1 do 5", "#94a3b8"),
        ("suma = 0", "#e2e8f0"),
        ("for i in range(1, 6):", "#93c5fd"),
        ("    suma = suma + i", "#e2e8f0"),
        ("    print(i, suma)", "#e2e8f0"),
        ("", "#e2e8f0"),
        ('print("Wynik:", suma)', "#86efac"),
    ]
    for i, (line, color) in enumerate(code):
        draw.text((80, 180 + i * 62), line, font=font(32, mono=True), fill=color)
    draw.rounded_rectangle([740, 140, 1152, 700], radius=18, fill="#f1f5f9", outline=GRID, width=2)
    draw.text((770, 160), "Wynik:", font=font(26, bold=True), fill=MUTED)
    output = ["1 1", "2 3", "3 6", "4 10", "5 15", "Wynik: 15"]
    for i, line in enumerate(output):
        draw.text((770, 220 + i * 62), line, font=font(32, mono=True), fill=INK)
    save(image, "p1_kod.png")


# --- Worksheets (PDF) ----------------------------------------------------------------------------

A4 = (1240, 1754)  # 150 dpi


def worksheet(name: str, title: str, intro: str, tasks: Sequence[tuple[str, int]]) -> None:
    """One A4 page: title, instruction and numbered tasks with lined space for answers."""
    page = Image.new("RGB", A4, "white")
    draw = ImageDraw.Draw(page)
    draw.rectangle([0, 0, A4[0], 22], fill=BLUE)
    draw.text((90, 80), "KARTA ĆWICZEŃ", font=font(28, bold=True), fill=BLUE)
    draw.text((90, 125), title, font=font(52, bold=True), fill=INK)
    draw.text(
        (90, 205), "Imię: ______________________     Data: ____________", font=font(28), fill=MUTED
    )
    y = 280
    for line in wrap(intro, font(30), A4[0] - 180):
        draw.text((90, y), line, font=font(30), fill=INK)
        y += 44
    y += 30
    for number, (task, lines) in enumerate(tasks, start=1):
        for i, line in enumerate(wrap(task, font(30), A4[0] - 240)):
            if i == 0:
                draw.text((90, y), f"{number}.", font=font(30, bold=True), fill=BLUE)
            draw.text((150, y), line, font=font(30), fill=INK)
            y += 44
        for _ in range(lines):
            y += 54
            draw.line([(150, y), (A4[0] - 90, y)], fill=GRID, width=2)
        y += 40
    draw.text(
        (90, A4[1] - 80),
        "Materiał kinestetyczny: wydrukuj albo rozwiąż w zeszycie.",
        font=font(24),
        fill=MUTED,
    )
    page.save(ASSETS / name, "PDF", resolution=150)
    print("ok", name)


def wrap(text: str, typeface: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if typeface.getlength(candidate) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def worksheets() -> None:
    worksheet(
        "m1_karta.pdf",
        "Wykres funkcji liniowej",
        "Weź kartkę w kratkę i linijkę. Każde zadanie zrób samodzielnie, krok po kroku.",
        [
            ("Narysuj układ współrzędnych od −5 do 5 na obu osiach.", 1),
            ("Dla y = 2x + 1 policz y dla x = −2, −1, 0, 1, 2 i zapisz w tabelce.", 3),
            ("Zaznacz punkty i połącz je linijką. Sprawdź: czy prosta przechodzi przez (0, 1)?", 2),
            ("Odczytaj z wykresu: dla jakiego x wartość y = 5?", 2),
            ("Wymyśl własną funkcję y = ax + b, narysuj ją i podpisz a i b.", 3),
        ],
    )
    worksheet(
        "m2_karta.pdf",
        "Współczynnik kierunkowy a",
        "Sprawdź w praktyce, jak liczba a zmienia wykres. Rysuj wszystkie proste w jednym układzie.",
        [
            ("Narysuj y = x, y = 3x oraz y = −2x. Która prosta jest najbardziej stroma?", 3),
            ("Uzupełnij: jeśli a > 0, funkcja ...; jeśli a < 0, funkcja ...", 2),
            ("Z kolegą: jedna osoba podaje a, druga rysuje prostą. Zamieńcie się 3 razy.", 2),
            ("Prosta przechodzi przez (0, 0) i (2, 6). Policz a.", 2),
        ],
    )
    worksheet(
        "m3_karta.pdf",
        "Miejsce zerowe",
        "Miejsce zerowe to x, dla którego y = 0. Licz na kartce i sprawdzaj na wykresie.",
        [
            ("Policz miejsce zerowe: y = 3x − 6.", 2),
            ("Policz miejsce zerowe: y = −2x + 8.", 2),
            ("Narysuj y = x + 2 i odczytaj miejsce zerowe z wykresu.", 3),
            ("Czy funkcja y = 4 ma miejsce zerowe? Uzasadnij jednym zdaniem.", 2),
        ],
    )
    worksheet(
        "e1_karta.pdf",
        "Present Perfect – budowa zdania",
        "Uzupełnij zdania formą have/has + V3. Potem przeczytaj je na głos.",
        [
            ("I ______ (finish) my homework.", 1),
            ("She ______ (visit) Paris twice.", 1),
            ("We ______ (not / see) this film.", 1),
            ("______ you ever ______ (eat) sushi?", 1),
            ("Napisz 3 zdania o tym, co już dziś zrobiłeś(-aś): I have already ...", 3),
        ],
    )
    worksheet(
        "e2_karta.pdf",
        "Present Perfect czy Past Simple?",
        "Wybierz czas. Podkreśl słowo, które Ci podpowiedziało (yesterday, ever, just ...).",
        [
            ("I ______ (lose) my keys yesterday.", 1),
            ("I ______ (lose) my keys. I can't open the door!", 1),
            ("______ you ______ (be) to Spain? – Yes, I ______ (go) there in 2019.", 2),
            ("They ______ (just / arrive).", 1),
            ("Zrób z kolegą mini-wywiad: 3 pytania „Have you ever ...?” i zapisz odpowiedzi.", 3),
        ],
    )
    worksheet(
        "p1_karta.pdf",
        "Pętla for",
        "Każdy program najpierw przewiduj na kartce, potem uruchom go w Pythonie i porównaj.",
        [
            ("Napisz pętlę, która wypisze liczby od 1 do 10.", 2),
            ("Napisz pętlę, która wypisze tylko liczby parzyste od 2 do 20 (range z krokiem).", 2),
            ("Policz sumę liczb od 1 do 100. Jaki wynik wyszedł?", 2),
            ("Wypisz każdą literę słowa „Python” w osobnej linii.", 2),
        ],
    )
    worksheet(
        "p2_karta.pdf",
        "Pętla while",
        "Pętla while działa, dopóki warunek jest prawdziwy. Uważaj na pętlę bez końca!",
        [
            ("Zamień pętlę for z zadania 1 poprzedniej karty na pętlę while.", 3),
            ("Napisz odliczanie 10, 9, ..., 1 i na końcu „Start!”.", 2),
            ("Program pyta o hasło, dopóki użytkownik nie wpisze „python”.", 3),
            ("Znajdź błąd: i = 0; while i < 5: print(i). Co się stanie i jak to naprawić?", 2),
        ],
    )


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    math_plot_basic()
    math_formula_map()
    math_slopes()
    math_values_table()
    math_zero()
    english_structure()
    english_timeline()
    loop_flowchart(
        "p1_schemat_for.png",
        "Jak działa pętla for",
        "for i in range(1, 6):",
        ["i = 1", "czy i ≤ 5?", "wykonaj ciało pętli\n(np. print(i))", "i = i + 1", "koniec pętli"],
    )
    loop_flowchart(
        "p2_schemat_while.png",
        "Jak działa pętla while",
        "while warunek:",
        [
            "przygotuj zmienne",
            "czy warunek\nprawdziwy?",
            "wykonaj ciało pętli",
            "zmień zmienną",
            "koniec pętli",
        ],
    )
    code_snippet()
    worksheets()


if __name__ == "__main__":
    main()
