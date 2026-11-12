# ruff: noqa: E501  (lesson texts are content, not code; keeping sentences whole)
"""Content of the three demo courses (v3): 3 courses x 4 lessons.

Every lesson has an outline and conclusions (TipTap), three versions with the same content
(V: text + images, A: recording + short description, K: step-by-step instruction + worksheet PDF)
and a pool of 8 single-choice questions with explanations. Files live in `assets/`
(`generate_assets.py` draws PNG and PDF, `generate_audio.py` records MP3 from `Audio.script`).

The seed builds courses from these objects through the services: `block_payload` turns a block
into the API shape of `app/modules/content/blocks.py`, `Question.payload` into a quiz question.
"""

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Literal

Form = Literal["V", "A", "K"]
FORMS: tuple[Form, ...] = ("V", "A", "K")

# --- TipTap documents ----------------------------------------------------------------------------

Part = str | tuple[str, bool]  # plain text or (text, bold)


def _text(content: str, bold: bool = False) -> dict[str, Any]:
    node: dict[str, Any] = {"type": "text", "text": content}
    if bold:
        node["marks"] = [{"type": "bold"}]
    return node


def heading(content: str, level: int = 2) -> dict[str, Any]:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(content)]}


def paragraph(*parts: Part) -> dict[str, Any]:
    """Plain strings; ("text", True) is bold."""
    nodes = [_text(*part) if isinstance(part, tuple) else _text(part) for part in parts]
    return {"type": "paragraph", "content": nodes}


def _items(items: tuple[str | list[Part], ...]) -> list[dict[str, Any]]:
    """List items: a string, or a list of parts when some words are bold."""
    return [
        {
            "type": "listItem",
            "content": [paragraph(*item) if isinstance(item, list) else paragraph(item)],
        }
        for item in items
    ]


def bullets(*items: str | list[Part]) -> dict[str, Any]:
    return {"type": "bulletList", "content": _items(items)}


def ordered(*items: str | list[Part]) -> dict[str, Any]:
    """Numbered list (TipTap `orderedList`), e.g. steps of an instruction."""
    return {"type": "orderedList", "attrs": {"start": 1}, "content": _items(items)}


def code(*lines: str) -> dict[str, Any]:
    """Program listing as one paragraph, lines joined with hard breaks (indentation kept)."""
    nodes: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        if index:
            nodes.append({"type": "hardBreak"})
        if line:
            nodes.append(_text(line))
    return {"type": "paragraph", "content": nodes}


def table(header: tuple[str, ...], *rows: tuple[str, ...]) -> dict[str, Any]:
    def row(cells: tuple[str, ...], cell_type: str) -> dict[str, Any]:
        return {
            "type": "tableRow",
            "content": [{"type": cell_type, "content": [paragraph(cell)]} for cell in cells],
        }

    return {
        "type": "table",
        "content": [row(header, "tableHeader"), *(row(cells, "tableCell") for cells in rows)],
    }


def doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


# --- Blocks --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Text:
    id: str
    doc: dict[str, Any]


@dataclass(frozen=True)
class Image:
    id: str
    title: str
    file: str
    alt: str
    description: str = ""


@dataclass(frozen=True)
class Pdf:
    id: str
    title: str
    file: str
    description: str = ""


# One turn of a recording: parts read one after another with a short gap, each by its voice.
# Voices: "Z" pl-PL-ZofiaNeural (teacher), "M" pl-PL-MarekNeural (student),
# "EN" / "EN2" British voices for English examples (see `generate_audio.VOICES`).
# Polish parts spell code words as they are said (e.g. "łajl" for while).
Turn = tuple[tuple[str, str], ...]


def say(voice: str, *parts: str | tuple[str, str]) -> Turn:
    """A turn of `voice`; a (voice, text) part is read by another voice, e.g. an English example."""
    return tuple(part if isinstance(part, tuple) else (voice, part) for part in parts)


@dataclass(frozen=True)
class Audio:
    """Recording (MP3 in `assets/`) generated from `script` by `generate_audio.py`."""

    id: str
    title: str
    file: str
    script: tuple[Turn, ...]
    description: str = ""


Block = Text | Image | Pdf | Audio


def block_payload(block: Block, file_ids: Mapping[str, int]) -> dict[str, Any]:
    """Block in the API shape (`content/blocks.py`); `file_ids` maps asset names to stored files."""
    if isinstance(block, Text):
        return {"id": block.id, "type": "text", "doc": block.doc}
    payload: dict[str, Any] = {
        "id": block.id,
        "type": "attachment",
        "title": block.title,
        "description": block.description,
        "file_id": file_ids[block.file],
    }
    if isinstance(block, Image):
        return payload | {"kind": "image", "alt": block.alt}
    if isinstance(block, Pdf):
        return payload | {"kind": "pdf"}
    return payload | {"kind": "audio"}


# --- Questions, lessons, courses -----------------------------------------------------------------


@dataclass(frozen=True)
class Question:
    """Single choice: one correct answer and 2-3 wrong ones; the explanation is shown after the quiz."""

    id: str
    text: str
    correct: str
    wrong: tuple[str, ...]
    explanation: str

    @property
    def correct_index(self) -> int:
        """Fixed but varied position of the correct answer."""
        return (sum(map(ord, self.id)) + len(self.text)) % (len(self.wrong) + 1)

    @property
    def answers(self) -> tuple[str, ...]:
        index = self.correct_index
        return (*self.wrong[:index], self.correct, *self.wrong[index:])

    def answer_id(self, index: int) -> str:
        return f"{self.id}-{'abcd'[index]}"

    def payload(self) -> dict[str, Any]:
        """Question in the API shape of `assessment/schemas.py` (`QuizQuestion`)."""
        return {
            "id": self.id,
            "text": self.text,
            "answers": [
                {"id": self.answer_id(index), "text": answer}
                for index, answer in enumerate(self.answers)
            ],
            "correct_answer_id": self.answer_id(self.correct_index),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class Lesson:
    title: str
    outline: dict[str, Any]
    conclusions: dict[str, Any]
    versions: Mapping[Form, tuple[Block, ...]]
    questions: tuple[Question, ...]


@dataclass(frozen=True)
class Course:
    code: str  # prefix of asset files, e.g. "m" -> m1_v_wykres.png
    title: str
    description: str  # catalog card, max 500 characters
    introduction: dict[str, Any]
    summary: dict[str, Any]  # "Podsumowanie i wnioski"
    lessons: tuple[Lesson, ...]


def lesson_blocks(course: Course) -> Iterator[Block]:
    for lesson in course.lessons:
        for form in FORMS:
            yield from lesson.versions[form]


def asset_files(courses: tuple[Course, ...]) -> set[str]:
    """Names of all files used by the courses (images, PDFs, recordings)."""
    return {
        block.file
        for course in courses
        for block in lesson_blocks(course)
        if not isinstance(block, Text)
    }


def audio_blocks(courses: tuple[Course, ...]) -> list[Audio]:
    return [
        block for course in courses for block in lesson_blocks(course) if isinstance(block, Audio)
    ]


WORKSHEET_STEP = "Wykonaj kartę zadania (PDF poniżej). Odpowiedzi są na ostatniej stronie karty – zajrzyj do nich dopiero po rozwiązaniu."


# =================================================================================================
# Matematyka: funkcja liniowa
# =================================================================================================

MATH = Course(
    code="m",
    title="Matematyka: funkcja liniowa",
    description=(
        "Funkcja liniowa dla klas 7–8 w czterech krótkich lekcjach: wzór y = ax + b i wykres, "
        "współczynnik kierunkowy, miejsce zerowe oraz zadania z życia – taksówka, świeca, porównanie ofert. "
        "Każdą lekcję przerobisz w formie, która Ci odpowiada: z wykresami, z nagraniem albo z kartą "
        "do samodzielnej pracy. Krótki quiz po lekcji otwiera następną."
    ),
    introduction=doc(
        heading("O kursie"),
        paragraph(
            "Funkcja liniowa to jeden z najważniejszych tematów matematyki w szkole podstawowej. "
            "Przyda się na egzaminie ósmoklasisty, w fizyce (droga i prędkość) i w zwykłych sytuacjach – "
            "gdy porównujesz ceny abonamentów albo liczysz koszt przejazdu."
        ),
        paragraph(
            "Kurs ma cztery lekcje. Każda zaczyna się od zarysu, potem przerabiasz materiał w swojej formie, "
            "a na końcu czytasz wnioski i rozwiązujesz quiz z 5 pytań. ",
            ("Zaliczenie (co najmniej 4 dobre odpowiedzi) otwiera kolejną lekcję.", True),
        ),
        paragraph("Przygotuj zeszyt w kratkę, ołówek i linijkę."),
    ),
    summary=doc(
        heading("Podsumowanie i wnioski"),
        bullets(
            "Funkcja liniowa ma wzór y = ax + b, a jej wykres to prosta. Do narysowania wystarczą dwa punkty.",
            "b to miejsce, w którym prosta przecina oś y – punkt (0, b).",
            "a mówi, o ile zmienia się y, gdy x rośnie o 1: a > 0 – funkcja rośnie, a < 0 – maleje, a = 0 – jest stała.",
            "Miejsce zerowe to x, dla którego y = 0; liczymy je z równania ax + b = 0.",
            "W zadaniach z życia b to zwykle wartość na starcie (opłata stała), a a – zmiana na jednostkę (cena za kilometr, ubytek na godzinę).",
        ),
        paragraph(
            "Co dalej: szukanie punktu, w którym dwie oferty kosztują tyle samo (lekcja 4), "
            "to wstęp do układów równań – poznasz je w kolejnych klasach."
        ),
    ),
    lessons=(
        # --- 1. Wzór i wykres -------------------------------------------------------------------
        Lesson(
            title="Wzór i wykres",
            outline=doc(
                paragraph(
                    "Poznasz wzór funkcji liniowej y = ax + b i nauczysz się liczyć jej wartości. "
                    "Z tabeli wartości narysujesz wykres – prostą – i sprawdzisz, czy dany punkt do niego należy."
                )
            ),
            conclusions=doc(
                bullets(
                    "Funkcja liniowa ma wzór y = ax + b, gdzie a i b to liczby. Każdemu x przyporządkowuje dokładnie jedną wartość y.",
                    "Wykres funkcji liniowej to prosta – wystarczą dwa punkty, trzeci służy do sprawdzenia.",
                    "Prosta przecina oś y w punkcie (0, b), bo dla x = 0 zostaje y = b.",
                    "Punkt (x, y) należy do wykresu, gdy po wstawieniu x do wzoru wychodzi właśnie y. Gdy znasz y, a szukasz x, rozwiązujesz równanie, np. 2x + 1 = 5, więc x = 2.",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Wzór funkcji liniowej"),
                            paragraph(
                                "Funkcja liniowa ma wzór ",
                                ("y = ax + b", True),
                                ", gdzie a i b to dowolne liczby. Wstawiasz liczbę x (argument), wykonujesz działania "
                                "i dostajesz wartość y. Dla każdego x wychodzi dokładnie jedno y.",
                            ),
                            paragraph(
                                "Przykład: ",
                                ("y = 2x + 1", True),
                                ". Tu a = 2 i b = 1. Dla x = 3: y = 2 · 3 + 1 = 7.",
                            ),
                            heading("Tabela wartości i wykres"),
                            paragraph("Wybierz kilka x, policz y i zapisz pary w tabeli:"),
                            table(("x", "−1", "0", "1", "2"), ("y = 2x + 1", "−1", "1", "3", "5")),
                            paragraph(
                                "Każda para to punkt w układzie współrzędnych: (−1, −1), (0, 1), (1, 3), (2, 5). "
                                "Wszystkie leżą na jednej prostej – ",
                                ("wykres funkcji liniowej to zawsze prosta", True),
                                ". Dlatego wystarczą dwa punkty, a trzeci pozwala sprawdzić, czy nie ma błędu w rachunkach.",
                            ),
                            paragraph(
                                "Zwróć uwagę na punkt (0, 1): dla x = 0 zostaje samo b. ",
                                ("Prosta przecina oś y w punkcie (0, b).", True),
                            ),
                            heading("Czy punkt należy do wykresu?"),
                            paragraph(
                                "Wstaw x do wzoru i porównaj wynik z y. Punkt (2, 5): 2 · 2 + 1 = 5 – należy. "
                                "Punkt (1, 4): 2 · 1 + 1 = 3, a nie 4 – nie należy."
                            ),
                            paragraph(
                                "Możesz też szukać w drugą stronę: dla jakiego x wartość y = 5? "
                                "Rozwiązujesz równanie 2x + 1 = 5, więc 2x = 4 i x = 2."
                            ),
                        ),
                    ),
                    Image(
                        "v-wykres",
                        "Wykres funkcji y = 2x + 1",
                        "m1_v_wykres.png",
                        "Prosta y = 2x + 1 w układzie współrzędnych z zaznaczonymi punktami (−1, −1), (0, 1), (1, 3) i (2, 5) oraz tabelą wartości",
                        "Punkty z tabeli leżą na jednej prostej; punkt (0, 1) to miejsce przecięcia z osią y.",
                    ),
                    Image(
                        "v-schemat",
                        "Od wzoru do wykresu w trzech krokach",
                        "m1_v_schemat.png",
                        "Schemat: wzór y = ax + b z opisem liter a, x i b oraz trzy kroki rysowania wykresu",
                    ),
                ),
                "A": (
                    Text(
                        "a-opis",
                        doc(
                            paragraph(
                                "Posłuchaj rozmowy nauczycielki z Markiem o wzorze i wykresie funkcji liniowej. "
                                "Najważniejsze do zapamiętania:"
                            ),
                            bullets(
                                "wzór y = ax + b i liczenie y dla danego x,",
                                "wykres to prosta – wystarczą dwa punkty,",
                                "prosta przecina oś y w punkcie (0, b),",
                                "sprawdzanie, czy punkt należy do wykresu, i szukanie x dla danego y.",
                            ),
                            paragraph("Zatrzymuj nagranie i licz razem z Markiem."),
                        ),
                    ),
                    Audio(
                        "a-nagranie",
                        "Rozmowa: wzór i wykres funkcji liniowej",
                        "m1_a_rozmowa.mp3",
                        (
                            say(
                                "Z",
                                "Cześć, Marek! Dzisiaj poznamy funkcję liniową. Jej wzór brzmi: igrek równa się a razy iks plus be.",
                            ),
                            say("M", "A co oznaczają te litery?"),
                            say(
                                "Z",
                                "A i be to liczby, które dla danej funkcji się nie zmieniają. Iks to liczba, którą wstawiamy do wzoru, a igrek to wynik. Weźmy przykład: igrek równa się dwa iks plus jeden. Tutaj a równa się dwa, a be równa się jeden.",
                            ),
                            say(
                                "M",
                                "Czyli jeśli wstawię iks równe trzy, to liczę dwa razy trzy plus jeden. Wychodzi siedem.",
                            ),
                            say(
                                "Z",
                                "Brawo. Dla każdego iksa wychodzi dokładnie jeden igrek. Policzmy kilka wartości i zapiszmy je w tabelce. Ile wychodzi dla iksa równego minus jeden?",
                            ),
                            say(
                                "M",
                                "Dwa razy minus jeden to minus dwa, plus jeden, czyli minus jeden.",
                            ),
                            say("Z", "A dla zera?"),
                            say("M", "Jeden. Dla jedynki wychodzi trzy, a dla dwójki pięć."),
                            say(
                                "Z",
                                "Świetnie. Każda para liczb to punkt w układzie współrzędnych: minus jeden i minus jeden, zero i jeden, jeden i trzy, dwa i pięć. Kiedy zaznaczysz te punkty, zobaczysz, że wszystkie leżą na jednej prostej.",
                            ),
                            say("M", "Zawsze wychodzi prosta?"),
                            say(
                                "Z",
                                "Zawsze. Wykres funkcji liniowej to prosta. Dlatego do narysowania wystarczą dwa punkty. Trzeci warto policzyć, żeby sprawdzić, czy nie ma pomyłki.",
                            ),
                            say(
                                "M",
                                "Zauważyłem coś. Dla iksa równego zero wyszło jeden, czyli tyle, ile wynosi be.",
                            ),
                            say(
                                "Z",
                                "Właśnie. Gdy iks to zero, zostaje samo be. Dlatego prosta zawsze przecina oś igrek w punkcie zero, be. W naszym przykładzie to punkt zero, jeden.",
                            ),
                            say("M", "A skąd mam wiedzieć, czy jakiś punkt leży na wykresie?"),
                            say(
                                "Z",
                                "Wstaw iks do wzoru i porównaj wynik z igrekiem. Sprawdźmy punkt jeden, cztery.",
                            ),
                            say(
                                "M",
                                "Dwa razy jeden plus jeden to trzy. A miało być cztery, więc ten punkt nie należy do wykresu.",
                            ),
                            say(
                                "Z",
                                "Dokładnie. Można też szukać w drugą stronę: dla jakiego iksa igrek równa się pięć? Rozwiązujemy równanie dwa iks plus jeden równa się pięć. Odejmujemy jeden: dwa iks równa się cztery, więc iks równa się dwa.",
                            ),
                            say("M", "Czyli wzór działa w obie strony."),
                            say(
                                "Z",
                                "Tak. Zapamiętaj trzy rzeczy: wzór igrek równa się a iks plus be, wykres to prosta, a prosta przecina oś igrek w punkcie zero, be.",
                            ),
                        ),
                        "Nauczycielka i Marek liczą wartości funkcji y = 2x + 1 i rysują jej wykres.",
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Potrzebujesz kartki w kratkę, ołówka i linijki. Wykonuj kroki po kolei."
                            ),
                            ordered(
                                "Zapisz u góry kartki wzór funkcji liniowej: y = ax + b. Litery a i b to liczby, x to argument (liczba, którą wstawiasz), y to wartość (wynik).",
                                "Weź funkcję y = 2x + 1 (a = 2, b = 1). Narysuj tabelkę z wierszami x i y, a w wierszu x wpisz: −1, 0, 1, 2.",
                                "Oblicz y dla każdego x i wpisz do tabelki, np. dla x = −1: 2 · (−1) + 1 = −1. Powinno wyjść: −1, 1, 3, 5.",
                                "Narysuj układ współrzędnych (oś x poziomo, oś y pionowo, od −5 do 5) i zaznacz punkty z tabelki: (−1, −1), (0, 1), (1, 3), (2, 5).",
                                "Przyłóż linijkę: wszystkie punkty leżą na jednej prostej. Połącz je i przedłuż prostą. Zapamiętaj: wykres funkcji liniowej to prosta, więc wystarczą dwa punkty, a trzeci służy do sprawdzenia.",
                                "Zaznacz kolorem punkt, w którym prosta przecina oś y. To (0, 1) – dla x = 0 zostaje y = b. Tak jest w każdej funkcji liniowej: punkt (0, b).",
                                "Sprawdź rachunkiem, czy punkt (1, 4) leży na prostej: 2 · 1 + 1 = 3, a nie 4 – nie leży. Zaznacz go w układzie i zobacz, że jest nad prostą.",
                                "Teraz w drugą stronę: dla jakiego x mamy y = 5? Rozwiąż równanie 2x + 1 = 5 (wychodzi x = 2) i odszukaj ten punkt na wykresie.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: tabela i wykres",
                        "m1_k_karta.pdf",
                        "Wydrukuj albo przerysuj do zeszytu. Na ostatniej stronie odpowiedzi do sprawdzenia.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Który wzór opisuje funkcję liniową?",
                    "y = 3x − 2",
                    ("y = x² + 1", "y = 2 / x", "y = x³"),
                    "Funkcja liniowa ma postać y = ax + b: x występuje w pierwszej potędze, nie jest podnoszony do kwadratu ani nie stoi w mianowniku. Tu a = 3 i b = −2.",
                ),
                Question(
                    "q2",
                    "Co jest wykresem funkcji liniowej?",
                    "prosta",
                    ("parabola", "okrąg", "łamana z kilku odcinków"),
                    "Wszystkie punkty (x, y) spełniające wzór y = ax + b leżą na jednej prostej – stąd nazwa „funkcja liniowa”.",
                ),
                Question(
                    "q3",
                    "Ile wynosi y dla x = 3 w funkcji y = 2x + 1?",
                    "7",
                    ("6", "5", "9"),
                    "Wstawiamy x = 3: y = 2 · 3 + 1 = 6 + 1 = 7.",
                ),
                Question(
                    "q4",
                    "W jakim punkcie wykres funkcji y = 2x + 1 przecina oś y?",
                    "(0, 1)",
                    ("(1, 0)", "(0, 2)", "(2, 1)"),
                    "Na osi y jest x = 0, więc y = 2 · 0 + 1 = 1. Prosta przecina oś y w punkcie (0, b), tu (0, 1).",
                ),
                Question(
                    "q5",
                    "Ile punktów wystarczy, aby narysować wykres funkcji liniowej?",
                    "2",
                    ("1", "4", "co najmniej 10"),
                    "Przez dwa punkty przechodzi dokładnie jedna prosta. Trzeci punkt warto policzyć tylko do sprawdzenia rachunków.",
                ),
                Question(
                    "q6",
                    "Czy punkt (1, 4) należy do wykresu funkcji y = 2x + 1?",
                    "Nie, bo dla x = 1 wychodzi y = 3.",
                    (
                        "Tak, bo 4 jest większe od 1.",
                        "Tak, bo 2 · 1 + 1 = 4.",
                        "Nie, bo punkt wykresu musi mieć x = 0.",
                    ),
                    "Wstawiamy x = 1: y = 2 · 1 + 1 = 3. Na wykresie leży punkt (1, 3), a nie (1, 4), więc (1, 4) jest poza prostą.",
                ),
                Question(
                    "q7",
                    "Ile wynosi b w funkcji y = −3x + 5?",
                    "5",
                    ("−3", "3", "−5"),
                    "We wzorze y = ax + b liczba b stoi osobno, bez x. Tu a = −3, a b = 5.",
                ),
                Question(
                    "q8",
                    "Dla jakiego x funkcja y = 4x − 1 ma wartość 7?",
                    "x = 2",
                    ("x = 27", "x = 1", "x = 3"),
                    "Rozwiązujemy równanie 4x − 1 = 7: 4x = 8, więc x = 2. Sprawdzenie: 4 · 2 − 1 = 7. (27 wychodzi, gdy błędnie wstawimy 7 zamiast x.)",
                ),
            ),
        ),
        # --- 2. Współczynnik kierunkowy a -------------------------------------------------------
        Lesson(
            title="Współczynnik kierunkowy a",
            outline=doc(
                paragraph(
                    "Zobaczysz, jak liczba a we wzorze y = ax + b zmienia wykres: kiedy funkcja rośnie, kiedy maleje, "
                    "kiedy jest stała i od czego zależy, jak stroma jest prosta. Nauczysz się też obliczać a z dwóch punktów."
                )
            ),
            conclusions=doc(
                bullets(
                    "a mówi, o ile zmienia się y, gdy x rośnie o 1 (w y = 3x − 1 y rośnie o 3).",
                    "a > 0 – funkcja rosnąca, a < 0 – malejąca, a = 0 – stała (pozioma prosta y = b).",
                    "Im większa liczba a bez znaku (np. 5 dla a = −5), tym bardziej stroma prosta.",
                    "a z dwóch punktów: a = (y₂ − y₁) : (x₂ − x₁). Proste o tym samym a są równoległe.",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Co mówi liczba a?"),
                            paragraph(
                                "W funkcji y = ax + b liczba a to ",
                                ("współczynnik kierunkowy", True),
                                ". Mówi, o ile zmienia się y, gdy x rośnie o 1. Dla y = 3x − 1: x = 0 daje −1, x = 1 daje 2, "
                                "x = 2 daje 5 – za każdym razem y rośnie o 3.",
                            ),
                            table(
                                ("a", "funkcja", "wykres (od lewej do prawej)", "przykład"),
                                ("a > 0", "rosnąca", "idzie w górę", "y = 2x"),
                                ("a < 0", "malejąca", "idzie w dół", "y = −x + 2"),
                                ("a = 0", "stała", "pozioma prosta y = b", "y = 4"),
                            ),
                            heading("Jak stroma jest prosta?"),
                            paragraph(
                                "Stromość zależy od wartości a ",
                                ("bez znaku", True),
                                ". Prosta y = −5x jest bardziej stroma niż y = 3x, bo 5 > 3 – tyle że opada, a nie rośnie. "
                                "Proste o tym samym a są równoległe, np. y = 2x + 5 i y = 2x − 3.",
                            ),
                            heading("Jak obliczyć a z dwóch punktów?"),
                            paragraph(
                                "Podziel zmianę y przez zmianę x: ",
                                ("a = (y₂ − y₁) : (x₂ − x₁)", True),
                                ". Dla punktów (0, 1) i (2, 7): a = (7 − 1) : (2 − 0) = 6 : 2 = 3.",
                            ),
                        ),
                    ),
                    Image(
                        "v-kierunek",
                        "Rosnąca, malejąca, stała",
                        "m2_v_kierunek.png",
                        "Trzy proste w jednym układzie: y = 2x rośnie, y = −x + 2 maleje, y = 4 jest pozioma",
                    ),
                    Image(
                        "v-obliczanie",
                        "Jak obliczyć a z dwóch punktów",
                        "m2_v_obliczanie_a.png",
                        "Prosta przez punkty (0, 1) i (2, 7) ze schodkiem: w prawo o 2, w górę o 6, więc a = 6 : 2 = 3",
                        "Schodek pokazuje zmianę x i zmianę y między punktami.",
                    ),
                ),
                "A": (
                    Text(
                        "a-opis",
                        doc(
                            paragraph(
                                "Posłuchaj rozmowy o współczynniku kierunkowym a. Najważniejsze do zapamiętania:"
                            ),
                            bullets(
                                "a mówi, o ile zmienia się y, gdy x rośnie o 1,",
                                "a > 0 – funkcja rośnie, a < 0 – maleje, a = 0 – jest stała,",
                                "stromość zależy od wartości a bez znaku,",
                                "a z dwóch punktów: zmiana y podzielona przez zmianę x; to samo a – proste równoległe.",
                            ),
                        ),
                    ),
                    Audio(
                        "a-nagranie",
                        "Rozmowa: co robi liczba a",
                        "m2_a_rozmowa.mp3",
                        (
                            say(
                                "Z",
                                "Marek, dziś zajmiemy się liczbą a we wzorze igrek równa się a iks plus be. Nazywamy ją współczynnikiem kierunkowym, bo decyduje, w którą stronę biegnie prosta.",
                            ),
                            say("M", "To znaczy?"),
                            say(
                                "Z",
                                "Liczba a mówi, o ile zmienia się igrek, gdy iks rośnie o jeden. Weźmy igrek równa się trzy iks minus jeden. Dla iksa równego zero mamy minus jeden, dla jedynki dwa, a dla dwójki pięć.",
                            ),
                            say("M", "Za każdym razem igrek rośnie o trzy. Tyle, ile wynosi a."),
                            say(
                                "Z",
                                "Właśnie. Gdy a jest dodatnie, prosta idzie w górę, jeśli patrzysz od lewej do prawej. Mówimy, że funkcja jest rosnąca.",
                            ),
                            say("M", "A jeśli a jest ujemne?"),
                            say(
                                "Z",
                                "Wtedy prosta opada, a funkcja jest malejąca. Na przykład w funkcji igrek równa się minus iks plus dwa: im większy iks, tym mniejszy igrek.",
                            ),
                            say("M", "A gdy a równa się zero?"),
                            say(
                                "Z",
                                "Zostaje samo be, na przykład igrek równa się cztery. Igrek jest zawsze taki sam, więc wykres to pozioma prosta. To funkcja stała.",
                            ),
                            say("M", "Rozumiem. A od czego zależy, czy prosta jest stroma?"),
                            say(
                                "Z",
                                "Od tego, jak duża jest liczba a, kiedy pominiesz jej znak. Prosta igrek równa się minus pięć iks jest bardziej stroma niż igrek równa się trzy iks, bo pięć to więcej niż trzy. Tylko że ona opada, a tamta rośnie.",
                            ),
                            say("M", "A jak policzyć a, gdy mam tylko dwa punkty?"),
                            say(
                                "Z",
                                "Dzielisz zmianę igreka przez zmianę iksa. Weźmy punkty zero, jeden oraz dwa, siedem. Igrek zmienił się z jednego na siedem, czyli o sześć. Iks zmienił się z zera na dwa, czyli o dwa.",
                            ),
                            say("M", "Sześć podzielić przez dwa to trzy. Czyli a równa się trzy."),
                            say(
                                "Z",
                                "Brawo. I jeszcze jedno: proste o tym samym a są równoległe. Proste igrek równa się dwa iks plus pięć i igrek równa się dwa iks minus trzy nigdy się nie przetną.",
                            ),
                            say(
                                "M",
                                "Podsumuję: a dodatnie – funkcja rośnie, a ujemne – maleje, a równe zero – jest stała. Im większe a bez znaku, tym bardziej stromo.",
                            ),
                            say("Z", "Doskonale. Tak właśnie działa współczynnik kierunkowy."),
                        ),
                        "Rozmowa o tym, jak liczba a zmienia wykres i jak obliczyć ją z dwóch punktów.",
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Potrzebujesz kartki w kratkę, linijki i trzech kolorowych długopisów lub kredek."
                            ),
                            ordered(
                                "Narysuj układ współrzędnych od −5 do 5. Zapisz obok: w funkcji y = ax + b liczba a to współczynnik kierunkowy – mówi, o ile zmienia się y, gdy x rośnie o 1.",
                                "Policz dla y = 3x − 1 wartości y dla x = 0, 1, 2 (wyjdzie −1, 2, 5). Między wynikami dopisz „+3” – y rośnie o tyle, ile wynosi a.",
                                "Pierwszym kolorem narysuj y = 2x (przez (0, 0) i (1, 2)). Prosta idzie w górę: a > 0, funkcja rosnąca.",
                                "Drugim kolorem narysuj y = −x + 2 (przez (0, 2) i (2, 0)). Prosta opada: a < 0, funkcja malejąca.",
                                "Trzecim kolorem narysuj y = 4 – poziomą prostą przez (0, 4). Tu a = 0, funkcja stała.",
                                "Porównaj stromość: narysuj ołówkiem y = 3x i y = −5x. Bardziej stroma jest ta, w której liczba a bez znaku jest większa – tu y = −5x.",
                                "Oblicz a dla prostej przez (0, 1) i (2, 7): narysuj „schodek” – w prawo o 2 (zmiana x), w górę o 6 (zmiana y). a = 6 : 2 = 3. Zapisz wzór: a = (y₂ − y₁) : (x₂ − x₁).",
                                "Narysuj y = 2x + 5 i y = 2x − 3. Mają to samo a, więc są równoległe – sprawdź linijką, że się nie przetną.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: współczynnik a",
                        "m2_k_karta.pdf",
                        "Zadania na rozpoznawanie, liczenie a i rysowanie prostych równoległych.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Funkcja y = −2x + 3 jest:",
                    "malejąca",
                    ("rosnąca", "stała"),
                    "a = −2 jest ujemne, więc gdy x rośnie o 1, y maleje o 2 – funkcja jest malejąca.",
                ),
                Question(
                    "q2",
                    "Która funkcja jest rosnąca?",
                    "y = 0,5x − 4",
                    ("y = −x + 2", "y = −3x", "y = 5"),
                    "Rosnąca jest funkcja z a > 0. Tylko w y = 0,5x − 4 współczynnik a = 0,5 jest dodatni (wyraz wolny −4 nie ma tu znaczenia).",
                ),
                Question(
                    "q3",
                    "Jak wygląda wykres funkcji y = 4?",
                    "pozioma prosta przechodząca przez punkt (0, 4)",
                    (
                        "pionowa prosta przechodząca przez punkt (4, 0)",
                        "prosta przechodząca przez punkt (0, 0)",
                        "prosta rosnąca",
                    ),
                    "y = 4 to y = 0 · x + 4: a = 0, więc y jest zawsze równe 4. Wykres to pozioma prosta przecinająca oś y w punkcie (0, 4).",
                ),
                Question(
                    "q4",
                    "Która prosta jest najbardziej stroma?",
                    "y = −5x + 1",
                    ("y = 3x", "y = 0,5x + 6", "y = x − 4"),
                    "Stromość zależy od wartości a bez znaku: 5, 3, 0,5 i 1. Największa jest 5, więc najbardziej stroma jest y = −5x + 1 – opada, ale najszybciej.",
                ),
                Question(
                    "q5",
                    "Jak zmienia się y w funkcji y = 3x − 1, gdy x rośnie o 1?",
                    "rośnie o 3",
                    ("rośnie o 1", "maleje o 1", "rośnie o 2"),
                    "Współczynnik a mówi, o ile zmienia się y przy wzroście x o 1. Tu a = 3, np. dla x = 0 mamy y = −1, a dla x = 1 – y = 2.",
                ),
                Question(
                    "q6",
                    "Prosta przechodzi przez punkty (0, 1) i (2, 7). Ile wynosi a?",
                    "3",
                    ("6", "4", "2"),
                    "a = (y₂ − y₁) : (x₂ − x₁) = (7 − 1) : (2 − 0) = 6 : 2 = 3.",
                ),
                Question(
                    "q7",
                    "Która prosta jest równoległa do prostej y = 2x + 5?",
                    "y = 2x − 3",
                    ("y = 5x + 2", "y = −2x + 5", "y = 0,5x + 5"),
                    "Proste równoległe mają ten sam współczynnik a. Prosta y = 2x − 3 ma a = 2, tak jak y = 2x + 5.",
                ),
                Question(
                    "q8",
                    "Dla jakiej wartości a funkcja y = ax + 2 jest stała?",
                    "a = 0",
                    ("a = 2", "a = 1", "a = −2"),
                    "Dla a = 0 wzór to y = 0 · x + 2 = 2 – wartość nie zależy od x, więc funkcja jest stała.",
                ),
            ),
        ),
        # --- 3. Miejsce zerowe ------------------------------------------------------------------
        Lesson(
            title="Miejsce zerowe",
            outline=doc(
                paragraph(
                    "Dowiesz się, czym jest miejsce zerowe funkcji i jak je obliczyć z równania ax + b = 0. "
                    "Odczytasz je z wykresu i sprawdzisz, gdzie funkcja ma wartości dodatnie, a gdzie ujemne."
                )
            ),
            conclusions=doc(
                bullets(
                    "Miejsce zerowe to taki x, dla którego y = 0. Wykres przecina tam oś x w punkcie (x₀, 0).",
                    "Obliczamy je z równania ax + b = 0; dla a ≠ 0 wychodzi x₀ = −b : a (np. 2x − 4 = 0, więc x₀ = 2).",
                    "Funkcja stała y = 5 nie ma miejsca zerowego, a y = 0 ma ich nieskończenie wiele.",
                    "Funkcja rosnąca ma wartości ujemne na lewo od miejsca zerowego, a dodatnie na prawo (y = 2x − 4: y > 0 dla x > 2).",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Gdzie wykres przecina oś x?"),
                            paragraph(
                                ("Miejsce zerowe", True),
                                " funkcji to taki argument x, dla którego wartość y = 0. Na wykresie to punkt (x₀, 0), "
                                "w którym prosta przecina oś x. Nie myl go z punktem (0, b), w którym prosta przecina oś y.",
                            ),
                            heading("Jak je obliczyć?"),
                            paragraph("Zamiast y wpisz 0 i rozwiąż równanie. Dla y = 2x − 4:"),
                            bullets("2x − 4 = 0", "2x = 4", "x = 2"),
                            paragraph(
                                "Miejsce zerowe to x₀ = 2, a wykres przechodzi przez punkt (2, 0). Ogólnie, gdy a ≠ 0: "
                                "z ax + b = 0 wychodzi ",
                                ("x₀ = −b : a", True),
                                ". Sprawdź: −(−4) : 2 = 2.",
                            ),
                            heading("Szczególne przypadki"),
                            bullets(
                                "y = 5 (a = 0, b ≠ 0) – pozioma prosta nad osią x, brak miejsca zerowego.",
                                "y = 0 – prosta leży na osi x, każdy x jest miejscem zerowym (nieskończenie wiele).",
                            ),
                            heading("Gdzie wartości są dodatnie?"),
                            paragraph(
                                "Funkcja y = 2x − 4 jest rosnąca. Na lewo od x₀ = 2 wykres leży pod osią x – wartości są ujemne "
                                "(dla x = 0: y = −4). Na prawo od 2 leży nad osią – wartości są dodatnie (dla x = 3: y = 2)."
                            ),
                        ),
                    ),
                    Image(
                        "v-wykres",
                        "Miejsce zerowe funkcji y = 2x − 4",
                        "m3_v_miejsce_zerowe.png",
                        "Wykres y = 2x − 4 przecinający oś x w punkcie (2, 0); część pod osią opisana jako wartości ujemne, nad osią jako dodatnie",
                    ),
                    Image(
                        "v-przypadki",
                        "Ile miejsc zerowych?",
                        "m3_v_przypadki.png",
                        "Trzy małe wykresy: y = 2x − 4 ma jedno miejsce zerowe, y = 5 nie ma żadnego, y = 0 ma nieskończenie wiele",
                    ),
                ),
                "A": (
                    Text(
                        "a-opis",
                        doc(
                            paragraph(
                                "Posłuchaj rozmowy o miejscu zerowym. Najważniejsze do zapamiętania:"
                            ),
                            bullets(
                                "miejsce zerowe to x, dla którego y = 0 – punkt (x₀, 0) na osi x,",
                                "liczymy je z równania ax + b = 0, a ≠ 0: x₀ = −b : a,",
                                "y = 5 nie ma miejsca zerowego, y = 0 ma ich nieskończenie wiele,",
                                "gdzie funkcja y = 2x − 4 ma wartości dodatnie, a gdzie ujemne.",
                            ),
                        ),
                    ),
                    Audio(
                        "a-nagranie",
                        "Rozmowa: szukamy miejsca zerowego",
                        "m3_a_rozmowa.mp3",
                        (
                            say(
                                "Z",
                                "Dziś poszukamy miejsca, w którym wykres przecina oś iks. Nazywamy je miejscem zerowym funkcji.",
                            ),
                            say("M", "Dlaczego zerowym?"),
                            say(
                                "Z",
                                "Bo w tym miejscu igrek równa się zero. Miejsce zerowe to taki iks, dla którego wartość funkcji wynosi zero. Na wykresie to punkt iks zero, zero, który leży na osi poziomej.",
                            ),
                            say("M", "Czyli to coś innego niż punkt zero, be na osi igrek?"),
                            say(
                                "Z",
                                "Tak, nie myl ich. Punkt zero, be leży na osi pionowej, a miejsce zerowe na poziomej. Policzmy przykład: igrek równa się dwa iks minus cztery. Zamiast igreka wpisujemy zero.",
                            ),
                            say(
                                "M",
                                "Dwa iks minus cztery równa się zero. Dodaję cztery: dwa iks równa się cztery. Dzielę przez dwa: iks równa się dwa.",
                            ),
                            say(
                                "Z",
                                "Świetnie. Miejsce zerowe to dwa, a wykres przechodzi przez punkt dwa, zero. Ogólnie, gdy a nie jest zerem, miejsce zerowe to minus be podzielone przez a.",
                            ),
                            say(
                                "M",
                                "Sprawdzę. Be to minus cztery, więc minus be to cztery. Cztery podzielić przez dwa daje dwa. Zgadza się.",
                            ),
                            say(
                                "Z",
                                "A teraz zagadka. Ile miejsc zerowych ma funkcja igrek równa się pięć?",
                            ),
                            say("M", "Igrek jest zawsze równy pięć, nigdy zero. Czyli żadnego?"),
                            say(
                                "Z",
                                "Dokładnie. Prosta jest pozioma i biegnie nad osią iks, więc jej nie przecina. Za to funkcja igrek równa się zero leży na osi iks i każdy iks jest jej miejscem zerowym. Jest ich nieskończenie wiele.",
                            ),
                            say("M", "Ciekawe. A co się dzieje obok miejsca zerowego?"),
                            say(
                                "Z",
                                "Wróćmy do funkcji dwa iks minus cztery. Jest rosnąca, bo a równa się dwa. Na lewo od dwójki wykres jest pod osią iks, więc wartości są ujemne. Na przykład dla zera wychodzi minus cztery. Na prawo od dwójki wykres jest nad osią i wartości są dodatnie. Dla trójki wychodzi dwa.",
                            ),
                            say(
                                "M", "Czyli dla iksów większych od dwóch ta funkcja jest dodatnia."
                            ),
                            say(
                                "Z",
                                "Tak. Zapamiętaj: miejsce zerowe liczysz, wpisując zero zamiast igreka i rozwiązując równanie. Na wykresie to punkt przecięcia prostej z osią iks.",
                            ),
                        ),
                        "Rozmowa o liczeniu miejsca zerowego, przypadkach szczególnych i znaku wartości funkcji.",
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Potrzebujesz kartki w kratkę, linijki i kolorowego długopisu."
                            ),
                            ordered(
                                "Zapisz definicję: miejsce zerowe to taki x, dla którego y = 0. Na wykresie to punkt (x₀, 0) na osi x – nie myl go z punktem (0, b) na osi y.",
                                "Oblicz miejsce zerowe funkcji y = 2x − 4. Zamiast y wpisz 0: 2x − 4 = 0, potem 2x = 4, więc x = 2.",
                                "Narysuj wykres y = 2x − 4 (np. przez punkty (0, −4) i (3, 2)) i sprawdź, że przecina oś x dokładnie w punkcie (2, 0). Zaznacz go kolorem.",
                                "Zapisz wzór ogólny: dla a ≠ 0 z równania ax + b = 0 wychodzi x₀ = −b : a. Sprawdź go na przykładzie: −(−4) : 2 = 2.",
                                "Pogrub kolorem część prostej nad osią x. Zapisz: dla x > 2 wartości są dodatnie (x = 3 daje y = 2), dla x < 2 – ujemne (x = 0 daje y = −4).",
                                "Narysuj y = 5. Prosta jest pozioma i nie dotyka osi x – funkcja nie ma miejsca zerowego.",
                                "Zastanów się nad y = 0: prosta leży na osi x, więc każdy x jest miejscem zerowym – jest ich nieskończenie wiele.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: miejsce zerowe",
                        "m3_k_karta.pdf",
                        "Liczenie miejsc zerowych, odczytywanie z wykresu i znak wartości funkcji.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Czym jest miejsce zerowe funkcji?",
                    "argumentem x, dla którego y = 0",
                    (
                        "wartością y dla x = 0",
                        "punktem przecięcia wykresu z osią y",
                        "najmniejszą wartością funkcji",
                    ),
                    "Miejsce zerowe to taki x, dla którego funkcja ma wartość 0. Na wykresie prosta przecina tam oś x. Wartość dla x = 0 to b – punkt na osi y.",
                ),
                Question(
                    "q2",
                    "Jakie jest miejsce zerowe funkcji y = 2x − 4?",
                    "2",
                    ("−4", "4", "−2"),
                    "2x − 4 = 0, więc 2x = 4 i x = 2. Sprawdzenie: 2 · 2 − 4 = 0.",
                ),
                Question(
                    "q3",
                    "Jakie jest miejsce zerowe funkcji y = −3x + 6?",
                    "2",
                    ("−2", "6", "3"),
                    "−3x + 6 = 0, więc −3x = −6 i x = 2. Sprawdzenie: −3 · 2 + 6 = 0.",
                ),
                Question(
                    "q4",
                    "W którym punkcie wykres funkcji y = 2x − 4 przecina oś x?",
                    "(2, 0)",
                    ("(0, 2)", "(0, −4)", "(−4, 0)"),
                    "Na osi x jest y = 0. Miejsce zerowe to x₀ = 2, więc punkt to (2, 0). Punkt (0, −4) to przecięcie z osią y.",
                ),
                Question(
                    "q5",
                    "Ile miejsc zerowych ma funkcja y = 5?",
                    "żadnego",
                    ("jedno: x = 5", "jedno: x = 0", "nieskończenie wiele"),
                    "y jest zawsze równe 5, nigdy 0. Pozioma prosta y = 5 biegnie nad osią x i jej nie przecina.",
                ),
                Question(
                    "q6",
                    "Jakie jest miejsce zerowe funkcji y = x + 3?",
                    "−3",
                    ("3", "0", "1"),
                    "x + 3 = 0, więc x = −3. Sprawdzenie: −3 + 3 = 0.",
                ),
                Question(
                    "q7",
                    "Dla jakich x funkcja y = 2x − 4 ma wartości dodatnie?",
                    "dla x > 2",
                    ("dla x < 2", "dla x > −4", "tylko dla x = 2"),
                    "Funkcja jest rosnąca (a = 2) i ma miejsce zerowe 2, więc na prawo od 2 wykres leży nad osią x. Np. x = 3: y = 2 > 0. Dla x = 2 wartość wynosi 0, a 0 nie jest liczbą dodatnią.",
                ),
                Question(
                    "q8",
                    "Którym wzorem obliczysz miejsce zerowe funkcji y = ax + b, gdy a ≠ 0?",
                    "x₀ = −b : a",
                    ("x₀ = b : a", "x₀ = −a : b", "x₀ = a − b"),
                    "Z równania ax + b = 0 mamy ax = −b, a po podzieleniu przez a: x₀ = −b : a. Dla y = 2x − 4: −(−4) : 2 = 2.",
                ),
            ),
        ),
        # --- 4. Funkcja liniowa w zadaniach -----------------------------------------------------
        Lesson(
            title="Funkcja liniowa w zadaniach",
            outline=doc(
                paragraph(
                    "Przełożysz sytuacje z życia na wzór y = ax + b: opłatę za taksówkę i wypalającą się świecę. "
                    "Odczytasz z wzoru koszt i czas, a na koniec porównasz dwie oferty i znajdziesz, kiedy kosztują tyle samo."
                )
            ),
            conclusions=doc(
                bullets(
                    "Gdy coś ma wartość startową i zmienia się o stałą ilość na jednostkę, opisuje to y = ax + b: b – wartość na starcie, a – zmiana na jednostkę.",
                    "Taksówka: 8 zł za start i 3 zł za km → y = 3x + 8; za 5 km płacisz 23 zł, a za 32 zł przejedziesz 8 km.",
                    "Gdy wielkość maleje (świeca 20 cm, ubywa 2 cm na godzinę), a jest ujemne: y = −2x + 20; miejsce zerowe x = 10 to chwila, gdy świeca się wypali.",
                    "Dwie oferty kosztują tyle samo, gdy ich wzory dają równe y: 3x + 8 = 4x + 2, więc x = 6 km.",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Od opisu do wzoru"),
                            paragraph(
                                "Wiele sytuacji wygląda podobnie: jest wartość na starcie i stała zmiana na każdą jednostkę "
                                "(kilometr, godzinę, minutę). Wtedy wzór to ",
                                ("y = ax + b", True),
                                ": b – wartość na starcie, a – zmiana na jednostkę, x – liczba jednostek.",
                            ),
                            heading("Przykład 1: taksówka"),
                            paragraph(
                                "Opłata początkowa 8 zł i 3 zł za każdy kilometr. Wzór: ",
                                ("y = 3x + 8", True),
                                " (x – kilometry, y – koszt w zł).",
                            ),
                            bullets(
                                "Koszt 5 km: y = 3 · 5 + 8 = 23 zł.",
                                "Ile km za 32 zł? 3x + 8 = 32, 3x = 24, x = 8 km.",
                            ),
                            heading("Przykład 2: świeca"),
                            paragraph(
                                "Świeca ma 20 cm i co godzinę ubywa jej 2 cm. Wzór: ",
                                ("y = −2x + 20", True),
                                " (x – godziny, y – wysokość w cm). a jest ujemne, bo świeca się skraca. "
                                "Wypali się, gdy y = 0: −2x + 20 = 0, więc x = 10 godzin. Wzór ma sens tylko dla x od 0 do 10.",
                            ),
                            heading("Przykład 3: która taksówka jest tańsza?"),
                            paragraph(
                                "Firma A: y = 3x + 8, firma B: y = 4x + 2. Tyle samo zapłacisz, gdy 3x + 8 = 4x + 2, czyli przy ",
                                ("x = 6 km", True),
                                " (w obu firmach 26 zł). Na krótszej trasie tańsza jest B (niska opłata na start), "
                                "na dłuższej – A (tańszy kilometr). Za 10 km: A – 38 zł, B – 42 zł.",
                            ),
                        ),
                    ),
                    Image(
                        "v-taksowki",
                        "Dwie taksówki: kiedy koszt jest równy?",
                        "m4_v_taksowki.png",
                        "Wykresy kosztu dwóch taksówek y = 3x + 8 i y = 4x + 2 przecinające się w punkcie (6, 26)",
                        "Na lewo od punktu przecięcia tańsza jest firma B, na prawo – firma A.",
                    ),
                    Image(
                        "v-swieca",
                        "Świeca: y = −2x + 20",
                        "m4_v_swieca.png",
                        "Wykres wysokości świecy malejący od 20 cm do 0 w ciągu 10 godzin",
                    ),
                ),
                "A": (
                    Text(
                        "a-opis",
                        doc(
                            paragraph(
                                "Posłuchaj, jak Marek układa wzory do zadań z życia. Najważniejsze do zapamiętania:"
                            ),
                            bullets(
                                "b to wartość na starcie, a to zmiana na jednostkę,",
                                "taksówka: y = 3x + 8 – koszt 5 km i liczba km za 32 zł,",
                                "świeca: y = −2x + 20 – kiedy się wypali (miejsce zerowe),",
                                "porównanie dwóch firm: kiedy kurs kosztuje tyle samo i która jest tańsza.",
                            ),
                        ),
                    ),
                    Audio(
                        "a-nagranie",
                        "Rozmowa: taksówka, świeca i porównanie ofert",
                        "m4_a_rozmowa.mp3",
                        (
                            say(
                                "Z",
                                "Marek, czas na zadania z życia. Wsiadasz do taksówki. Opłata na start to osiem złotych, a każdy kilometr kosztuje trzy złote. Jak zapisać to wzorem?",
                            ),
                            say(
                                "M",
                                "Trzy złote razy liczba kilometrów i do tego osiem złotych. Igrek równa się trzy iks plus osiem.",
                            ),
                            say(
                                "Z",
                                "Doskonale. Zwróć uwagę: be, czyli osiem, to wartość na starcie, a a, czyli trzy, to zmiana na każdy kilometr. Tak wygląda większość takich zadań. Ile zapłacisz za pięć kilometrów?",
                            ),
                            say(
                                "M",
                                "Trzy razy pięć to piętnaście, plus osiem. Dwadzieścia trzy złote.",
                            ),
                            say(
                                "Z",
                                "A jeśli masz trzydzieści dwa złote, ile kilometrów przejedziesz?",
                            ),
                            say(
                                "M",
                                "Trzy iks plus osiem równa się trzydzieści dwa. Odejmuję osiem: trzy iks równa się dwadzieścia cztery. Czyli iks równa się osiem kilometrów.",
                            ),
                            say(
                                "Z",
                                "Brawo. Teraz coś, co maleje. Świeca ma dwadzieścia centymetrów i co godzinę ubywa jej dwa centymetry.",
                            ),
                            say(
                                "M",
                                "Tu a będzie ujemne, bo świeca się skraca. Igrek równa się minus dwa iks plus dwadzieścia.",
                            ),
                            say("Z", "Tak. A kiedy świeca się wypali?"),
                            say(
                                "M",
                                "Gdy jej wysokość będzie równa zero. To miejsce zerowe: minus dwa iks plus dwadzieścia równa się zero, więc iks równa się dziesięć. Po dziesięciu godzinach.",
                            ),
                            say(
                                "Z",
                                "Dokładnie. Dlatego ten wzór ma sens tylko od zera do dziesięciu godzin. Na koniec porównajmy dwie firmy. Firma A: igrek równa się trzy iks plus osiem. Firma Be: igrek równa się cztery iks plus dwa. Przy jakiej długości kursu zapłacisz tyle samo?",
                            ),
                            say(
                                "M",
                                "Przyrównuję wzory: trzy iks plus osiem równa się cztery iks plus dwa. Po przeniesieniu wychodzi: sześć równa się iks. Przy sześciu kilometrach.",
                            ),
                            say(
                                "Z",
                                "Wtedy obie firmy biorą po dwadzieścia sześć złotych. Na krótszej trasie tańsza jest firma Be, bo ma niską opłatę na start. Na dłuższej firma A, bo kilometr jest tańszy. Za dziesięć kilometrów zapłacisz w firmie A trzydzieści osiem złotych, a w firmie Be czterdzieści dwa.",
                            ),
                            say("M", "Czyli najpierw wzór, potem liczenie."),
                            say(
                                "Z",
                                "Tak. Szukaj wartości na starcie, czyli be, i zmiany na jednostkę, czyli a.",
                            ),
                        ),
                        "Rozmowa o układaniu wzorów do zadań z taksówką, świecą i porównaniem dwóch firm.",
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph("Potrzebujesz kartki w kratkę, linijki i dwóch kolorów."),
                            ordered(
                                "Zapisz zasadę: gdy coś ma wartość startową i zmienia się o stałą ilość na jednostkę, wzór to y = ax + b – b to wartość na starcie, a to zmiana na jednostkę.",
                                "Taksówka A: start 8 zł, 3 zł za km. Zapisz wzór y = 3x + 8 i zrób tabelkę dla x = 0, 2, 5, 10 (wyjdzie 8, 14, 23, 38 zł).",
                                "Oblicz, ile kilometrów przejedziesz za 32 zł: 3x + 8 = 32, 3x = 24, x = 8.",
                                "Świeca: 20 cm, ubywa 2 cm na godzinę. Zapisz y = −2x + 20 (a ujemne, bo świeca się skraca). Policz wysokość po 3 godzinach (14 cm).",
                                "Oblicz, kiedy świeca się wypali: −2x + 20 = 0, x = 10. Narysuj wykres tylko dla x od 0 do 10 – dalej wzór nie ma sensu.",
                                "Taksówka B: start 2 zł, 4 zł za km, czyli y = 4x + 2. Narysuj dwoma kolorami wykresy obu firm dla x od 0 do 10 (na osi y przyjmij 1 kratkę = 5 zł).",
                                "Odczytaj punkt przecięcia i sprawdź rachunkiem: 3x + 8 = 4x + 2, więc x = 6; obie firmy biorą wtedy 26 zł.",
                                "Zapisz wniosek: poniżej 6 km tańsza jest B, powyżej – A (za 10 km: A 38 zł, B 42 zł).",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: funkcja liniowa w życiu",
                        "m4_k_karta.pdf",
                        "Wypożyczalnia rowerów, bak samochodu i porównanie dwóch ofert.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Taksówka: opłata początkowa 8 zł i 3 zł za każdy kilometr. Który wzór opisuje koszt y za x km?",
                    "y = 3x + 8",
                    ("y = 8x + 3", "y = 11x", "y = 3x − 8"),
                    "Opłata na start (8 zł) to b, a cenę za kilometr (3 zł, czyli a) mnożymy przez liczbę kilometrów: y = 3x + 8.",
                ),
                Question(
                    "q2",
                    "Ile zapłacisz za kurs na 5 km, jeśli koszt opisuje wzór y = 3x + 8?",
                    "23 zł",
                    ("15 zł", "40 zł", "19 zł"),
                    "y = 3 · 5 + 8 = 15 + 8 = 23 zł.",
                ),
                Question(
                    "q3",
                    "Koszt kursu to y = 3x + 8. Ile kilometrów przejedziesz za 32 zł?",
                    "8 km",
                    ("10 km", "13 km", "6 km"),
                    "3x + 8 = 32, więc 3x = 24 i x = 8. Sprawdzenie: 3 · 8 + 8 = 32.",
                ),
                Question(
                    "q4",
                    "Świeca ma 20 cm i co godzinę ubywa jej 2 cm. Który wzór opisuje jej wysokość y po x godzinach?",
                    "y = −2x + 20",
                    ("y = 2x + 20", "y = 20x − 2", "y = −20x + 2"),
                    "Na starcie świeca ma 20 cm (b = 20), a co godzinę ubywa 2 cm, więc a = −2 – ujemne, bo wysokość maleje.",
                ),
                Question(
                    "q5",
                    "Po ilu godzinach wypali się świeca o wysokości y = −2x + 20 (x – godziny)?",
                    "po 10 godzinach",
                    ("po 20 godzinach", "po 18 godzinach", "po 40 godzinach"),
                    "Świeca się wypali, gdy y = 0: −2x + 20 = 0, więc 2x = 20 i x = 10. To miejsce zerowe funkcji.",
                ),
                Question(
                    "q6",
                    "Co oznacza liczba 8 we wzorze kosztu taksówki y = 3x + 8?",
                    "opłatę na start, niezależną od liczby kilometrów",
                    (
                        "cenę jednego kilometra",
                        "liczbę przejechanych kilometrów",
                        "koszt całego kursu",
                    ),
                    "8 to b – wartość dla x = 0, czyli tyle płacisz, zanim taksówka przejedzie choćby kilometr. Cena kilometra to a = 3.",
                ),
                Question(
                    "q7",
                    "Firma A liczy y = 3x + 8, a firma B y = 4x + 2 (x – kilometry). Przy jakiej długości kursu zapłacisz w obu firmach tyle samo?",
                    "6 km",
                    ("2 km", "8 km", "10 km"),
                    "Przyrównujemy: 3x + 8 = 4x + 2, więc 8 − 2 = 4x − 3x i x = 6. Wtedy obie firmy biorą 26 zł.",
                ),
                Question(
                    "q8",
                    "Firma A: y = 3x + 8, firma B: y = 4x + 2. Która jest tańsza na trasie 10 km?",
                    "firma A",
                    ("firma B", "obie kosztują tyle samo"),
                    "A: 3 · 10 + 8 = 38 zł, B: 4 · 10 + 2 = 42 zł. Powyżej 6 km tańsza jest firma A, bo ma tańszy kilometr.",
                ),
            ),
        ),
    ),
)


COURSES: tuple[Course, ...] = (MATH,)
