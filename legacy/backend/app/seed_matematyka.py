"""Kurs demonstracyjny „Matematyka: funkcja liniowa" (liceum, klasa 1).

Każdy temat ma bloki wspólne oraz osobne dla stylu V (wykresy SVG generowane w kodzie),
A (omówienie słowne dla lektora) i K (ćwiczenie krok po kroku), a także przykłady na poziomach 1 / 2 / 3.

Liczby w treści są zapisane wprost, a obok — w polach `sprawdzenia` — stoją dane, z których test
`tests/test_seed_matematyka.py` przelicza je niezależnie (na ułamkach) i porównuje z tekstem.
Wykresy powstają z tych samych funkcji i punktów, które opisuje treść.
"""
from fractions import Fraction as F

from app.wykresy import Prosta, Punkt, Schodek, Wykres

NAZWA_KURSU_MATEMATYKA = "Matematyka: funkcja liniowa"
KATALOG_WYKRESOW = ("demo", "matematyka")


def url_wykresu(plik: str) -> str:
    return "/media/" + "/".join(KATALOG_WYKRESOW) + "/" + plik


# ---------------------------------------------------------------------------
# TeX formatting used in the content and in the tests
# ---------------------------------------------------------------------------


def tex(v) -> str:
    """Liczba w TeX-u: całkowita albo ułamek zwykły, np. -\\tfrac{3}{2}."""
    f = F(v)
    if f.denominator == 1:
        return str(f.numerator)
    znak = "-" if f < 0 else ""
    return rf"{znak}\tfrac{{{abs(f.numerator)}}}{{{f.denominator}}}"


def punkt_tex(x, y) -> str:
    return f"({tex(x)}, {tex(y)})"


def wzor_tex(a, b) -> str:
    """Wzór y = ax + b w TeX-u, np. 'y = -2x + 3' albo 'y = \\tfrac{3}{4}x + \\tfrac{11}{4}'."""
    a, b = F(a), F(b)
    if a == 0:
        return f"y = {tex(b)}"
    czesc_x = "x" if a == 1 else "-x" if a == -1 else f"{tex(a)}x"
    if b == 0:
        return f"y = {czesc_x}"
    return f"y = {czesc_x} {'+' if b > 0 else '-'} {tex(abs(b))}"


def _quiz(*pytania: tuple[str, list[str], int, dict]) -> dict:
    """Quiz + dane do niezależnego sprawdzenia klucza (pole `sprawdzenia_quizu` bloku)."""
    return {
        "dane": {"pytania": [{"tresc": t, "odpowiedzi": o, "poprawna": p} for t, o, p, _ in pytania]},
        "sprawdzenia_quizu": [s for *_, s in pytania],
    }


def _kroki(*kroki: tuple[str, str | None]) -> dict:
    return {"kroki": [{"polecenie": p, "podpowiedz": h} for p, h in kroki]}


# ===========================================================================
# Topic 1: y = ax + b — the meaning of a and b
# ===========================================================================

WYKRES_1A = Wykres(
    plik="wzor-schodek.svg",
    tytul="y = 2x + 3: 1 w prawo, 2 w górę",
    proste=(Prosta(2, 3),),
    punkty=(
        Punkt(0, 3, "przeciecie_oy", "b = 3", dx=-10, dy=-8),
        Punkt(1, 5, "punkt", "(1, 5)"),
    ),
    schodek=Schodek(0, 3, 1, 5),
    x_min=-4,
    x_max=4,
    y_min=-2,
    y_max=8,
)

WYKRES_1B = Wykres(
    plik="wzor-rownolegle.svg",
    tytul="To samo a = 2, różne b",
    proste=(Prosta(2, 3), Prosta(2, 0), Prosta(2, -2)),
    punkty=(
        Punkt(0, 3, "przeciecie_oy", "(0, 3)", dx=-10, dy=-8),
        Punkt(0, 0, "przeciecie_oy", "(0, 0)", dx=10, dy=18),
        Punkt(0, -2, "przeciecie_oy", "(0, −2)", dx=10, dy=18),
    ),
    x_min=-4,
    x_max=4,
    y_min=-5,
    y_max=7,
)

TEMAT_1 = {
    "tytul": "Wzór funkcji liniowej y = ax + b",
    "wykresy": (WYKRES_1A, WYKRES_1B),
    "bloki": [
        {
            "typ": "teoria",
            "tresc": r"""## Ściąga

$$
y = ax + b
$$

- $a$ — **współczynnik kierunkowy**: mówi, o ile zmienia się $y$, gdy $x$ rośnie o $1$.
- $b$ — **wyraz wolny**: wartość funkcji dla $x = 0$. Wykres przecina oś $OY$ w punkcie $(0, b)$.

**Przykład:** $y = 2x + 3$. Tutaj $a = 2$ i $b = 3$.

Podstawiamy kolejne liczby: $f(0) = 3$, $f(1) = 5$, $f(2) = 7$. Za każdym razem, gdy $x$ rośnie o $1$, wynik rośnie o $2$ — właśnie tyle wynosi $a$.""",
            "sprawdzenia": [
                ("wartosc", {"a": 2, "b": 3, "x": 0}, "f(0) = 3"),
                ("wartosc", {"a": 2, "b": 3, "x": 1}, "f(1) = 5"),
                ("wartosc", {"a": 2, "b": 3, "x": 2}, "f(2) = 7"),
            ],
        },
        {
            "typ": "diagram",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_1A.plik),
            "tresc": r"Wykres funkcji $y = 2x + 3$. Zaczynasz w punkcie $(0, 3)$ — to jest $b$. Potem „schodek”: $1$ w prawo i $2$ w górę — to jest $a$. Trafiasz w punkt $(1, 5)$.",
            "sprawdzenia": [
                ("oy", {"a": 2, "b": 3}, "(0, 3)"),
                ("punkt", {"a": 2, "b": 3, "x": 1}, "(1, 5)"),
            ],
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_1B.plik),
            "tresc": r"Trzy funkcje z tym samym $a = 2$: $y = 2x + 3$, $y = 2x$ i $y = 2x - 2$. Nachylenie jest identyczne, więc proste są równoległe. Zmienia się tylko $b$, czyli miejsce przecięcia z osią $OY$: $(0, 3)$, $(0, 0)$ i $(0, -2)$.",
            "sprawdzenia": [
                ("oy", {"a": 2, "b": 3}, "(0, 3)"),
                ("oy", {"a": 2, "b": 0}, "(0, 0)"),
                ("oy", {"a": 2, "b": -2}, "(0, -2)"),
            ],
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Posłuchaj. Funkcja liniowa ma wzór: igrek równa się a razy iks plus b. "
                "Są w nim dwie liczby i każda ma swoje zadanie. "
                "Litera a to współczynnik kierunkowy. Mówi, o ile zmienia się igrek, kiedy iks rośnie o jeden. "
                "Litera b to wyraz wolny. To wartość funkcji dla iksa równego zero, czyli miejsce, w którym wykres przecina oś igrek. "
                "Weźmy przykład: igrek równa się dwa iks plus trzy. Tutaj a wynosi dwa, a b wynosi trzy. "
                "Dla iksa równego zero dostajemy trzy. Dla iksa równego jeden dostajemy pięć. Dla iksa równego dwa dostajemy siedem. "
                "Słyszysz? Trzy, pięć, siedem. Za każdym razem o dwa więcej. To właśnie jest a. "
                "Zapamiętaj krótko: b mówi, skąd startujesz, a mówi, jak szybko idziesz w górę albo w dół."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": r"Weź kartkę w kratkę i ołówek. Pracujemy z funkcją $y = 3x - 2$. Każdy krok wykonaj na kartce, zanim klikniesz „Zrobione”.",
            "dane": _kroki(
                (r"Zapisz, ile wynosi $a$, a ile $b$.", r"$a = 3$, $b = -2$. Minus należy do liczby."),
                (r"Podstaw $x = 0$ i oblicz wartość funkcji.", r"$3 \cdot 0 - 2$, czyli $f(0) = -2$."),
                (r"Podstaw $x = 1$, a potem $x = 2$.", r"$f(1) = 1$ oraz $f(2) = 4$."),
                (r"Porównaj trzy wyniki. O ile rosną?", r"Od $-2$ do $1$ i od $1$ do $4$ — za każdym razem o $3$, czyli o $a$."),
                (r"Narysuj układ współrzędnych i zaznacz punkty $(0, -2)$, $(1, 1)$, $(2, 4)$. Połącz je linijką.", "Jeśli punkty nie leżą na jednej prostej, sprawdź rachunki."),
            ),
            "sprawdzenia": [
                ("wartosc", {"a": 3, "b": -2, "x": 0}, "f(0) = -2"),
                ("wartosc", {"a": 3, "b": -2, "x": 1}, "f(1) = 1"),
                ("wartosc", {"a": 3, "b": -2, "x": 2}, "f(2) = 4"),
                ("punkt", {"a": 3, "b": -2, "x": 0}, "(0, -2)"),
                ("punkt", {"a": 3, "b": -2, "x": 1}, "(1, 1)"),
                ("punkt", {"a": 3, "b": -2, "x": 2}, "(2, 4)"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": r"""**Na rozgrzewkę.** Funkcja $y = x + 2$.

Przed $x$ nie ma żadnej liczby, czyli stoi tam „niewidzialna” jedynka: $a = 1$. Wyraz wolny to $b = 2$.

Dla $x = 3$: $3 + 2$, czyli $f(3) = 5$.""",
            "sprawdzenia": [("wartosc", {"a": 1, "b": 2, "x": 3}, "f(3) = 5")],
        },
        {
            "typ": "przyklad",
            "poziom": 2,
            "tresc": r"""Funkcja $y = -3x + 4$. Odczytujemy: $a = -3$, $b = 4$.

- Dla $x = 2$: $-3 \cdot 2 + 4 = -6 + 4$, czyli $f(2) = -2$.
- Dla $x = -1$: $-3 \cdot (-1) + 4 = 3 + 4$, czyli $f(-1) = 7$.

Ujemne $a$ oznacza, że gdy $x$ rośnie, wartości funkcji maleją.""",
            "sprawdzenia": [
                ("wartosc", {"a": -3, "b": 4, "x": 2}, "f(2) = -2"),
                ("wartosc", {"a": -3, "b": 4, "x": -1}, "f(-1) = 7"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": r"""**Zadanie z treścią.** Taksówka: opłata początkowa 8 zł i 3,50 zł za każdy kilometr.

Koszt przejazdu $x$ kilometrów opisuje funkcja $y = \tfrac{7}{2}x + 8$. Opłata za kilometr to $a = \tfrac{7}{2}$, opłata początkowa to $b = 8$.

- Ile kosztuje 6 km? $\tfrac{7}{2} \cdot 6 + 8 = 21 + 8$, czyli 29 zł.
- Ile kilometrów przejedziemy za 43 zł? Rozwiązujemy $\tfrac{7}{2}x + 8 = 43$, czyli $\tfrac{7}{2}x = 35$, stąd 10 km.""",
            "sprawdzenia": [
                ("wzor", {"a": F(7, 2), "b": 8}, r"y = \tfrac{7}{2}x + 8"),
                ("koszt", {"a": F(7, 2), "b": 8, "x": 6}, "29 zł"),
                ("argument", {"a": F(7, 2), "b": 8, "y": 43}, "10 km"),
            ],
        },
        {
            "typ": "uwaga",
            "tresc": r"""**Typowy błąd: mylenie $a$ z $b$, gdy wzór jest zapisany w innej kolejności.**

Funkcja $y = 5 - 2x$. Uczeń czyta od lewej: „$a = 5$, $b = -2$” — **źle**.

$a$ to liczba stojąca **przy $x$**, a nie pierwsza liczba we wzorze. Uporządkuj zapis: $y = -2x + 5$. Teraz widać, że $a = -2$, $b = 5$.""",
            "sprawdzenia": [("wzor", {"a": -2, "b": 5}, "y = -2x + 5")],
        },
        {
            "typ": "zadanie",
            "tresc": r"Dana jest funkcja $f(x) = -2x + 6$. Podaj $a$ i $b$, a następnie oblicz $f(4)$ oraz $f(-1)$.",
            "odpowiedz": r"$a = -2$, $b = 6$, $f(4) = -2$, $f(-1) = 8$",
            "rozwiazanie": r"""Liczba przy $x$ to $a = -2$, wyraz wolny to $b = 6$.

$-2 \cdot 4 + 6 = -8 + 6$, czyli $f(4) = -2$.

$-2 \cdot (-1) + 6 = 2 + 6$, czyli $f(-1) = 8$.""",
            "sprawdzenia": [
                ("wartosc", {"a": -2, "b": 6, "x": 4}, "f(4) = -2"),
                ("wartosc", {"a": -2, "b": 6, "x": -1}, "f(-1) = 8"),
            ],
        },
        {
            "typ": "quiz",
            "tresc": "Sprawdź, czy rozróżniasz $a$ i $b$.",
            **_quiz(
                (r"W funkcji $y = 4x - 7$ współczynnik kierunkowy $a$ jest równy:", ["$4$", "$-7$", "$7$"], 0,
                 {"typ": "a", "a": 4, "b": -7}),
                (r"Wyraz wolny funkcji $y = 5 - 3x$ to:", ["$-3$", "$5$", "$3$"], 1,
                 {"typ": "b", "a": -3, "b": 5}),
                (r"Dla funkcji $f(x) = 2x - 5$ wartość $f(3)$ wynosi:", ["$11$", "$-1$", "$1$"], 2,
                 {"typ": "wartosc", "a": 2, "b": -5, "x": 3}),
                (r"W jakim punkcie wykres funkcji $y = -x + 4$ przecina oś $OY$?", ["$(4, 0)$", "$(0, 4)$", "$(0, -1)$"], 1,
                 {"typ": "oy", "a": -1, "b": 4}),
                (r"Gdy $x$ wzrośnie o $1$, wartość funkcji $y = -3x + 2$:", ["zmaleje o $3$", "wzrośnie o $3$", "wzrośnie o $2$"], 0,
                 {"typ": "zmiana", "a": -3, "b": 2}),
            ),
        },
    ],
}

# ===========================================================================
# Topic 2: graph and monotonicity
# ===========================================================================

WYKRES_2A = Wykres(
    plik="wykres-dwa-punkty.svg",
    tytul="y = 2x − 1: wystarczą dwa punkty",
    proste=(Prosta(2, -1),),
    punkty=(
        Punkt(0, -1, "przeciecie_oy", "(0, −1)", dx=10, dy=18),
        Punkt(2, 3, "punkt", "(2, 3)"),
    ),
    x_min=-3,
    x_max=4,
    y_min=-4,
    y_max=6,
)

WYKRES_2B = Wykres(
    plik="monotonicznosc.svg",
    tytul="Znak a decyduje o monotoniczności",
    proste=(Prosta(1, 1), Prosta(-1, 1), Prosta(0, 1)),
    punkty=(Punkt(0, 1, "przeciecie_oy", "(0, 1)", dx=10, dy=-12),),
    x_min=-4,
    x_max=4,
    y_min=-3,
    y_max=5,
    etykiety_prostych=(
        "a > 0:  y = x + 1  (rosnąca)",
        "a < 0:  y = −x + 1  (malejąca)",
        "a = 0:  y = 1  (stała)",
    ),
)

TEMAT_2 = {
    "tytul": "Wykres funkcji liniowej i monotoniczność",
    "wykresy": (WYKRES_2A, WYKRES_2B),
    "bloki": [
        {
            "typ": "teoria",
            "tresc": r"""## Ściąga

$$
y = ax + b
$$

Wykresem funkcji liniowej jest **prosta**. Żeby ją narysować, wystarczą **dwa punkty**.

O tym, czy funkcja rośnie, czy maleje, decyduje **znak $a$**:

- $a > 0$ — funkcja **rosnąca** (prosta idzie w górę, gdy patrzysz od lewej do prawej),
- $a < 0$ — funkcja **malejąca** (prosta idzie w dół),
- $a = 0$ — funkcja **stała**: $y = b$, prosta pozioma.

**Przykład:** $y = 2x - 1$. Liczymy dwa punkty: dla $x = 0$ mamy $f(0) = -1$, dla $x = 2$ mamy $f(2) = 3$. Zaznaczamy $(0, -1)$ i $(2, 3)$, prowadzimy przez nie prostą. Ponieważ $a = 2 > 0$, funkcja jest rosnąca.""",
            "sprawdzenia": [
                ("wartosc", {"a": 2, "b": -1, "x": 0}, "f(0) = -1"),
                ("wartosc", {"a": 2, "b": -1, "x": 2}, "f(2) = 3"),
                ("punkt", {"a": 2, "b": -1, "x": 0}, "(0, -1)"),
                ("punkt", {"a": 2, "b": -1, "x": 2}, "(2, 3)"),
                ("monotonicznosc", {"a": 2}, "rosnąca"),
            ],
        },
        {
            "typ": "diagram",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_2A.plik),
            "tresc": r"Wykres funkcji $y = 2x - 1$. Dwa punkty: $(0, -1)$ oraz $(2, 3)$ — i linijka. Prosta wspina się w prawo, bo $a = 2$ jest dodatnie.",
            "sprawdzenia": [
                ("punkt", {"a": 2, "b": -1, "x": 0}, "(0, -1)"),
                ("punkt", {"a": 2, "b": -1, "x": 2}, "(2, 3)"),
            ],
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_2B.plik),
            "tresc": r"Trzy proste przez ten sam punkt $(0, 1)$: przy $a > 0$ prosta idzie w górę, przy $a < 0$ w dół, a przy $a = 0$ jest pozioma.",
            "sprawdzenia": [
                ("oy", {"a": 1, "b": 1}, "(0, 1)"),
                ("oy", {"a": -1, "b": 1}, "(0, 1)"),
                ("oy", {"a": 0, "b": 1}, "(0, 1)"),
            ],
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Wykres funkcji liniowej to zawsze prosta. A do narysowania prostej wystarczą dwa punkty. "
                "Wybierasz dwie wartości iksa, liczysz dla nich igrek, zaznaczasz dwa punkty i prowadzisz przez nie linię. "
                "Teraz monotoniczność, czyli pytanie: czy funkcja rośnie, czy maleje. Patrzysz tylko na a, na liczbę przy iksie. "
                "Jeśli a jest dodatnie, funkcja jest rosnąca. Idąc w prawo, wchodzisz pod górę. "
                "Jeśli a jest ujemne, funkcja jest malejąca. Idąc w prawo, schodzisz w dół. "
                "Jeśli a jest równe zero, funkcja jest stała. Wykres jest poziomy, jak podłoga. "
                "Przykład: igrek równa się dwa iks minus jeden. Przy iksie stoi dwa, liczba dodatnia, więc funkcja jest rosnąca. "
                "Uwaga na pułapkę: wyraz wolny b nie ma tu nic do powiedzenia. O monotoniczności decyduje wyłącznie znak a. "
                "Powtórz: plus rośnie, minus maleje, zero stoi w miejscu."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": r"Narysujesz wykres funkcji $y = -2x + 4$. Przygotuj kartkę w kratkę, linijkę i ołówek.",
            "dane": _kroki(
                (r"Zrób tabelkę z trzema kolumnami: $x = 0$, $x = 1$, $x = 2$.", None),
                (r"Oblicz wartości funkcji i wpisz je do tabelki.", r"$f(0) = 4$, $f(1) = 2$, $f(2) = 0$."),
                (r"Narysuj układ współrzędnych i zaznacz punkty $(0, 4)$, $(1, 2)$, $(2, 0)$.", "Pierwsza liczba to x (w poziomie), druga to y (w pionie)."),
                (r"Przyłóż linijkę i połącz punkty. Przedłuż linię w obie strony.", "Wszystkie trzy punkty muszą leżeć na jednej prostej."),
                (r"Przesuń palcem po prostej od lewej do prawej. Idziesz w górę czy w dół? Nazwij monotoniczność.", r"W dół — funkcja jest malejąca, bo $a = -2 < 0$."),
            ),
            "sprawdzenia": [
                ("wartosc", {"a": -2, "b": 4, "x": 0}, "f(0) = 4"),
                ("wartosc", {"a": -2, "b": 4, "x": 1}, "f(1) = 2"),
                ("wartosc", {"a": -2, "b": 4, "x": 2}, "f(2) = 0"),
                ("punkt", {"a": -2, "b": 4, "x": 0}, "(0, 4)"),
                ("punkt", {"a": -2, "b": 4, "x": 1}, "(1, 2)"),
                ("punkt", {"a": -2, "b": 4, "x": 2}, "(2, 0)"),
                ("monotonicznosc", {"a": -2}, "malejąca"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": r"""**Na rozgrzewkę.** Funkcja $y = x - 1$.

Dwa punkty: $f(0) = -1$ oraz $f(1) = 0$, czyli $(0, -1)$ i $(1, 0)$. Łączymy je prostą.

Przy $x$ stoi $a = 1$, liczba dodatnia — funkcja jest rosnąca.""",
            "sprawdzenia": [
                ("wartosc", {"a": 1, "b": -1, "x": 0}, "f(0) = -1"),
                ("wartosc", {"a": 1, "b": -1, "x": 1}, "f(1) = 0"),
                ("punkt", {"a": 1, "b": -1, "x": 1}, "(1, 0)"),
                ("monotonicznosc", {"a": 1}, "rosnąca"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 2,
            "tresc": r"""Funkcja $y = -2x + 3$.

Punkty do wykresu: $f(0) = 3$ oraz $f(2) = -1$, czyli $(0, 3)$ i $(2, -1)$.

$a = -2 < 0$, więc funkcja jest malejąca: przesuwając się o $1$ w prawo, schodzimy o $2$ w dół.""",
            "sprawdzenia": [
                ("wartosc", {"a": -2, "b": 3, "x": 0}, "f(0) = 3"),
                ("wartosc", {"a": -2, "b": 3, "x": 2}, "f(2) = -1"),
                ("punkt", {"a": -2, "b": 3, "x": 2}, "(2, -1)"),
                ("monotonicznosc", {"a": -2}, "malejąca"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": r"""**Z parametrem.** Dla jakich wartości $m$ funkcja $f(x) = (3 - 2m)x + 1$ jest malejąca?

Współczynnik kierunkowy to całe wyrażenie w nawiasie: $a = 3 - 2m$. Funkcja jest malejąca, gdy $a < 0$:

$$
3 - 2m < 0
$$
$$
-2m < -3
$$

Dzielimy przez liczbę ujemną, więc **odwracamy znak nierówności**:

$$
m > \tfrac{3}{2}
$$

Podobnie: funkcja jest stała dla $m = \tfrac{3}{2}$, a rosnąca dla $m < \tfrac{3}{2}$.""",
            "sprawdzenia": [("prog", {"p": -2, "q": 3}, r"\tfrac{3}{2}")],
        },
        {
            "typ": "uwaga",
            "tresc": r"""**Typowy błąd: ocenianie monotoniczności po pierwszej liczbie we wzorze.**

Funkcja $y = 3 - 4x$. Uczeń widzi dodatnią trójkę i pisze „rosnąca” — **źle**.

Trójka to wyraz wolny $b$. Przy $x$ stoi $a = -4$, liczba ujemna, więc funkcja jest **malejąca**. Sprawdzenie: $f(0) = 3$, $f(1) = -1$ — wartości spadają.""",
            "sprawdzenia": [
                ("wartosc", {"a": -4, "b": 3, "x": 0}, "f(0) = 3"),
                ("wartosc", {"a": -4, "b": 3, "x": 1}, "f(1) = -1"),
                ("monotonicznosc", {"a": -4}, "malejąca"),
            ],
        },
        {
            "typ": "zadanie",
            "tresc": r"Dana jest funkcja $f(x) = 3x - 6$. Wyznacz punkty jej wykresu dla $x = 0$ i $x = 2$ oraz określ monotoniczność.",
            "odpowiedz": r"Punkty $(0, -6)$ i $(2, 0)$; funkcja rosnąca.",
            "rozwiazanie": r"""$3 \cdot 0 - 6$, czyli $f(0) = -6$ — punkt $(0, -6)$.

$3 \cdot 2 - 6$, czyli $f(2) = 0$ — punkt $(2, 0)$.

$a = 3 > 0$, więc funkcja jest rosnąca.""",
            "sprawdzenia": [
                ("wartosc", {"a": 3, "b": -6, "x": 0}, "f(0) = -6"),
                ("wartosc", {"a": 3, "b": -6, "x": 2}, "f(2) = 0"),
                ("punkt", {"a": 3, "b": -6, "x": 0}, "(0, -6)"),
                ("punkt", {"a": 3, "b": -6, "x": 2}, "(2, 0)"),
                ("monotonicznosc", {"a": 3}, "rosnąca"),
            ],
        },
        {
            "typ": "quiz",
            "tresc": "Wykres i monotoniczność — sprawdź się.",
            **_quiz(
                (r"Funkcja $y = -5x + 2$ jest:", ["rosnąca", "malejąca", "stała"], 1,
                 {"typ": "monotonicznosc", "a": -5}),
                (r"Funkcja $y = 7 - 2x$ jest:", ["rosnąca, bo $7 > 0$", "stała", "malejąca, bo $a = -2$"], 2,
                 {"typ": "monotonicznosc", "a": -2}),
                (r"Wykresem funkcji $y = 4$ jest:", ["prosta pionowa", "prosta pozioma, równoległa do osi $OX$", "prosta przechodząca przez punkt $(0, 0)$"], 1,
                 {"typ": "pozioma", "a": 0, "b": 4}),
                (r"Który punkt należy do wykresu funkcji $y = 3x - 2$?", ["$(2, 8)$", "$(4, 2)$", "$(2, 4)$"], 2,
                 {"typ": "punkt_na_wykresie", "a": 3, "b": -2, "punkty": [(2, 8), (4, 2), (2, 4)]}),
                (r"Funkcja $f(x) = (m - 3)x + 1$ jest rosnąca dla:", ["$m > 3$", "$m < 3$", "$m > -3$"], 0,
                 {"typ": "parametr_rosnaca", "p": 1, "q": -3}),
            ),
        },
    ],
}

# ===========================================================================
# Topic 3: zero of the function and intercepts
# ===========================================================================

WYKRES_3A = Wykres(
    plik="miejsce-zerowe.svg",
    tytul="y = 2x − 4: miejsce zerowe",
    proste=(Prosta(2, -4),),
    punkty=(
        Punkt(2, 0, "miejsce_zerowe", "(2, 0)", dx=14, dy=-6),
        Punkt(0, -4, "przeciecie_oy", "(0, −4)", dx=10, dy=5),
    ),
    x_min=-2,
    x_max=6,
    y_min=-5,
    y_max=4,
)

WYKRES_3B = Wykres(
    plik="miejsce-zerowe-ulamek.svg",
    tytul="y = −2x + 3: miejsce zerowe 3/2",
    proste=(Prosta(-2, 3),),
    punkty=(
        Punkt(F(3, 2), 0, "miejsce_zerowe", "(3/2, 0)", dx=10, dy=-10),
        Punkt(0, 3, "przeciecie_oy", "(0, 3)", dx=10, dy=-8),
    ),
    x_min=-2,
    x_max=4,
    y_min=-3,
    y_max=5,
)

TEMAT_3 = {
    "tytul": "Miejsce zerowe i punkty przecięcia z osiami",
    "wykresy": (WYKRES_3A, WYKRES_3B),
    "bloki": [
        {
            "typ": "teoria",
            "tresc": r"""## Ściąga

**Miejsce zerowe** to taki $x$, dla którego wartość funkcji jest równa $0$. Rozwiązujemy równanie $ax + b = 0$ i dostajemy (dla $a \neq 0$):

$$
x_0 = -\frac{b}{a}
$$

Punkty przecięcia wykresu z osiami:

- z osią $OX$: $(x_0, 0)$ — tu „mieszka” miejsce zerowe,
- z osią $OY$: $(0, b)$.

**Przykład:** $y = 2x - 4$.

$2x - 4 = 0$, więc $2x = 4$, czyli $x_0 = 2$. Wykres przecina oś $OX$ w punkcie $(2, 0)$, a oś $OY$ w punkcie $(0, -4)$.""",
            "sprawdzenia": [
                ("zero", {"a": 2, "b": -4}, "x_0 = 2"),
                ("ox", {"a": 2, "b": -4}, "(2, 0)"),
                ("oy", {"a": 2, "b": -4}, "(0, -4)"),
            ],
        },
        {
            "typ": "diagram",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_3A.plik),
            "tresc": r"Wykres funkcji $y = 2x - 4$. Miejsce zerowe widać na wykresie: to punkt $(2, 0)$, w którym prosta przecina oś $OX$. Oś $OY$ prosta przecina w punkcie $(0, -4)$ — to wyraz wolny $b$.",
            "sprawdzenia": [
                ("ox", {"a": 2, "b": -4}, "(2, 0)"),
                ("oy", {"a": 2, "b": -4}, "(0, -4)"),
            ],
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_3B.plik),
            "tresc": r"Dla $y = -2x + 3$ miejsce zerowe nie jest liczbą całkowitą: $x_0 = \tfrac{3}{2}$. Prosta przecina oś $OX$ dokładnie w połowie między $1$ a $2$, w punkcie $(\tfrac{3}{2}, 0)$, a oś $OY$ w punkcie $(0, 3)$.",
            "sprawdzenia": [
                ("zero", {"a": -2, "b": 3}, r"x_0 = \tfrac{3}{2}"),
                ("ox", {"a": -2, "b": 3}, r"(\tfrac{3}{2}, 0)"),
                ("oy", {"a": -2, "b": 3}, "(0, 3)"),
            ],
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Miejsce zerowe to taki iks, dla którego funkcja daje zero. "
                "Na wykresie to punkt, w którym prosta przecina oś iks. "
                "Jak je znaleźć? Wzór funkcji przyrównujesz do zera i rozwiązujesz równanie. "
                "Przykład: igrek równa się dwa iks minus cztery. "
                "Piszemy: dwa iks minus cztery równa się zero. "
                "Przenosimy czwórkę na drugą stronę, ze zmienionym znakiem: dwa iks równa się cztery. "
                "Dzielimy obie strony przez dwa: iks równa się dwa. To jest miejsce zerowe. "
                "Jest też gotowy wzór: iks zero równa się minus b przez a. Pamiętaj o minusie na początku, to najczęstsze potknięcie. "
                "Drugi ważny punkt to przecięcie z osią igrek. Tu nie trzeba nic liczyć. Wystarczy odczytać b. "
                "W naszym przykładzie b to minus cztery, więc wykres przecina oś igrek na wysokości minus cztery. "
                "Powtórz: oś iks, czyli miejsce zerowe. Oś igrek, czyli b."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": r"Znajdziesz miejsce zerowe funkcji $y = 3x + 6$ i sprawdzisz je na dwa sposoby: rachunkiem i na rysunku.",
            "dane": _kroki(
                (r"Zapisz równanie $3x + 6 = 0$.", "Miejsce zerowe to x, dla którego y jest równe zero."),
                (r"Przenieś $6$ na prawą stronę. Pamiętaj o zmianie znaku.", r"$3x = -6$"),
                (r"Podziel obie strony przez $3$.", r"$x_0 = -2$"),
                (r"Sprawdź: podstaw wynik do wzoru funkcji.", r"$3 \cdot (-2) + 6 = 0$, czyli $f(-2) = 0$. Zgadza się."),
                (r"Odczytaj punkt przecięcia z osią $OY$.", r"To $b$: punkt $(0, 6)$."),
                (r"Zaznacz na kartce punkty $(-2, 0)$ i $(0, 6)$ i połącz je prostą.", "Prosta powinna przecinać oś OX dokładnie w miejscu zerowym."),
            ),
            "sprawdzenia": [
                ("zero", {"a": 3, "b": 6}, "x_0 = -2"),
                ("wartosc", {"a": 3, "b": 6, "x": -2}, "f(-2) = 0"),
                ("ox", {"a": 3, "b": 6}, "(-2, 0)"),
                ("oy", {"a": 3, "b": 6}, "(0, 6)"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": r"""**Na rozgrzewkę.** Funkcja $y = x - 3$.

Pytamy: dla jakiego $x$ wynik jest zerem? $x - 3 = 0$, więc $x_0 = 3$.

Punkty przecięcia z osiami: $(3, 0)$ na osi $OX$ oraz $(0, -3)$ na osi $OY$.""",
            "sprawdzenia": [
                ("zero", {"a": 1, "b": -3}, "x_0 = 3"),
                ("ox", {"a": 1, "b": -3}, "(3, 0)"),
                ("oy", {"a": 1, "b": -3}, "(0, -3)"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 2,
            "tresc": r"""Funkcja $y = -4x + 8$.

$-4x + 8 = 0$, więc $-4x = -8$. Dzielimy przez $-4$ i dostajemy $x_0 = 2$.

Punkty przecięcia z osiami: $(2, 0)$ oraz $(0, 8)$.""",
            "sprawdzenia": [
                ("zero", {"a": -4, "b": 8}, "x_0 = 2"),
                ("ox", {"a": -4, "b": 8}, "(2, 0)"),
                ("oy", {"a": -4, "b": 8}, "(0, 8)"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": r"""**Dla chętnych: ułamek i pole trójkąta.** Funkcja $y = -\tfrac{3}{4}x + 6$.

Miejsce zerowe: $-\tfrac{3}{4}x + 6 = 0$, więc $\tfrac{3}{4}x = 6$. Mnożymy obie strony przez $\tfrac{4}{3}$ i dostajemy $x_0 = 8$.

Wykres przecina osie w punktach $(8, 0)$ i $(0, 6)$. Razem z początkiem układu tworzą one trójkąt prostokątny o przyprostokątnych $8$ i $6$.

Jego pole: $P = \tfrac{1}{2} \cdot 8 \cdot 6$, czyli $P = 24$.""",
            "sprawdzenia": [
                ("zero", {"a": F(-3, 4), "b": 6}, "x_0 = 8"),
                ("ox", {"a": F(-3, 4), "b": 6}, "(8, 0)"),
                ("oy", {"a": F(-3, 4), "b": 6}, "(0, 6)"),
                ("pole", {"a": F(-3, 4), "b": 6}, "P = 24"),
            ],
        },
        {
            "typ": "uwaga",
            "tresc": r"""**Typowy błąd: zgubiony minus we wzorze $x_0 = -\tfrac{b}{a}$.**

Funkcja $y = 2x + 6$. Uczeń liczy: „$6 : 2 = 3$, więc miejsce zerowe to $3$” — **źle**.

Poprawnie: $2x + 6 = 0$, więc $2x = -6$, czyli $x_0 = -3$.

Zawsze sprawdzaj przez podstawienie: $f(3) = 12$ (to nie zero!), a $f(-3) = 0$ — zgadza się.

Drugi częsty błąd: punkt $(0, 6)$ to przecięcie z osią $OY$, a **nie** miejsce zerowe.""",
            "sprawdzenia": [
                ("zero", {"a": 2, "b": 6}, "x_0 = -3"),
                ("wartosc", {"a": 2, "b": 6, "x": 3}, "f(3) = 12"),
                ("wartosc", {"a": 2, "b": 6, "x": -3}, "f(-3) = 0"),
                ("oy", {"a": 2, "b": 6}, "(0, 6)"),
            ],
        },
        {
            "typ": "zadanie",
            "tresc": r"Wyznacz miejsce zerowe funkcji $f(x) = -2x + 5$ oraz punkty przecięcia jej wykresu z osiami układu współrzędnych.",
            "odpowiedz": r"$x_0 = \tfrac{5}{2}$; punkty $(\tfrac{5}{2}, 0)$ i $(0, 5)$",
            "rozwiazanie": r"""$-2x + 5 = 0$, więc $-2x = -5$. Dzielimy przez $-2$: $x_0 = \tfrac{5}{2}$.

Przecięcie z osią $OX$: $(\tfrac{5}{2}, 0)$.

Przecięcie z osią $OY$ odczytujemy z wyrazu wolnego: $(0, 5)$.""",
            "sprawdzenia": [
                ("zero", {"a": -2, "b": 5}, r"x_0 = \tfrac{5}{2}"),
                ("ox", {"a": -2, "b": 5}, r"(\tfrac{5}{2}, 0)"),
                ("oy", {"a": -2, "b": 5}, "(0, 5)"),
            ],
        },
        {
            "typ": "quiz",
            "tresc": "Miejsce zerowe i przecięcia z osiami — sprawdź się.",
            **_quiz(
                (r"Miejsce zerowe funkcji $y = 2x - 8$ to:", ["$-4$", "$4$", "$-8$"], 1,
                 {"typ": "zero", "a": 2, "b": -8}),
                (r"Miejsce zerowe funkcji $y = 3x + 9$ to:", ["$3$", "$9$", "$-3$"], 2,
                 {"typ": "zero", "a": 3, "b": 9}),
                (r"Wykres funkcji $y = -x + 5$ przecina oś $OY$ w punkcie:", ["$(0, 5)$", "$(5, 0)$", "$(0, -5)$"], 0,
                 {"typ": "oy", "a": -1, "b": 5}),
                (r"Miejsce zerowe funkcji $y = 4x - 6$ to:", [r"$-\tfrac{3}{2}$", r"$\tfrac{2}{3}$", r"$\tfrac{3}{2}$"], 2,
                 {"typ": "zero", "a": 4, "b": -6}),
                (r"Funkcja $y = 5$:", ["ma miejsce zerowe $x = 5$", "nie ma miejsc zerowych", "ma miejsce zerowe $x = 0$"], 1,
                 {"typ": "brak_zera", "a": 0, "b": 5}),
            ),
        },
    ],
}

# ===========================================================================
# Topic 4: formula of a line through two points
# ===========================================================================

WYKRES_4A = Wykres(
    plik="dwa-punkty-rosnaca.svg",
    tytul="A = (1, 3), B = (3, 7): 2 w prawo, 4 w górę",
    proste=(Prosta(2, 1),),
    punkty=(
        Punkt(1, 3, "punkt", "A = (1, 3)", dx=-10, dy=-8),
        Punkt(3, 7, "punkt", "B = (3, 7)", dx=-10, dy=-8),
    ),
    schodek=Schodek(1, 3, 3, 7),
    x_min=-2,
    x_max=5,
    y_min=-2,
    y_max=8,
)

WYKRES_4B = Wykres(
    plik="dwa-punkty-malejaca.svg",
    tytul="(−1, 4) i (2, −2): 3 w prawo, 6 w dół",
    proste=(Prosta(-2, 2),),
    punkty=(
        Punkt(-1, 4, "punkt", "(−1, 4)", dx=-10, dy=-8),
        Punkt(2, -2, "punkt", "(2, −2)", dx=12, dy=5),
    ),
    schodek=Schodek(-1, 4, 2, -2),
    x_min=-3,
    x_max=4,
    y_min=-4,
    y_max=6,
)

TEMAT_4 = {
    "tytul": "Wzór funkcji przechodzącej przez dwa punkty",
    "wykresy": (WYKRES_4A, WYKRES_4B),
    "bloki": [
        {
            "typ": "teoria",
            "tresc": r"""## Ściąga

Mamy dwa punkty $A = (x_1, y_1)$ i $B = (x_2, y_2)$, przy czym $x_1 \neq x_2$. Szukamy wzoru $y = ax + b$.

**Krok 1.** Współczynnik kierunkowy — „o ile w górę” podzielone przez „o ile w prawo”:

$$
a = \frac{y_2 - y_1}{x_2 - x_1}
$$

**Krok 2.** Wyraz wolny — podstawiamy jeden z punktów do wzoru:

$$
b = y_1 - a \cdot x_1
$$

**Przykład:** $A = (1, 3)$, $B = (3, 7)$.

Liczymy $\dfrac{7 - 3}{3 - 1} = \dfrac{4}{2}$, czyli $a = 2$. Następnie $3 - 2 \cdot 1$, czyli $b = 1$.

Wzór: $y = 2x + 1$. Sprawdzenie drugim punktem: $2 \cdot 3 + 1 = 7$ — zgadza się.""",
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (1, 3), "p2": (3, 7)}, "a = 2"),
                ("b_z_punktow", {"p1": (1, 3), "p2": (3, 7)}, "b = 1"),
                ("wzor_z_punktow", {"p1": (1, 3), "p2": (3, 7)}, "y = 2x + 1"),
            ],
        },
        {
            "typ": "diagram",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_4A.plik),
            "tresc": r"Od $A = (1, 3)$ do $B = (3, 7)$ idziemy $2$ w prawo i $4$ w górę. Dzielimy: $4 : 2$, czyli $a = 2$. Prosta przecina oś $OY$ w punkcie $(0, 1)$, czyli $b = 1$.",
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (1, 3), "p2": (3, 7)}, "a = 2"),
                ("b_z_punktow", {"p1": (1, 3), "p2": (3, 7)}, "b = 1"),
                ("oy", {"a": 2, "b": 1}, "(0, 1)"),
            ],
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": url_wykresu(WYKRES_4B.plik),
            "tresc": r"Od $(-1, 4)$ do $(2, -2)$ idziemy $3$ w prawo i $6$ **w dół**, dlatego $a = -2$. Prosta przecina oś $OY$ w punkcie $(0, 2)$, więc wzór to $y = -2x + 2$.",
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (-1, 4), "p2": (2, -2)}, "a = -2"),
                ("oy", {"a": -2, "b": 2}, "(0, 2)"),
                ("wzor_z_punktow", {"p1": (-1, 4), "p2": (2, -2)}, "y = -2x + 2"),
            ],
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Masz dwa punkty i chcesz znaleźć wzór prostej, która przez nie przechodzi. Robimy to w dwóch krokach. "
                "Krok pierwszy: liczymy a. Odejmujemy igreki i dzielimy przez różnicę iksów. "
                "Mówiąc po ludzku: o ile poszliśmy w górę, podzielone przez to, o ile poszliśmy w prawo. "
                "Przykład. Punkt pierwszy: iks jeden, igrek trzy. Punkt drugi: iks trzy, igrek siedem. "
                "Różnica igreków: siedem odjąć trzy, czyli cztery. Różnica iksów: trzy odjąć jeden, czyli dwa. "
                "Cztery podzielić przez dwa to dwa. Mamy a równe dwa. "
                "Krok drugi: liczymy b. Bierzemy pierwszy punkt i od jego igreka odejmujemy a razy iks. "
                "Trzy odjąć dwa razy jeden daje jeden. Mamy b równe jeden. "
                "Wzór: igrek równa się dwa iks plus jeden. "
                "Na koniec zawsze sprawdź drugim punktem. Dwa razy trzy plus jeden to siedem. Zgadza się. "
                "Najważniejsza zasada: odejmuj w tej samej kolejności u góry i na dole ułamka."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": r"Wyznaczysz wzór prostej przechodzącej przez punkty $A = (2, 1)$ i $B = (4, 5)$. Licz na kartce, krok po kroku.",
            "dane": _kroki(
                (r"Zaznacz oba punkty w układzie współrzędnych i połącz je prostą.", None),
                (r"Policz po kratkach: o ile w prawo i o ile w górę trzeba przejść z $A$ do $B$?", r"$2$ w prawo i $4$ w górę."),
                (r"Podziel „w górę” przez „w prawo”.", r"$4 : 2$, czyli $a = 2$."),
                (r"Podstaw punkt $A$ do wzoru $y = 2x + b$ i wyznacz $b$.", r"$1 = 2 \cdot 2 + b$, stąd $b = -3$."),
                (r"Zapisz wzór i sprawdź go punktem $B$.", r"$y = 2x - 3$. Sprawdzenie: $2 \cdot 4 - 3 = 5$. Zgadza się."),
                (r"Zobacz na rysunku, gdzie prosta przecina oś $OY$.", r"W punkcie $(0, -3)$ — dokładnie tyle wyszło $b$."),
            ),
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (2, 1), "p2": (4, 5)}, "a = 2"),
                ("b_z_punktow", {"p1": (2, 1), "p2": (4, 5)}, "b = -3"),
                ("wzor_z_punktow", {"p1": (2, 1), "p2": (4, 5)}, "y = 2x - 3"),
                ("oy", {"a": 2, "b": -3}, "(0, -3)"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": r"""**Na rozgrzewkę.** Punkty $(0, 2)$ i $(1, 5)$.

Pierwszy punkt leży na osi $OY$, więc od razu widać, że $b = 2$.

Od pierwszego do drugiego punktu idziemy $1$ w prawo i $3$ w górę, czyli $a = 3$.

Wzór: $y = 3x + 2$.""",
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (0, 2), "p2": (1, 5)}, "a = 3"),
                ("b_z_punktow", {"p1": (0, 2), "p2": (1, 5)}, "b = 2"),
                ("wzor_z_punktow", {"p1": (0, 2), "p2": (1, 5)}, "y = 3x + 2"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 2,
            "tresc": r"""Punkty $A = (-2, 7)$ i $B = (1, 1)$.

Liczymy $\dfrac{1 - 7}{1 - (-2)} = \dfrac{-6}{3}$, czyli $a = -2$.

Podstawiamy punkt $A$: $7 - (-2) \cdot (-2) = 7 - 4$, czyli $b = 3$.

Wzór: $y = -2x + 3$. Sprawdzenie punktem $B$: $-2 \cdot 1 + 3 = 1$ — zgadza się.""",
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (-2, 7), "p2": (1, 1)}, "a = -2"),
                ("b_z_punktow", {"p1": (-2, 7), "p2": (1, 1)}, "b = 3"),
                ("wzor_z_punktow", {"p1": (-2, 7), "p2": (1, 1)}, "y = -2x + 3"),
            ],
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": r"""**Dla chętnych: wynik z ułamkami.** Punkty $A = (-1, 2)$ i $B = (3, 5)$.

Liczymy $\dfrac{5 - 2}{3 - (-1)}$, czyli $a = \tfrac{3}{4}$.

Podstawiamy punkt $A$: $2 - \tfrac{3}{4} \cdot (-1) = 2 + \tfrac{3}{4}$, czyli $b = \tfrac{11}{4}$.

Wzór: $y = \tfrac{3}{4}x + \tfrac{11}{4}$.

Sprawdzenie punktem $B$: $\tfrac{3}{4} \cdot 3 + \tfrac{11}{4} = \tfrac{9}{4} + \tfrac{11}{4} = \tfrac{20}{4} = 5$ — zgadza się.""",
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (-1, 2), "p2": (3, 5)}, r"a = \tfrac{3}{4}"),
                ("b_z_punktow", {"p1": (-1, 2), "p2": (3, 5)}, r"b = \tfrac{11}{4}"),
                ("wzor_z_punktow", {"p1": (-1, 2), "p2": (3, 5)}, r"y = \tfrac{3}{4}x + \tfrac{11}{4}"),
            ],
        },
        {
            "typ": "uwaga",
            "tresc": r"""**Typowy błąd: odejmowanie w różnej kolejności w liczniku i w mianowniku.**

Punkty $A = (1, 2)$ i $B = (4, 8)$.

Źle: $\dfrac{8 - 2}{1 - 4} = \dfrac{6}{-3} = -2$. U góry odjęto „$B$ minus $A$”, a na dole „$A$ minus $B$”.

Dobrze: $\dfrac{8 - 2}{4 - 1} = \dfrac{6}{3}$, czyli $a = 2$.

Kolejność punktów jest dowolna, ale musi być **taka sama** u góry i na dole: $\dfrac{2 - 8}{1 - 4} = \dfrac{-6}{-3}$ też daje $2$.""",
            "sprawdzenia": [("a_z_punktow", {"p1": (1, 2), "p2": (4, 8)}, "a = 2")],
        },
        {
            "typ": "zadanie",
            "tresc": r"Wyznacz wzór funkcji liniowej, której wykres przechodzi przez punkty $A = (-1, -5)$ i $B = (2, 4)$.",
            "odpowiedz": r"$y = 3x - 2$",
            "rozwiazanie": r"""$\dfrac{4 - (-5)}{2 - (-1)} = \dfrac{9}{3}$, czyli $a = 3$.

Podstawiamy punkt $A$: $-5 - 3 \cdot (-1) = -5 + 3$, czyli $b = -2$.

Wzór: $y = 3x - 2$. Sprawdzenie punktem $B$: $3 \cdot 2 - 2 = 4$ — zgadza się.""",
            "sprawdzenia": [
                ("a_z_punktow", {"p1": (-1, -5), "p2": (2, 4)}, "a = 3"),
                ("b_z_punktow", {"p1": (-1, -5), "p2": (2, 4)}, "b = -2"),
                ("wzor_z_punktow", {"p1": (-1, -5), "p2": (2, 4)}, "y = 3x - 2"),
            ],
        },
        {
            "typ": "quiz",
            "tresc": "Wzór prostej przez dwa punkty — sprawdź się.",
            **_quiz(
                (r"Współczynnik kierunkowy prostej przechodzącej przez punkty $A = (1, 2)$ i $B = (3, 8)$ jest równy:", [r"$\tfrac{1}{3}$", "$3$", "$-3$"], 1,
                 {"typ": "a_z_punktow", "p1": (1, 2), "p2": (3, 8)}),
                (r"Prosta przechodzi przez punkty $(0, -4)$ i $(2, 0)$. Jej wzór to:", ["$y = 2x - 4$", "$y = -4x + 2$", "$y = 2x + 4$"], 0,
                 {"typ": "wzor_z_punktow", "p1": (0, -4), "p2": (2, 0), "opcje_ab": [(2, -4), (-4, 2), (2, 4)]}),
                (r"Dla punktów $A = (2, 5)$ i $B = (4, 1)$ współczynnik $a$ jest równy:", ["$2$", r"$-\tfrac{1}{2}$", "$-2$"], 2,
                 {"typ": "a_z_punktow", "p1": (2, 5), "p2": (4, 1)}),
                (r"Prosta ma współczynnik $a = 3$ i przechodzi przez punkt $(2, 1)$. Wyraz wolny $b$ jest równy:", ["$7$", "$-5$", "$5$"], 1,
                 {"typ": "b_z_a_i_punktu", "a": 3, "p": (2, 1)}),
                (r"Wykres funkcji liniowej przechodzi przez punkty $(1, 1)$ i $(3, 5)$. Wzór tej funkcji to:", ["$y = 2x + 1$", r"$y = \tfrac{1}{2}x + \tfrac{1}{2}$", "$y = 2x - 1$"], 2,
                 {"typ": "wzor_z_punktow", "p1": (1, 1), "p2": (3, 5), "opcje_ab": [(2, 1), (F(1, 2), F(1, 2)), (2, -1)]}),
            ),
        },
    ],
}

KURS_MATEMATYKA = {
    "nazwa": NAZWA_KURSU_MATEMATYKA,
    "opis": "Kurs demonstracyjny (liceum, klasa 1): funkcja liniowa w wersji dla wzrokowca, słuchowca i kinestetyka.",
    "dzialy": [
        {"nazwa": "Podstawy", "tematy": [TEMAT_1, TEMAT_2]},
        {"nazwa": "Zastosowania", "tematy": [TEMAT_3, TEMAT_4]},
    ],
}

WSZYSTKIE_WYKRESY: tuple[Wykres, ...] = tuple(
    w for dzial in KURS_MATEMATYKA["dzialy"] for temat in dzial["tematy"] for w in temat["wykresy"]
)
