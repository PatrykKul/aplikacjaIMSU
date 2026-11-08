# ruff: noqa: E501  (lesson texts are content, not code; keeping sentences whole)
"""Content of the three demo courses. Files come from `assets/` (see `generate_assets.py`).

Each lesson has common text blocks and attachments marked with the forms they suit:
V (images, diagrams), A (text read aloud by the browser), K (worksheets to do) and mixed ones.
"""

from dataclasses import dataclass, field
from typing import Any


def _text(content: str, bold: bool = False) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": content}
    if bold:
        node["marks"] = [{"type": "bold"}]
    return node


def heading(content: str) -> dict[str, Any]:
    return {"type": "heading", "attrs": {"level": 2}, "content": [_text(content)]}


def paragraph(*parts: str | tuple[str, bool]) -> dict[str, Any]:
    """Plain strings; ("text", True) is bold."""
    nodes = [_text(*part) if isinstance(part, tuple) else _text(part) for part in parts]
    return {"type": "paragraph", "content": nodes}


def bullets(*items: str) -> dict[str, Any]:
    return {
        "type": "bulletList",
        "content": [{"type": "listItem", "content": [paragraph(item)]} for item in items],
    }


def doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


@dataclass(frozen=True)
class Text:
    id: str
    nodes: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class Image:
    id: str
    forms: tuple[str, ...]
    title: str
    file: str
    alt: str
    description: str = ""


@dataclass(frozen=True)
class Pdf:
    id: str
    forms: tuple[str, ...]
    title: str
    file: str
    description: str = ""


@dataclass(frozen=True)
class Speech:
    """Audio attachment read aloud by the browser (transcript)."""

    id: str
    forms: tuple[str, ...]
    title: str
    transcript: str
    description: str = ""


Block = Text | Image | Pdf | Speech


@dataclass(frozen=True)
class Lesson:
    title: str
    blocks: tuple[Block, ...]


@dataclass(frozen=True)
class Course:
    title: str
    description: str
    introduction: tuple[dict[str, Any], ...]
    lessons: tuple[Lesson, ...] = field(default_factory=tuple)


MATH = Course(
    title="Matematyka: funkcja liniowa",
    description="Wzór y = ax + b, wykres, nachylenie i miejsce zerowe – w trzech krótkich lekcjach.",
    introduction=(
        paragraph(
            "W tym kursie poznasz najprostszą funkcję w matematyce. ",
            "Każda lekcja ma materiały do oglądania, słuchania i do zrobienia samodzielnie – ",
            "zobaczysz te, które pasują do Twojego stylu uczenia się.",
        ),
    ),
    lessons=(
        Lesson(
            "Wzór i wykres funkcji liniowej",
            (
                Text(
                    "t1",
                    (
                        heading("Czym jest funkcja liniowa?"),
                        paragraph(
                            "Funkcja liniowa ma wzór ",
                            ("y = ax + b", True),
                            ", gdzie a i b to dowolne liczby. Jej wykresem zawsze jest prosta.",
                        ),
                        bullets(
                            "b (wyraz wolny) mówi, gdzie prosta przecina oś y,",
                            "a (współczynnik kierunkowy) mówi, jak prosta jest nachylona.",
                        ),
                    ),
                ),
                Image(
                    "v-wykres",
                    ("V",),
                    "Wykres y = 2x + 1",
                    "m1_wykres.png",
                    "Wykres prostej y = 2x + 1 z zaznaczonymi punktami (0, 1) i (1, 3)",
                    "Zobacz, jak z wzoru odczytać punkt startowy i nachylenie.",
                ),
                Image(
                    "v-schemat",
                    ("V",),
                    "Schemat: co oznaczają litery we wzorze",
                    "m1_schemat.png",
                    "Schemat wzoru y = a·x + b z opisem liter a, x i b",
                ),
                Speech(
                    "a-wyjasnienie",
                    ("A",),
                    "Posłuchaj: jak czytać wzór funkcji liniowej",
                    "Funkcja liniowa ma wzór y równa się a razy x plus b. "
                    "Spróbujmy na przykładzie: y równa się dwa x plus jeden. "
                    "Liczba b, czyli jeden, mówi, gdzie wykres przecina oś pionową: w punkcie zero, jeden. "
                    "Liczba a, czyli dwa, mówi, że gdy x rośnie o jeden, to y rośnie o dwa. "
                    "Zapamiętaj zdanie: b to start, a to krok. Start w jedynce, krok w górę o dwa.",
                    "Lektor przeczyta wyjaśnienie. Możesz słuchać kilka razy.",
                ),
                Pdf(
                    "k-karta",
                    ("K",),
                    "Karta ćwiczeń: narysuj wykres",
                    "m1_karta.pdf",
                    "Wydrukuj albo przepisz zadania do zeszytu i narysuj wykres samodzielnie.",
                ),
                Speech(
                    "ak-cwiczenie",
                    ("A", "K"),
                    "Ćwiczenie z lektorem: rysujemy krok po kroku",
                    "Weź kartkę w kratkę i ołówek. Narysuj dwie osie, poziomą x i pionową y. "
                    "Zaznacz punkt zero, jeden – to nasz start, bo b równa się jeden. "
                    "Teraz zrób krok: jedna kratka w prawo i dwie kratki w górę. Postaw drugi punkt. "
                    "Połącz oba punkty linijką i przedłuż prostą. Gotowe – to wykres y równa się dwa x plus jeden.",
                    "Słuchaj i od razu rysuj.",
                ),
            ),
        ),
        Lesson(
            "Współczynnik kierunkowy a",
            (
                Text(
                    "t1",
                    (
                        heading("Co robi liczba a?"),
                        paragraph(
                            "Liczba a decyduje, czy funkcja rośnie, czy maleje, i jak szybko.",
                        ),
                        bullets(
                            "a > 0 – prosta idzie w górę (funkcja rosnąca),",
                            "a < 0 – prosta idzie w dół (funkcja malejąca),",
                            "a = 0 – prosta jest pozioma (funkcja stała).",
                        ),
                    ),
                ),
                Image(
                    "v-nachylenie",
                    ("V",),
                    "Trzy proste o różnym a",
                    "m2_nachylenie.png",
                    "Wykresy y = 2x, y = 0,5x i y = −x w jednym układzie",
                ),
                Speech(
                    "a-wyjasnienie",
                    ("A",),
                    "Posłuchaj: rośnie czy maleje?",
                    "Wyobraź sobie, że idziesz po wykresie od lewej do prawej. "
                    "Jeśli a jest dodatnie, idziesz pod górkę – funkcja rośnie. "
                    "Im większe a, tym bardziej stroma górka. "
                    "Jeśli a jest ujemne, schodzisz z górki – funkcja maleje. "
                    "A gdy a równa się zero, idziesz po płaskim – funkcja jest stała.",
                ),
                Image(
                    "vk-tabela",
                    ("V", "K"),
                    "Tabela wartości – uzupełnij i narysuj",
                    "m2_tabela.png",
                    "Tabela wartości funkcji y = −x + 3 i cztery kroki rysowania wykresu",
                    "Przerysuj tabelę do zeszytu i zaznacz punkty w układzie.",
                ),
                Pdf("k-karta", ("K",), "Karta ćwiczeń: współczynnik a", "m2_karta.pdf"),
            ),
        ),
        Lesson(
            "Miejsce zerowe",
            (
                Text(
                    "t1",
                    (
                        heading("Gdzie wykres przecina oś x?"),
                        paragraph(
                            "Miejsce zerowe to taki x, dla którego y = 0. ",
                            "Liczymy je, przyrównując wzór do zera: ",
                            ("ax + b = 0, czyli x = −b / a", True),
                            ".",
                        ),
                    ),
                ),
                Image(
                    "v-wykres",
                    ("V",),
                    "Miejsce zerowe na wykresie",
                    "m3_miejsce_zerowe.png",
                    "Wykres y = 2x − 4 przecinający oś x w punkcie x = 2",
                ),
                Speech(
                    "a-wyjasnienie",
                    ("A",),
                    "Posłuchaj: liczymy miejsce zerowe",
                    "Miejsce zerowe to punkt, w którym wykres dotyka osi x. Wtedy y równa się zero. "
                    "Weźmy funkcję y równa się dwa x minus cztery. Wstawiamy zero zamiast y: "
                    "dwa x minus cztery równa się zero. Przenosimy czwórkę: dwa x równa się cztery. "
                    "Dzielimy przez dwa: x równa się dwa. Miejsce zerowe to dwa.",
                ),
                Pdf(
                    "vk-karta",
                    ("V", "K"),
                    "Karta ćwiczeń: miejsce zerowe",
                    "m3_karta.pdf",
                    "Policz na kartce i sprawdź na wykresie.",
                ),
            ),
        ),
    ),
)

ENGLISH = Course(
    title="Angielski: Present Perfect",
    description="Kiedy używać Present Perfect, jak zbudować zdanie i czym różni się od Past Simple.",
    introduction=(
        paragraph(
            "Present Perfect łączy przeszłość z teraźniejszością. ",
            "W dwóch lekcjach nauczysz się budować zdania i wybierać między Present Perfect a Past Simple.",
        ),
    ),
    lessons=(
        Lesson(
            "Budowa zdania w Present Perfect",
            (
                Text(
                    "t1",
                    (
                        heading("Have / has + trzecia forma"),
                        paragraph(
                            "Zdanie twierdzące: ",
                            ("osoba + have/has + V3", True),
                            ". Has używamy z he, she, it.",
                        ),
                        bullets(
                            "I have finished my homework.",
                            "She has visited Paris twice.",
                            "We haven't seen this film. – przeczenie: haven't / hasn't",
                            "Have you ever eaten sushi? – pytanie: Have / Has na początku",
                        ),
                    ),
                ),
                Image(
                    "v-budowa",
                    ("V",),
                    "Schemat budowy zdania",
                    "e1_budowa.png",
                    "Kolorowy schemat: osoba, have/has, trzecia forma czasownika i reszta zdania",
                ),
                Speech(
                    "a-wyjasnienie",
                    ("A",),
                    "Posłuchaj: jak zbudować zdanie",
                    "Zdanie w czasie Present Perfect budujemy z trzech części. "
                    "Najpierw osoba, potem słowo have, a przy on, ona, ono – has. "
                    "Na końcu trzecia forma czasownika, na przykład seen, finished albo been. "
                    "Przeczenie tworzymy przez dodanie not: have not, w skrócie haven't. "
                    "W pytaniu have albo has przechodzi na sam początek zdania.",
                ),
                Pdf(
                    "k-karta",
                    ("K",),
                    "Karta ćwiczeń: uzupełnij zdania",
                    "e1_karta.pdf",
                    "Uzupełnij luki, a potem napisz trzy własne zdania.",
                ),
                Speech(
                    "ak-powtorz",
                    ("A", "K"),
                    "Mów na głos: trzy zdania o sobie",
                    "Teraz Twoja kolej. Powiedz na głos trzy zdania o tym, co już dziś zrobiłeś albo zrobiłaś. "
                    "Zacznij od I have already. Na przykład: I have already eaten breakfast. "
                    "Potem powiedz jedno zdanie z never: I have never been to Japan. "
                    "Mówienie na głos pomaga zapamiętać budowę zdania.",
                ),
            ),
        ),
        Lesson(
            "Present Perfect czy Past Simple?",
            (
                Text(
                    "t1",
                    (
                        heading("Liczy się, czy wiemy kiedy"),
                        bullets(
                            "Past Simple: zakończone, z konkretnym czasem – I lost my keys yesterday.",
                            "Present Perfect: ważny skutek teraz, czas nieistotny – I have lost my keys.",
                        ),
                        paragraph(
                            "Słowa-podpowiedzi Present Perfect: ",
                            ("ever, never, already, yet, just", True),
                            ".",
                        ),
                    ),
                ),
                Image(
                    "v-os",
                    ("V",),
                    "Oś czasu: dwa czasy",
                    "e2_os_czasu.png",
                    "Oś czasu: Past Simple jako punkt w przeszłości, Present Perfect jako łuk do teraz",
                ),
                Speech(
                    "a-wyjasnienie",
                    ("A",),
                    "Posłuchaj: jak wybrać czas",
                    "Zadaj sobie jedno pytanie: czy mówię, kiedy to się stało? "
                    "Jeśli tak, na przykład wczoraj, w zeszłym tygodniu albo w dwa tysiące dwudziestym roku, "
                    "używasz Past Simple. Jeśli czas nie jest ważny, a liczy się skutek teraz, "
                    "używasz Present Perfect. Zgubiłem klucze i nie mogę wejść do domu – to Present Perfect.",
                ),
                Pdf("k-karta", ("K",), "Karta ćwiczeń: wybierz czas", "e2_karta.pdf"),
            ),
        ),
    ),
)

PYTHON = Course(
    title="Programowanie: pętle w Pythonie",
    description="Pętle for i while: jak działają, kiedy ich używać i jak nie wpaść w pętlę bez końca.",
    introduction=(
        paragraph(
            "Pętla pozwala powtórzyć kod wiele razy bez przepisywania go. ",
            "W kursie poznasz dwie pętle Pythona: for i while.",
        ),
    ),
    lessons=(
        Lesson(
            "Pętla for",
            (
                Text(
                    "t1",
                    (
                        heading("Powtórz dla każdego elementu"),
                        paragraph(
                            "Pętla ",
                            ("for", True),
                            " wykonuje ciało pętli dla każdego elementu: liczby z range(), "
                            "litery w napisie albo elementu listy.",
                        ),
                        bullets(
                            "range(1, 6) daje liczby 1, 2, 3, 4, 5 (bez 6!),",
                            "ciało pętli musi mieć wcięcie (4 spacje),",
                            "zmienna i w każdym obrocie ma kolejną wartość.",
                        ),
                    ),
                ),
                Image(
                    "v-schemat",
                    ("V",),
                    "Schemat blokowy pętli for",
                    "p1_schemat_for.png",
                    "Schemat blokowy: start i = 1, warunek i ≤ 5, ciało pętli, i = i + 1",
                ),
                Image(
                    "vk-kod",
                    ("V", "K"),
                    "Przykład: suma liczb od 1 do 5",
                    "p1_kod.png",
                    "Kod w Pythonie liczący sumę liczb od 1 do 5 i wynik programu",
                    "Przepisz kod, uruchom go i zmień zakres na 1–10.",
                ),
                Speech(
                    "a-wyjasnienie",
                    ("A",),
                    "Posłuchaj: jak czytać pętlę for",
                    "Zdanie for i in range od jeden do sześć czytaj tak: "
                    "dla każdej liczby i od jeden do pięć zrób to, co jest niżej z wcięciem. "
                    "Uwaga: liczba sześć to granica, której pętla już nie wykona. "
                    "W pierwszym obrocie i równa się jeden, w drugim dwa, i tak aż do pięciu. "
                    "Potem pętla się kończy i program idzie dalej.",
                ),
                Pdf("k-karta", ("K",), "Karta ćwiczeń: pętla for", "p1_karta.pdf"),
            ),
        ),
        Lesson(
            "Pętla while",
            (
                Text(
                    "t1",
                    (
                        heading("Powtarzaj, dopóki warunek jest prawdziwy"),
                        paragraph(
                            "Pętla ",
                            ("while", True),
                            " sprawdza warunek przed każdym obrotem. "
                            "Jeśli w ciele pętli nic nie zmienia warunku, pętla nigdy się nie skończy.",
                        ),
                        bullets(
                            "while sprawdza się, gdy nie wiemy z góry, ile będzie powtórzeń,",
                            "zawsze zmieniaj zmienną z warunku w ciele pętli.",
                        ),
                    ),
                ),
                Image(
                    "v-schemat",
                    ("V",),
                    "Schemat blokowy pętli while",
                    "p2_schemat_while.png",
                    "Schemat blokowy pętli while z warunkiem i powrotem do sprawdzenia",
                ),
                Speech(
                    "a-wyjasnienie",
                    ("A",),
                    "Posłuchaj: pętla bez końca",
                    "Pętla while działa jak zdanie: dopóki warunek jest prawdziwy, powtarzaj. "
                    "Na przykład: dopóki i jest mniejsze od pięciu, wypisz i, a potem zwiększ i o jeden. "
                    "Jeśli zapomnisz zwiększyć i, warunek zawsze będzie prawdziwy "
                    "i program będzie działał bez końca. Dlatego w każdej pętli while szukaj linijki, "
                    "która zmienia warunek.",
                ),
                Pdf(
                    "vk-karta",
                    ("V", "K"),
                    "Karta ćwiczeń: pętla while",
                    "p2_karta.pdf",
                    "Rozwiąż na kartce, potem sprawdź w Pythonie.",
                ),
            ),
        ),
    ),
)

COURSES = (MATH, ENGLISH, PYTHON)
