"""Wykresy funkcji liniowych jako SVG generowane w kodzie (bez zewnętrznych bibliotek i obrazków)."""
from dataclasses import dataclass, field
from fractions import Fraction
from xml.sax.saxutils import escape

Liczba = Fraction | int

JEDNOSTKA = 36  # pixels per unit
MARGINES = 44
KOLORY = ("#0ea5e9", "#8b5cf6", "#10b981")
FONT = 'font-family="Segoe UI, Arial, sans-serif"'


@dataclass(frozen=True)
class Prosta:
    """Prosta y = ax + b."""

    a: Liczba
    b: Liczba

    def wartosc(self, x: Liczba) -> Fraction:
        return Fraction(self.a) * Fraction(x) + Fraction(self.b)


@dataclass(frozen=True)
class Punkt:
    x: Liczba
    y: Liczba
    # e.g. "miejsce_zerowe", "przeciecie_oy", "punkt"
    rola: str = "punkt"
    etykieta: str | None = None
    # Label offset in pixels (right / down positive)
    dx: int = 10
    dy: int = -10


@dataclass(frozen=True)
class Schodek:
    """Trójkąt „o ile w prawo, o ile w górę" między dwoma punktami prostej."""

    x1: Liczba
    y1: Liczba
    x2: Liczba
    y2: Liczba


@dataclass(frozen=True)
class Wykres:
    plik: str
    tytul: str
    proste: tuple[Prosta, ...]
    punkty: tuple[Punkt, ...] = ()
    schodek: Schodek | None = None
    x_min: int = -5
    x_max: int = 5
    y_min: int = -5
    y_max: int = 5
    etykiety_prostych: tuple[str, ...] = field(default=())


def liczba_tekst(v: Liczba) -> str:
    """Liczba do opisu na wykresie: całkowita albo ułamek zwykły, z prawdziwym minusem."""
    f = Fraction(v)
    tekst = str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
    return tekst.replace("-", "−")


def wzor_tekst(a: Liczba, b: Liczba) -> str:
    """Wzór prostej zwykłym tekstem, np. 'y = −2x + 3'."""
    a, b = Fraction(a), Fraction(b)
    if a == 0:
        return f"y = {liczba_tekst(b)}"
    if a == 1:
        czesc_x = "x"
    elif a == -1:
        czesc_x = "−x"
    elif a.denominator == 1:
        czesc_x = f"{liczba_tekst(a)}x"
    else:
        czesc_x = f"({liczba_tekst(a)})x"
    if b == 0:
        return f"y = {czesc_x}"
    znak = "+" if b > 0 else "−"
    return f"y = {czesc_x} {znak} {liczba_tekst(abs(b))}"


def _zmiana(v: Fraction) -> str:
    return ("+" if v > 0 else "") + liczba_tekst(v)


ZNAK_TYTULU_PX = 7.8  # approximate width of one character of the bold 15 px title


def linie_tytulu(tytul: str, szerokosc: float) -> list[str]:
    """Tytuł w jednej linii, a gdy się nie mieści — łamany po dwukropku."""
    if len(tytul) * ZNAK_TYTULU_PX <= szerokosc - 20 or ": " not in tytul:
        return [tytul]
    poczatek, reszta = tytul.split(": ", 1)
    return [poczatek + ":", reszta]


def wykres_svg(w: Wykres) -> str:
    """Układ współrzędnych z siatką i podziałką, proste, zaznaczone punkty i opcjonalny „schodek"."""
    szer = 2 * MARGINES + (w.x_max - w.x_min) * JEDNOSTKA
    tytul = linie_tytulu(w.tytul, szer)
    # Room above the plot for the title (one or two rows)
    naglowek = 28 + 20 * (len(tytul) - 1)
    # Extra room: title on top, legend (one row per line) at the bottom
    wys = 2 * MARGINES + (w.y_max - w.y_min) * JEDNOSTKA + naglowek + 18 * len(w.proste)

    def px(x: Liczba) -> float:
        return MARGINES + float(Fraction(x) - w.x_min) * JEDNOSTKA

    def py(y: Liczba) -> float:
        return naglowek + MARGINES + float(w.y_max - Fraction(y)) * JEDNOSTKA

    lewo, prawo, gora, dol = px(w.x_min), px(w.x_max), py(w.y_max), py(w.y_min)
    cz: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {szer} {wys}" role="img" {FONT}>',
        f"<title>{escape(w.tytul)}</title>",
        f'<rect width="{szer}" height="{wys}" rx="16" fill="#f8fafc"/>',
        *(
            f'<text class="tytul" x="{szer / 2}" y="{28 + 20 * i}" text-anchor="middle" font-size="15" font-weight="700" fill="#0f172a">{escape(linia)}</text>'
            for i, linia in enumerate(tytul)
        ),
        f'<clipPath id="pole"><rect x="{lewo}" y="{gora}" width="{prawo - lewo}" height="{dol - gora}"/></clipPath>',
    ]

    # Grid
    for x in range(w.x_min, w.x_max + 1):
        cz.append(f'<line x1="{px(x)}" y1="{gora}" x2="{px(x)}" y2="{dol}" stroke="#e2e8f0" stroke-width="1"/>')
    for y in range(w.y_min, w.y_max + 1):
        cz.append(f'<line x1="{lewo}" y1="{py(y)}" x2="{prawo}" y2="{py(y)}" stroke="#e2e8f0" stroke-width="1"/>')

    # Axes with arrowheads
    ox, oy = py(0), px(0)
    cz.append(f'<line x1="{lewo - 8}" y1="{ox}" x2="{prawo + 14}" y2="{ox}" stroke="#0f172a" stroke-width="2"/>')
    cz.append(f'<polygon points="{prawo + 22},{ox} {prawo + 12},{ox - 5} {prawo + 12},{ox + 5}" fill="#0f172a"/>')
    cz.append(f'<line x1="{oy}" y1="{dol + 8}" x2="{oy}" y2="{gora - 14}" stroke="#0f172a" stroke-width="2"/>')
    cz.append(f'<polygon points="{oy},{gora - 22} {oy - 5},{gora - 12} {oy + 5},{gora - 12}" fill="#0f172a"/>')
    cz.append(f'<text x="{prawo + 20}" y="{ox + 20}" font-size="15" font-style="italic" fill="#0f172a">x</text>')
    cz.append(f'<text x="{oy + 10}" y="{gora - 14}" font-size="15" font-style="italic" fill="#0f172a">y</text>')

    # Tick marks with numbers
    for x in range(w.x_min, w.x_max + 1):
        if x == 0:
            continue
        cz.append(f'<line x1="{px(x)}" y1="{ox - 4}" x2="{px(x)}" y2="{ox + 4}" stroke="#0f172a" stroke-width="1.5"/>')
        cz.append(f'<text x="{px(x)}" y="{ox + 18}" text-anchor="middle" font-size="12" fill="#475569">{liczba_tekst(x)}</text>')
    for y in range(w.y_min, w.y_max + 1):
        if y == 0:
            continue
        cz.append(f'<line x1="{oy - 4}" y1="{py(y)}" x2="{oy + 4}" y2="{py(y)}" stroke="#0f172a" stroke-width="1.5"/>')
        cz.append(f'<text x="{oy - 9}" y="{py(y) + 4}" text-anchor="end" font-size="12" fill="#475569">{liczba_tekst(y)}</text>')
    cz.append(f'<text x="{oy - 9}" y="{ox + 16}" text-anchor="end" font-size="12" fill="#475569">0</text>')

    # Lines (clipped to the plotting area)
    for i, p in enumerate(w.proste):
        kolor = KOLORY[i % len(KOLORY)]
        cz.append(
            f'<line class="prosta" data-a="{Fraction(p.a)}" data-b="{Fraction(p.b)}" clip-path="url(#pole)" '
            f'x1="{px(w.x_min)}" y1="{py(p.wartosc(w.x_min))}" x2="{px(w.x_max)}" y2="{py(p.wartosc(w.x_max))}" '
            f'stroke="{kolor}" stroke-width="3"/>'
        )

    # Legend with formulas
    for i, p in enumerate(w.proste):
        kolor = KOLORY[i % len(KOLORY)]
        opis = w.etykiety_prostych[i] if i < len(w.etykiety_prostych) else wzor_tekst(p.a, p.b)
        y_leg = wys - 14 - (len(w.proste) - 1 - i) * 18
        cz.append(f'<line x1="{lewo}" y1="{y_leg - 4}" x2="{lewo + 22}" y2="{y_leg - 4}" stroke="{kolor}" stroke-width="3"/>')
        cz.append(f'<text x="{lewo + 30}" y="{y_leg}" font-size="14" font-weight="600" fill="{kolor}">{escape(opis)}</text>')

    # "Step" triangle: run and rise between two points
    if w.schodek:
        s = w.schodek
        cz.append(
            f'<path class="schodek" d="M {px(s.x1)} {py(s.y1)} H {px(s.x2)} V {py(s.y2)}" fill="none" '
            f'stroke="#f59e0b" stroke-width="2.5" stroke-dasharray="6 4"/>'
        )
        dx, dy = Fraction(s.x2) - Fraction(s.x1), Fraction(s.y2) - Fraction(s.y1)
        srodek_x = (px(s.x1) + px(s.x2)) / 2
        srodek_y = (py(s.y1) + py(s.y2)) / 2
        pod = 16 if dy > 0 else -8
        cz.append(f'<text x="{srodek_x}" y="{py(s.y1) + pod}" text-anchor="middle" font-size="13" font-weight="700" fill="#b45309">{_zmiana(dx)}</text>')
        cz.append(f'<text x="{px(s.x2) + 8}" y="{srodek_y + 4}" font-size="13" font-weight="700" fill="#b45309">{_zmiana(dy)}</text>')

    # Marked points
    for p in w.punkty:
        opis = p.etykieta or f"({liczba_tekst(p.x)}, {liczba_tekst(p.y)})"
        cz.append(
            f'<circle class="punkt" data-rola="{p.rola}" data-x="{Fraction(p.x)}" data-y="{Fraction(p.y)}" '
            f'cx="{px(p.x)}" cy="{py(p.y)}" r="5.5" fill="#ef4444" stroke="#ffffff" stroke-width="2"/>'
        )
        kotwica = "end" if p.dx < 0 else "start"
        cz.append(
            f'<text x="{px(p.x) + p.dx}" y="{py(p.y) + p.dy}" text-anchor="{kotwica}" font-size="13" font-weight="700" '
            f'fill="#b91c1c" stroke="#f8fafc" stroke-width="3" paint-order="stroke">{escape(opis)}</text>'
        )

    cz.append("</svg>")
    return "\n".join(cz) + "\n"
