# ruff: noqa: E501  (lesson texts are content, not code; keeping sentences whole)
"""Content of the three demo courses (v3): 3 courses x 4 lessons.

Every lesson has an outline and conclusions (TipTap), three versions with the same content
(V: text + images, A: recording + short description, K: step-by-step instruction + worksheet PDF)
and a pool of 8 single-choice questions with explanations. Files live in `assets/`
(`generate_assets.py` draws PNG and PDF, `generate_audio.py` records MP3 from `Audio.script`).

The seed builds courses from these objects through the services: `block_payload` turns a block
into the API shape of `app/modules/content/blocks.py`, `Lesson.quiz` gives the question pool.
"""

import random
import re
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

Form = Literal["V", "A", "K"]
FORMS: tuple[Form, ...] = ("V", "A", "K")

# --- TipTap documents ----------------------------------------------------------------------------

Node = dict[str, Any]
# plain text (code in `backticks`), (text, bold) or a ready node (e.g. `mono`)
Part = str | tuple[str, bool] | Node


def _text(content: str, bold: bool = False) -> Node:
    node: Node = {"type": "text", "text": content}
    if bold:
        node["marks"] = [{"type": "bold"}]
    return node


def mono(content: str) -> Node:
    """Code or a formula inside a sentence (TipTap mark `code`, fixed-width font)."""
    return {"type": "text", "text": content, "marks": [{"type": "code"}]}


def _nodes(part: Part) -> list[Node]:
    """Text nodes of one part; in plain strings `backticks` mark code, as in Markdown."""
    if isinstance(part, dict):
        return [part]
    if isinstance(part, tuple):
        return [_text(*part)]
    pieces = part.split("`")
    return [mono(piece) if odd % 2 else _text(piece) for odd, piece in enumerate(pieces) if piece]


def heading(content: str, level: int = 2) -> Node:
    return {"type": "heading", "attrs": {"level": level}, "content": [_text(content)]}


def paragraph(*parts: Part) -> Node:
    """Plain strings (code in `backticks`); ("text", True) is bold; `mono(...)` is code too."""
    return {"type": "paragraph", "content": [node for part in parts for node in _nodes(part)]}


def _items(items: tuple[str | list[Part], ...]) -> list[Node]:
    """List items: a string, or a list of parts when some words are bold or code."""
    return [
        {
            "type": "listItem",
            "content": [paragraph(*item) if isinstance(item, list) else paragraph(item)],
        }
        for item in items
    ]


def bullets(*items: str | list[Part]) -> Node:
    return {"type": "bulletList", "content": _items(items)}


def ordered(*items: str | list[Part]) -> Node:
    """Numbered list (TipTap `orderedList`), e.g. steps of an instruction."""
    return {"type": "orderedList", "attrs": {"start": 1}, "content": _items(items)}


def code_block(*lines: str) -> Node:
    """Program listing or a calculation (TipTap `codeBlock`), indentation kept."""
    return {
        "type": "codeBlock",
        "attrs": {"language": None},
        "content": [_text("\n".join(lines))],
    }


def table(header: tuple[str, ...], *rows: tuple[str, ...]) -> Node:
    def row(cells: tuple[str, ...], cell_type: str) -> Node:
        return {
            "type": "tableRow",
            "content": [{"type": cell_type, "content": [paragraph(cell)]} for cell in cells],
        }

    return {
        "type": "table",
        "content": [row(header, "tableHeader"), *(row(cells, "tableCell") for cells in rows)],
    }


def doc(*nodes: Node) -> Node:
    return {"type": "doc", "content": list(nodes)}


# --- Blocks --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Text:
    id: str
    doc: Node


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


# Voices (see `generate_audio.VOICES`): "Z" teacher (pl-PL-ZofiaNeural), "M" student Marek
# (pl-PL-MarekNeural), "EN" / "EN2" British voices for English examples.
SPEAKERS = {"Z": "Nauczycielka", "M": "Marek", "EN": "Lektorka", "EN2": "Lektor"}

# {written|spoken}: the transcript shows the first part, the voice reads the second
_SPOKEN = re.compile(r"\{([^{}|]*)\|([^{}|]*)\}")


@dataclass(frozen=True)
class Line:
    """Text read by one voice in one go.

    Code, formulas and digits are marked `{written|spoken}`, e.g. `{y = 2x|igrek równa się dwa
    iks}`: the student reads `y = 2x` in the transcript and hears natural Polish.
    """

    voice: str
    text: str

    @property
    def written(self) -> str:
        return _SPOKEN.sub(r"\1", self.text)

    @property
    def spoken(self) -> str:
        return _SPOKEN.sub(r"\2", self.text)


@dataclass(frozen=True)
class Turn:
    """One turn of a recording: lines read one after another with a short gap."""

    speaker: str
    lines: tuple[Line, ...]


def say(voice: str, *parts: str | Line) -> Turn:
    """A turn of `voice`; a `Line` part is read by another voice, e.g. `en("I have seen it.")`."""
    return Turn(
        voice, tuple(part if isinstance(part, Line) else Line(voice, part) for part in parts)
    )


def en(text: str) -> Line:
    return Line("EN", text)


def en2(text: str) -> Line:
    return Line("EN2", text)


@dataclass(frozen=True)
class Audio:
    """Recording (MP3 in `assets/`) generated from `script` by `generate_audio.py`.

    Version A has 2-3 short recordings (30-50 s) titled like the sections of version V and
    a recap (20-30 s) at the end; each one carries its transcript (D58).
    """

    id: str
    title: str
    file: str
    script: tuple[Turn, ...]
    description: str = ""
    recap: bool = False

    def transcript(self) -> str:
        """What the recording says, as the student reads it under the player; speakers named
        when more than one voice speaks."""
        dialog = len({turn.speaker for turn in self.script}) > 1
        lines = []
        for turn in self.script:
            text = " ".join(line.written for line in turn.lines)
            lines.append(f"{SPEAKERS[turn.speaker]}: {text}" if dialog else text)
        return "\n".join(lines)


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
    # the recording and its transcript (expandable under the player, D58)
    return payload | {"kind": "audio", "transcript": block.transcript()}


# --- Questions, lessons, courses -----------------------------------------------------------------


@dataclass(frozen=True)
class Question:
    """Single choice: one correct answer and 2-3 wrong ones; the explanation is shown after the quiz."""

    id: str
    text: str
    correct: str
    wrong: tuple[str, ...]
    explanation: str

    def answers(self, position: int) -> tuple[str, ...]:
        """Answers with the correct one at `position` (modulo the number of answers)."""
        index = position % (len(self.wrong) + 1)
        return (*self.wrong[:index], self.correct, *self.wrong[index:])

    def answer_id(self, index: int) -> str:
        return f"{self.id}-{'abcd'[index]}"

    def payload(self, position: int) -> dict[str, Any]:
        """Question in the API shape of `assessment/schemas.py` (`QuizQuestion`)."""
        answers = self.answers(position)
        return {
            "id": self.id,
            "text": self.text,
            "answers": [
                {"id": self.answer_id(index), "text": answer}
                for index, answer in enumerate(answers)
            ],
            "correct_answer_id": self.answer_id(answers.index(self.correct)),
            "explanation": self.explanation,
        }


@dataclass(frozen=True)
class Lesson:
    title: str
    outline: dict[str, Any]
    conclusions: dict[str, Any]
    versions: Mapping[Form, tuple[Block, ...]]
    questions: tuple[Question, ...]

    def quiz(self) -> list[dict[str, Any]]:
        """Question pool in the API shape. Correct answers are spread evenly over the positions
        (each used equally often), shuffled with a fixed seed so the seed gives the same pool."""
        positions = [index % 4 for index in range(len(self.questions))]
        random.Random(self.title).shuffle(positions)
        return [
            question.payload(position)
            for question, position in zip(self.questions, positions, strict=True)
        ]


@dataclass(frozen=True)
class Course:
    code: str  # prefix of asset files, e.g. "m" -> m1_v_wykres.png
    title: str
    description: str  # catalog card, max 500 characters
    introduction: dict[str, Any]
    summary: Node  # "Podsumowanie i wnioski"; no own heading (the course page titles it)
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
TRANSCRIPT_TIP = "Pod każdym nagraniem możesz rozwinąć transkrypcję – zapis tego, co słyszysz."


def audio_intro(lead: str) -> Text:
    """Short text of version A (R11 needs a description besides the recordings)."""
    return Text("a-opis", doc(paragraph(lead), paragraph(TRANSCRIPT_TIP)))


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
                                mono("y = ax + b"),
                                ", gdzie a i b to dowolne liczby. Wstawiasz liczbę x (argument), wykonujesz działania "
                                "i dostajesz wartość y. Dla każdego x wychodzi dokładnie jedno y.",
                            ),
                            paragraph(
                                "Przykład: ",
                                mono("y = 2x + 1"),
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
                    audio_intro(
                        "Trzy krótkie rozmowy nauczycielki z Markiem o wzorze i wykresie funkcji liniowej, a na końcu powtórka. "
                        "Zatrzymuj nagranie i licz razem z Markiem."
                    ),
                    Audio(
                        "a-1",
                        "Wzór funkcji liniowej",
                        "m1_a1_wzor.mp3",
                        (
                            say(
                                "Z",
                                "Cześć, Marek! Dziś poznamy funkcję liniową. Jej wzór to {y = ax + b|igrek równa się a iks plus be}.",
                            ),
                            say("M", "A co oznaczają te litery?"),
                            say(
                                "Z",
                                "{a i b|A i be} to liczby, które w danej funkcji się nie zmieniają. {x|Iks} to liczba, którą wstawiamy do wzoru, a {y|igrek} to wynik. "
                                "Weźmy przykład: {y = 2x + 1|igrek równa się dwa iks plus jeden}. Tutaj {a = 2|a równa się dwa}, a {b = 1|be równa się jeden}.",
                            ),
                            say(
                                "M",
                                "Czyli jeśli wstawię {x = 3|iks równe trzy}, liczę {2 · 3 + 1|dwa razy trzy plus jeden}. Wychodzi {7|siedem}.",
                            ),
                            say(
                                "Z",
                                "Brawo. I zapamiętaj: dla każdego {x|iksa} wychodzi dokładnie jeden {y|igrek}.",
                            ),
                        ),
                        "Co oznaczają litery we wzorze y = ax + b i jak policzyć y dla danego x.",
                    ),
                    Audio(
                        "a-2",
                        "Tabela wartości i wykres",
                        "m1_a2_wykres.mp3",
                        (
                            say(
                                "Z",
                                "Policzmy kilka wartości funkcji {y = 2x + 1|igrek równa się dwa iks plus jeden} i zapiszmy je w tabelce. Ile wychodzi dla {x = −1|iksa równego minus jeden}?",
                            ),
                            say(
                                "M",
                                "{2 · (−1) = −2|Dwa razy minus jeden to minus dwa}, plus jeden, czyli {−1|minus jeden}.",
                            ),
                            say("Z", "A dla zera?"),
                            say(
                                "M",
                                "{1|Jeden}. Dla {x = 1|jedynki} wychodzi {3|trzy}, a dla {x = 2|dwójki} – {5|pięć}.",
                            ),
                            say(
                                "Z",
                                "Każda para to punkt: {(−1, −1), (0, 1), (1, 3) i (2, 5)|minus jeden i minus jeden, zero i jeden, jeden i trzy, dwa i pięć}. "
                                "Wszystkie leżą na jednej prostej. Wykres funkcji liniowej to zawsze prosta, więc wystarczą dwa punkty.",
                            ),
                            say(
                                "M",
                                "Dla {x = 0|iksa równego zero} wyszło {1|jeden}, czyli tyle, ile wynosi {b|be}.",
                            ),
                            say(
                                "Z",
                                "Właśnie. Prosta przecina oś {y|igrek} w punkcie {(0, b)|zero, be}.",
                            ),
                        ),
                        "Tabela wartości funkcji y = 2x + 1, punkty na jednej prostej i punkt (0, b).",
                    ),
                    Audio(
                        "a-3",
                        "Czy punkt należy do wykresu?",
                        "m1_a3_punkt.mp3",
                        (
                            say("M", "Skąd mam wiedzieć, czy jakiś punkt leży na wykresie?"),
                            say(
                                "Z",
                                "Wstaw {x|iks} do wzoru i porównaj wynik z {y|igrekiem}. Sprawdźmy punkt {(1, 4)|jeden, cztery}.",
                            ),
                            say(
                                "M",
                                "{2 · 1 + 1 = 3|Dwa razy jeden plus jeden to trzy}, a miało być {4|cztery}. Ten punkt nie należy do wykresu.",
                            ),
                            say("Z", "Dokładnie. A punkt {(2, 5)|dwa, pięć}?"),
                            say("M", "{2 · 2 + 1 = 5|Dwa razy dwa plus jeden to pięć}. Należy."),
                            say(
                                "Z",
                                "Można też szukać w drugą stronę: dla jakiego {x|iksa} mamy {y = 5|igrek równy pięć}? Rozwiązujemy równanie {2x + 1 = 5|dwa iks plus jeden równa się pięć}. "
                                "Odejmujemy jeden: {2x = 4|dwa iks równa się cztery}, więc {x = 2|iks równa się dwa}.",
                            ),
                            say("M", "Czyli wzór działa w obie strony."),
                        ),
                        "Sprawdzanie punktów (1, 4) i (2, 5) oraz szukanie x, gdy znamy y.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "m1_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórzmy najważniejsze. Funkcja liniowa ma wzór {y = ax + b|igrek równa się a iks plus be}. Jej wykres to prosta, więc wystarczą dwa punkty. "
                                "Prosta przecina oś {y|igrek} w punkcie {(0, b)|zero, be}. Punkt należy do wykresu, gdy po wstawieniu {x|iksa} do wzoru wychodzi jego {y|igrek}. "
                                "Na przykład dla {y = 2x + 1|igrek równa się dwa iks plus jeden} i {x = 3|iksa równego trzy} wychodzi {7|siedem}.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
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
                                mono("a = (y₂ − y₁) : (x₂ − x₁)"),
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
                    audio_intro(
                        "Trzy krótkie rozmowy o liczbie a we wzorze y = ax + b – kierunek, stromość i obliczanie a z dwóch punktów – a na końcu powtórka."
                    ),
                    Audio(
                        "a-1",
                        "Co mówi liczba a?",
                        "m2_a1_liczba_a.mp3",
                        (
                            say(
                                "Z",
                                "Marek, dziś zajmiemy się liczbą a we wzorze {y = ax + b|igrek równa się a iks plus be}. To współczynnik kierunkowy. "
                                "Mówi, o ile zmienia się {y|igrek}, gdy {x|iks} rośnie o jeden. Weźmy {y = 3x − 1|igrek równa się trzy iks minus jeden}. "
                                "Dla zera mamy {−1|minus jeden}, dla jedynki {2|dwa}, a dla dwójki {5|pięć}.",
                            ),
                            say(
                                "M", "Za każdym razem {y|igrek} rośnie o trzy. Tyle, ile wynosi a."
                            ),
                            say(
                                "Z",
                                "Właśnie. Gdy {a > 0|a jest dodatnie}, funkcja jest rosnąca. Gdy {a < 0|a jest ujemne} – malejąca, jak {y = −x + 2|igrek równa się minus iks plus dwa}. "
                                "A gdy {a = 0|a równa się zero}, zostaje samo {b|be}, na przykład {y = 4|igrek równa się cztery}. To funkcja stała, a jej wykres to pozioma prosta.",
                            ),
                        ),
                        "O ile zmienia się y, gdy x rośnie o 1, i kiedy funkcja rośnie, maleje albo jest stała.",
                    ),
                    Audio(
                        "a-2",
                        "Jak stroma jest prosta?",
                        "m2_a2_stromosc.mp3",
                        (
                            say("M", "A od czego zależy, czy prosta jest stroma?"),
                            say(
                                "Z",
                                "Od tego, jak duża jest liczba a, gdy pominiesz jej znak. Prosta {y = −5x|igrek równa się minus pięć iks} jest bardziej stroma niż {y = 3x|igrek równa się trzy iks}, bo pięć to więcej niż trzy.",
                            ),
                            say("M", "Ale ona opada, a tamta rośnie."),
                            say(
                                "Z",
                                "Tak. Znak mówi o kierunku, a wielkość liczby – o stromości. I jeszcze jedno: proste o tym samym a są równoległe. "
                                "Proste {y = 2x + 5|igrek równa się dwa iks plus pięć} i {y = 2x − 3|igrek równa się dwa iks minus trzy} nigdy się nie przetną.",
                            ),
                            say("M", "Bo obie rosną tak samo szybko."),
                        ),
                        "Stromość prostej i proste równoległe.",
                    ),
                    Audio(
                        "a-3",
                        "Jak obliczyć a z dwóch punktów?",
                        "m2_a3_dwa_punkty.mp3",
                        (
                            say("M", "A jak policzyć a, gdy mam tylko dwa punkty?"),
                            say(
                                "Z",
                                "Dzielisz zmianę {y|igreka} przez zmianę {x|iksa}. Weźmy punkty {(0, 1)|zero, jeden} i {(2, 7)|dwa, siedem}. "
                                "{y|Igrek} zmienił się z jednego na siedem, czyli o sześć.",
                            ),
                            say("M", "A {x|iks} z zera na dwa, czyli o dwa."),
                            say(
                                "Z",
                                "Więc {a = 6 : 2 = 3|a równa się sześć podzielić przez dwa, czyli trzy}. Wzór ogólny: "
                                "{a = (y₂ − y₁) : (x₂ − x₁)|a równa się igrek dwa minus igrek jeden, podzielone przez iks dwa minus iks jeden}.",
                            ),
                            say(
                                "M",
                                "Sprawdzę: od punktu {(0, 1)|zero, jeden} w prawo o jeden i w górę o trzy daje {(1, 4)|jeden, cztery}. Jeszcze raz to samo i jestem w {(2, 7)|dwa, siedem}. Zgadza się.",
                            ),
                        ),
                        "Zmiana y podzielona przez zmianę x na przykładzie punktów (0, 1) i (2, 7).",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "m2_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. Liczba a mówi, o ile zmienia się {y|igrek}, gdy {x|iks} rośnie o jeden. "
                                "{a > 0|A większe od zera} – funkcja rośnie, {a < 0|a mniejsze od zera} – maleje, {a = 0|a równe zero} – jest stała. "
                                "Im większe a bez znaku, tym bardziej stroma prosta, a proste o tym samym a są równoległe. "
                                "Z dwóch punktów liczysz a, dzieląc zmianę {y|igreka} przez zmianę {x|iksa}.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
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
                            code_block("2x − 4 = 0", "2x = 4", "x = 2"),
                            paragraph(
                                "Miejsce zerowe to x₀ = 2, a wykres przechodzi przez punkt (2, 0). Ogólnie, gdy a ≠ 0: "
                                "z ax + b = 0 wychodzi ",
                                mono("x₀ = −b : a"),
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
                    audio_intro(
                        "Trzy krótkie rozmowy o miejscu zerowym – jak je obliczyć, przypadki szczególne i znak wartości funkcji – a na końcu powtórka. "
                        "Zatrzymuj nagranie i rozwiązuj równania razem z Markiem."
                    ),
                    Audio(
                        "a-1",
                        "Jak obliczyć miejsce zerowe?",
                        "m3_a1_obliczanie.mp3",
                        (
                            say(
                                "Z",
                                "Dziś poszukamy miejsca, w którym wykres przecina oś {x|iks}. To miejsce zerowe funkcji – taki {x|iks}, dla którego {y = 0|igrek równa się zero}.",
                            ),
                            say(
                                "M",
                                "Czyli to coś innego niż punkt {(0, b)|zero, be} na osi {y|igrek}?",
                            ),
                            say(
                                "Z",
                                "Tak, nie myl ich. Policzmy przykład: {y = 2x − 4|igrek równa się dwa iks minus cztery}. Zamiast {y|igreka} wpisujemy zero.",
                            ),
                            say(
                                "M",
                                "{2x − 4 = 0|Dwa iks minus cztery równa się zero}. Dodaję cztery: {2x = 4|dwa iks równa się cztery}. Dzielę przez dwa: {x = 2|iks równa się dwa}.",
                            ),
                            say(
                                "Z",
                                "Świetnie. Miejsce zerowe to dwa, a wykres przechodzi przez punkt {(2, 0)|dwa, zero}.",
                            ),
                        ),
                        "Miejsce zerowe funkcji y = 2x − 4 z równania 2x − 4 = 0.",
                    ),
                    Audio(
                        "a-2",
                        "Szczególne przypadki",
                        "m3_a2_przypadki.mp3",
                        (
                            say(
                                "Z",
                                "Ogólnie, gdy {a ≠ 0|a nie jest zerem}, miejsce zerowe to {x₀ = −b : a|minus be podzielone przez a}. Sprawdź to na naszym przykładzie.",
                            ),
                            say(
                                "M",
                                "{b = −4|Be to minus cztery}, więc {−b = 4|minus be to cztery}. {4 : 2 = 2|Cztery podzielić przez dwa daje dwa}. Zgadza się.",
                            ),
                            say(
                                "Z",
                                "A teraz zagadka. Ile miejsc zerowych ma funkcja {y = 5|igrek równa się pięć}?",
                            ),
                            say(
                                "M", "{y|Igrek} jest zawsze równy pięć, nigdy zero. Czyli żadnego?"
                            ),
                            say(
                                "Z",
                                "Dokładnie. Ta pozioma prosta biegnie nad osią {x|iks} i jej nie przecina. Za to {y = 0|igrek równa się zero} leży na osi {x|iks}, "
                                "więc każdy {x|iks} jest miejscem zerowym. Jest ich nieskończenie wiele.",
                            ),
                        ),
                        "Wzór x₀ = −b : a oraz funkcje y = 5 i y = 0.",
                    ),
                    Audio(
                        "a-3",
                        "Gdzie wartości są dodatnie?",
                        "m3_a3_znak.mp3",
                        (
                            say("M", "A co się dzieje obok miejsca zerowego?"),
                            say(
                                "Z",
                                "Wróćmy do {y = 2x − 4|igrek równa się dwa iks minus cztery}. Funkcja jest rosnąca, bo {a = 2|a równa się dwa}. "
                                "Na lewo od dwójki wykres leży pod osią {x|iks}, więc wartości są ujemne. Dla zera wychodzi {−4|minus cztery}.",
                            ),
                            say("M", "A na prawo od dwójki?"),
                            say(
                                "Z",
                                "Tam wykres jest nad osią i wartości są dodatnie. Dla trójki wychodzi {2|dwa}.",
                            ),
                            say(
                                "M",
                                "Czyli {y > 0|igrek jest dodatni} dla {x > 2|iksów większych od dwóch}, a ujemny dla mniejszych.",
                            ),
                            say("Z", "Tak. Miejsce zerowe dzieli oś {x|iks} na dwie części."),
                        ),
                        "Gdzie funkcja y = 2x − 4 ma wartości dodatnie, a gdzie ujemne.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "m3_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. Miejsce zerowe to {x|iks}, dla którego {y = 0|igrek równa się zero}. Na wykresie to punkt przecięcia prostej z osią {x|iks}. "
                                "Liczysz je, wpisując zero zamiast {y|igreka} i rozwiązując równanie: {2x − 4 = 0|dwa iks minus cztery równa się zero}, więc {x = 2|iks równa się dwa}. "
                                "Funkcja {y = 5|igrek równa się pięć} nie ma miejsca zerowego, a {y = 0|igrek równa się zero} ma ich nieskończenie wiele.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
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
                                mono("y = ax + b"),
                                ": b – wartość na starcie, a – zmiana na jednostkę, x – liczba jednostek.",
                            ),
                            heading("Przykład 1: taksówka"),
                            paragraph(
                                "Opłata początkowa 8 zł i 3 zł za każdy kilometr. Wzór: ",
                                mono("y = 3x + 8"),
                                " (x – kilometry, y – koszt w zł).",
                            ),
                            bullets(
                                "Koszt 5 km: y = 3 · 5 + 8 = 23 zł.",
                                "Ile km za 32 zł? 3x + 8 = 32, 3x = 24, x = 8 km.",
                            ),
                            heading("Przykład 2: świeca"),
                            paragraph(
                                "Świeca ma 20 cm i co godzinę ubywa jej 2 cm. Wzór: ",
                                mono("y = −2x + 20"),
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
                    audio_intro(
                        "Trzy krótkie rozmowy o zadaniach z życia – taksówka, świeca i porównanie dwóch firm – a na końcu powtórka. "
                        "Zatrzymuj nagranie i licz razem z Markiem."
                    ),
                    Audio(
                        "a-1",
                        "Taksówka: od opisu do wzoru",
                        "m4_a1_taksowka.mp3",
                        (
                            say(
                                "Z",
                                "Marek, wsiadasz do taksówki. Opłata na start to {8 zł|osiem złotych}, a każdy kilometr kosztuje {3 zł|trzy złote}. Jak to zapisać wzorem?",
                            ),
                            say(
                                "M",
                                "Trzy złote razy liczba kilometrów i do tego osiem złotych. {y = 3x + 8|Igrek równa się trzy iks plus osiem}.",
                            ),
                            say(
                                "Z",
                                "Doskonale. {b|Be} to wartość na starcie, a a to zmiana na każdy kilometr. Ile zapłacisz za {5 km|pięć kilometrów}?",
                            ),
                            say(
                                "M",
                                "{3 · 5 + 8 = 23|Trzy razy pięć to piętnaście, plus osiem – dwadzieścia trzy}. {23 zł|Dwadzieścia trzy złote}.",
                            ),
                            say(
                                "Z",
                                "A ile kilometrów przejedziesz za {32 zł|trzydzieści dwa złote}?",
                            ),
                            say(
                                "M",
                                "{3x + 8 = 32|Trzy iks plus osiem równa się trzydzieści dwa}, więc {3x = 24|trzy iks równa się dwadzieścia cztery} i {x = 8|iks równa się osiem}. {8 km|Osiem kilometrów}.",
                            ),
                        ),
                        "Wzór y = 3x + 8: koszt 5 km i liczba kilometrów za 32 zł.",
                    ),
                    Audio(
                        "a-2",
                        "Świeca, która się wypala",
                        "m4_a2_swieca.mp3",
                        (
                            say(
                                "Z",
                                "Teraz coś, co maleje. Świeca ma {20 cm|dwadzieścia centymetrów} i co godzinę ubywa jej {2 cm|dwa centymetry}.",
                            ),
                            say(
                                "M",
                                "Tu a będzie ujemne, bo świeca się skraca. {y = −2x + 20|Igrek równa się minus dwa iks plus dwadzieścia}.",
                            ),
                            say("Z", "Tak. A kiedy świeca się wypali?"),
                            say(
                                "M",
                                "Gdy jej wysokość będzie równa zero. To miejsce zerowe: {−2x + 20 = 0|minus dwa iks plus dwadzieścia równa się zero}, "
                                "więc {x = 10|iks równa się dziesięć}. Po {10|dziesięciu} godzinach.",
                            ),
                            say(
                                "Z",
                                "Dokładnie. Dlatego ten wzór ma sens tylko dla {x|iksów} od {0|zera} do {10|dziesięciu}. Później świecy już nie ma.",
                            ),
                        ),
                        "Wzór y = −2x + 20 i miejsce zerowe jako chwila, gdy świeca się wypali.",
                    ),
                    Audio(
                        "a-3",
                        "Która taksówka jest tańsza?",
                        "m4_a3_porownanie.mp3",
                        (
                            say(
                                "Z",
                                "Porównajmy dwie firmy. Firma A: {y = 3x + 8|igrek równa się trzy iks plus osiem}. Firma {B: y = 4x + 2|Be: igrek równa się cztery iks plus dwa}. Kiedy zapłacisz tyle samo?",
                            ),
                            say(
                                "M",
                                "Przyrównuję wzory: {3x + 8 = 4x + 2|trzy iks plus osiem równa się cztery iks plus dwa}. Wychodzi {x = 6|iks równa się sześć}. Przy {6 km|sześciu kilometrach}.",
                            ),
                            say(
                                "Z",
                                "Wtedy obie firmy biorą po {26 zł|dwadzieścia sześć złotych}. Na krótszej trasie tańsza jest firma {B|Be}, bo ma niską opłatę na start. "
                                "Na dłuższej – firma A, bo kilometr jest tańszy. Za {10 km|dziesięć kilometrów} zapłacisz w A {38 zł|trzydzieści osiem złotych}, a w {B 42 zł|Be czterdzieści dwa}.",
                            ),
                        ),
                        "Kiedy dwie oferty kosztują tyle samo: 3x + 8 = 4x + 2.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "m4_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. W zadaniu szukaj dwóch liczb: wartości na starcie, czyli {b|be}, i zmiany na jednostkę, czyli a. "
                                "Taksówka: {y = 3x + 8|igrek równa się trzy iks plus osiem}. Świeca, która maleje: {y = −2x + 20|igrek równa się minus dwa iks plus dwadzieścia}, "
                                "a miejsce zerowe mówi, kiedy się wypali. Dwie oferty kosztują tyle samo, gdy ich wzory dają równe {y|igreki}.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
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


# =================================================================================================
# Angielski: Present Perfect
# =================================================================================================

ENGLISH = Course(
    code="e",
    title="Angielski: Present Perfect",
    description=(
        "Present Perfect krok po kroku dla klas 6–8: budowa zdania z have/has i trzecią formą czasownika, "
        "słówka ever, never, already i yet, różnica między for i since oraz wybór między Present Perfect "
        "a Past Simple. Każdą lekcję przerobisz z tabelami i osią czasu, z nagraniem (objaśnienia po polsku, "
        "przykłady czytane po angielsku) albo z kartą ćwiczeń. Quiz po lekcji otwiera następną."
    ),
    introduction=doc(
        paragraph(
            "Present Perfect to czas, który łączy przeszłość z teraźniejszością: mówi o tym, co się wydarzyło "
            "i ma znaczenie teraz. W języku polskim nie ma takiego czasu, dlatego warto poćwiczyć go osobno."
        ),
        paragraph(
            "Kurs ma cztery lekcje: budowa zdania, słówka ever, never, already i yet, for i since oraz porównanie "
            "z Past Simple. Po każdej lekcji rozwiązujesz quiz z 5 pytań – ",
            ("zaliczenie (co najmniej 4 dobre odpowiedzi) otwiera następną lekcję.", True),
        ),
        paragraph(
            "W nagraniach objaśnienia są po polsku, a angielskie zdania przykładowe czytają głosy z wymową brytyjską."
        ),
    ),
    summary=doc(
        bullets(
            "Budowa: have/has + trzecia forma czasownika (V3). Has tylko z he, she, it; przeczenie haven't/hasn't, pytanie Have/Has + osoba + V3?",
            "ever (kiedykolwiek) w pytaniach, never (nigdy) w zdaniach twierdzących, already (już) przed V3, yet (już / jeszcze) na końcu pytań i przeczeń.",
            "for + okres (for three years), since + początek (since 2019, since Monday) – gdy coś trwa od przeszłości do teraz.",
            "Past Simple, gdy podajesz zakończony czas (yesterday, last week, ago) albo pytasz When…?; Present Perfect, gdy czas jest nieważny albo okres wciąż trwa.",
        ),
        paragraph(
            "Sprawdzian dla siebie: opowiedz po angielsku o trzech swoich doświadczeniach (I have been…, I have tried…) "
            "i o jednej rzeczy, której jeszcze nie ma na Twojej liście (I have never…)."
        ),
    ),
    lessons=(
        # --- 1. Budowa zdania -------------------------------------------------------------------
        Lesson(
            title="Budowa zdania",
            outline=doc(
                paragraph(
                    "Nauczysz się budować zdania w Present Perfect: twierdzące, przeczące i pytające. "
                    "Poznasz trzecią formę czasownika (V3) – regularną z końcówką -ed i nieregularną z tabeli – oraz krótkie odpowiedzi."
                )
            ),
            conclusions=doc(
                bullets(
                    "Zdanie twierdzące: osoba + have/has + V3, np. I have finished. Has tylko z he, she, it: She has finished.",
                    "V3 czasowników regularnych kończy się na -ed (play → played), nieregularnych – to trzecia kolumna tabeli (go – went – gone).",
                    "Przeczenie: haven't / hasn't + V3; pytanie: Have / Has + osoba + V3? Krótkie odpowiedzi: Yes, I have. / No, she hasn't.",
                    "Skróty: I've, you've, he's, she's – tu 's to has, nie is (She's visited Rome = She has visited Rome).",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Present Perfect = have / has + V3"),
                            paragraph(
                                "Present Perfect opisuje coś, co wydarzyło się w przeszłości i ma znaczenie teraz (skutek albo doświadczenie). "
                                "Nie podajemy, kiedy dokładnie to było."
                            ),
                            table(
                                ("osoba", "twierdzenie", "przeczenie", "pytanie"),
                                (
                                    "I / you / we / they",
                                    "I have finished.",
                                    "I haven't finished.",
                                    "Have you finished?",
                                ),
                                (
                                    "he / she / it",
                                    "She has finished.",
                                    "She hasn't finished.",
                                    "Has she finished?",
                                ),
                            ),
                            paragraph(
                                ("Has", True),
                                " tylko z he, she, it (i z imionami: Tom has…). Krótkie odpowiedzi powtarzają have/has, bez V3: "
                                "Yes, I have. / No, I haven't. / Yes, she has. / No, she hasn't.",
                            ),
                            heading("Trzecia forma czasownika (V3)"),
                            bullets(
                                "Regularne: + -ed, jak w drugiej formie: work → worked, play → played, stop → stopped (podwojone p).",
                                "Nieregularne – trzecia kolumna tabeli: go – went – gone, see – saw – seen, eat – ate – eaten, write – wrote – written, be – was/were – been.",
                            ),
                            paragraph(
                                "Uwaga: w Present Perfect używamy V3, nie V2: ",
                                ("I have written", True),
                                " (nie: I have wrote).",
                            ),
                            heading("Skróty"),
                            paragraph(
                                "I have → I've, she has → she's, have not → haven't, has not → hasn't. "
                                "W zdaniu She's visited Rome skrót 's oznacza has, bo dalej stoi V3."
                            ),
                        ),
                    ),
                    Image(
                        "v-budowa",
                        "Budowa zdania w Present Perfect",
                        "e1_v_budowa.png",
                        "Schemat trzech rodzajów zdań: twierdzące osoba + have/has + V3, przeczące z haven't/hasn't, pytanie z Have/Has na początku",
                    ),
                    Image(
                        "v-formy",
                        "Trzecia forma czasownika",
                        "e1_v_formy.png",
                        "Tabela form czasowników: regularne work, play, stop i nieregularne go, see, eat, write, be z wyróżnioną kolumną V3",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie nagrania o budowie zdań w Present Perfect i powtórka na końcu. Objaśnienia są po polsku, "
                        "a angielskie przykłady czytają lektorzy z wymową brytyjską. Powtarzaj zdania na głos razem z lektorem."
                    ),
                    Audio(
                        "a-1",
                        "have / has + trzecia forma",
                        "e1_a1_budowa.mp3",
                        (
                            say(
                                "Z",
                                "Cześć! Present Perfect łączy przeszłość z teraźniejszością: mówi o czymś, co się wydarzyło i ma znaczenie teraz. Nie mówimy, kiedy dokładnie to było.",
                            ),
                            say("M", "A jak zbudować takie zdanie?"),
                            say(
                                "Z",
                                "Potrzebujesz słówka",
                                en("have"),
                                "albo",
                                en("has"),
                                "i trzeciej formy czasownika. Posłuchaj:",
                            ),
                            say("EN2", "I have finished my homework."),
                            say(
                                "Z",
                                "Słówko",
                                en("has"),
                                "stawiamy tylko przy osobach",
                                en("he, she, it"),
                                "i przy imionach:",
                                en("She has finished her homework. Tom has finished, too."),
                            ),
                        ),
                        "Budowa zdania: osoba + have/has + trzecia forma czasownika.",
                    ),
                    Audio(
                        "a-2",
                        "Trzecia forma czasownika (V3)",
                        "e1_a2_v3.mp3",
                        (
                            say("M", "A czym jest trzecia forma?"),
                            say(
                                "Z",
                                "Przy czasownikach regularnych dodajesz końcówkę {-ed|e de}, tak jak w drugiej formie:",
                                en("work, worked. Play, played. Stop, stopped."),
                            ),
                            say(
                                "Z",
                                "Przy nieregularnych bierzesz trzecią kolumnę z tabeli czasowników:",
                                en(
                                    "go, went, gone. See, saw, seen. Eat, ate, eaten. Write, wrote, written."
                                ),
                            ),
                            say(
                                "Z",
                                "Uważaj, żeby nie pomylić drugiej formy z trzecią. Mówimy",
                                en("I have written a letter,"),
                                "a nie",
                                en("I have wrote."),
                            ),
                        ),
                        "Czasowniki regularne z -ed i nieregularne z tabeli.",
                    ),
                    Audio(
                        "a-3",
                        "Przeczenia, pytania i skróty",
                        "e1_a3_pytania.mp3",
                        (
                            say("M", "A jak zrobić przeczenie?"),
                            say(
                                "Z",
                                "Dodajesz",
                                en("not"),
                                "i prawie zawsze używasz skrótu:",
                                en2("I haven't seen this film. She hasn't called."),
                            ),
                            say("M", "A pytania?"),
                            say(
                                "Z",
                                "Przestawiasz",
                                en("have"),
                                "albo",
                                en("has"),
                                "przed osobę:",
                                en("Have you finished? Has she called?"),
                                "Krótko odpowiadasz bez trzeciej formy:",
                                en2("Yes, I have. No, she hasn't."),
                            ),
                            say("M", "A skrót", en2("she's"), "to zawsze", en2("she is?")),
                            say(
                                "Z",
                                "Nie. Jeśli dalej stoi trzecia forma, to skrót od",
                                en("has:"),
                                en("She's visited Rome."),
                            ),
                        ),
                        "haven't / hasn't, pytania z Have / Has, krótkie odpowiedzi i skrót 's.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "e1_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. Osoba, potem",
                                en("have"),
                                "albo",
                                en("has,"),
                                "a na końcu trzecia forma czasownika:",
                                en2("I have finished. She has finished."),
                                "Przeczenie:",
                                en2("I haven't finished."),
                                "Pytanie:",
                                en2("Have you finished?"),
                                "Słówko",
                                en("has"),
                                "tylko z",
                                en("he, she, it."),
                                "I zawsze trzecia forma, nie druga:",
                                en2("I have written, not I have wrote."),
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Przygotuj zeszyt i dwa kolorowe długopisy. Każde zdanie zapisz i przeczytaj na głos – "
                                "pisanie i mówienie pomagają zapamiętać."
                            ),
                            ordered(
                                "Zapisz dużymi literami wzór: osoba + have/has + V3. Pod spodem dopisz: has tylko z he, she, it (i z imionami).",
                                "Zrób tabelkę czasowników z trzema kolumnami: forma podstawowa – V2 – V3. Wpisz regularne: work – worked – worked, play – played – played, stop – stopped – stopped, i nieregularne: go – went – gone, see – saw – seen, eat – ate – eaten, write – wrote – written, be – was/were – been. Pokoloruj kolumnę V3.",
                                "Ułóż 3 zdania twierdzące, np. I have finished my homework. She has eaten breakfast. We have seen this film.",
                                "Zamień je na przeczenia, dopisując not w skrócie: I haven't finished… She hasn't eaten… We haven't seen…",
                                "Zamień je na pytania – przestaw have/has na początek: Have you finished…? Has she eaten…?",
                                "Dopisz krótkie odpowiedzi bez V3: Yes, I have. / No, she hasn't.",
                                "Zapisz skróty: I've, you've, she's (= she has, gdy dalej jest V3), haven't, hasn't. Obok zapisz pułapkę: I have written, nie I have wrote.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: budowa zdania",
                        "e1_k_karta.pdf",
                        "Uzupełnianie, przekształcanie i poprawianie zdań w Present Perfect.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Uzupełnij: She ___ finished her homework.",
                    "has",
                    ("have", "is", "was"),
                    "Z he, she, it używamy has: She has finished. Have stoi przy I, you, we, they.",
                ),
                Question(
                    "q2",
                    "Jaka jest trzecia forma (V3) czasownika go?",
                    "gone",
                    ("went", "goed", "going"),
                    "go – went – gone: went to druga forma (Past Simple), a w Present Perfect potrzebna jest trzecia, np. She has gone to school.",
                ),
                Question(
                    "q3",
                    "Uzupełnij przeczenie: They ___ seen this film.",
                    "haven't",
                    ("hasn't", "didn't", "don't"),
                    "Przeczenie w Present Perfect to have not / has not + V3. Przy they – haven't: They haven't seen this film.",
                ),
                Question(
                    "q4",
                    "Uzupełnij pytanie: ___ he eaten breakfast?",
                    "Has",
                    ("Have", "Did", "Is"),
                    "W pytaniu have/has stoi na początku. Przy he – Has: Has he eaten breakfast?",
                ),
                Question(
                    "q5",
                    "Które zdanie jest poprawne?",
                    "I have written a letter.",
                    (
                        "I have wrote a letter.",
                        "I has written a letter.",
                        "I written have a letter.",
                    ),
                    "Potrzebujemy have (przy I) i trzeciej formy write – written. Wrote to druga forma.",
                ),
                Question(
                    "q6",
                    "Have you seen my keys? Wybierz poprawną krótką odpowiedź przeczącą.",
                    "No, I haven't.",
                    ("No, I didn't.", "No, I don't.", "No, I hasn't."),
                    "Krótka odpowiedź powtarza have/has z pytania: Have you…? – No, I haven't. Did i don't należą do innych czasów, a hasn't nie łączy się z I.",
                ),
                Question(
                    "q7",
                    "Co oznacza skrót 's w zdaniu She's visited Rome?",
                    "has",
                    ("is", "was"),
                    "Po skrócie stoi V3 (visited), więc to Present Perfect: She has visited Rome. Gdyby dalej stało np. happy, 's znaczyłoby is.",
                ),
                Question(
                    "q8",
                    "Jaka jest trzecia forma regularnego czasownika play?",
                    "played",
                    ("plaid", "playen", "plays"),
                    "Czasowniki regularne mają V3 z końcówką -ed, taką samą jak V2: play – played – played.",
                ),
            ),
        ),
        # --- 2. ever, never, already, yet -------------------------------------------------------
        Lesson(
            title="ever, never, already, yet",
            outline=doc(
                paragraph(
                    "Poznasz cztery słówka, które często występują w Present Perfect: ever, never, already i yet. "
                    "Dowiesz się, co znaczą, w jakich zdaniach się ich używa i gdzie stoją w zdaniu."
                )
            ),
            conclusions=doc(
                bullets(
                    "ever = kiedykolwiek (w życiu), w pytaniach przed V3: Have you ever been to London?",
                    "never = nigdy, w zdaniu twierdzącym przed V3: I have never eaten sushi. Bez not – po angielsku tylko jedno przeczenie.",
                    "already = już, w zdaniu twierdzącym między have/has a V3: We have already bought the tickets.",
                    "yet na końcu zdania: w pytaniu = już (Have you finished yet?), w przeczeniu = jeszcze (I haven't finished yet).",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Cztery słówka Present Perfect"),
                            table(
                                ("słówko", "znaczenie", "gdzie w zdaniu", "przykład"),
                                (
                                    "ever",
                                    "kiedykolwiek (w życiu)",
                                    "pytanie, przed V3",
                                    "Have you ever been to London?",
                                ),
                                (
                                    "never",
                                    "nigdy",
                                    "zdanie twierdzące, przed V3",
                                    "I have never eaten sushi.",
                                ),
                                (
                                    "already",
                                    "już",
                                    "zdanie twierdzące, między have/has a V3",
                                    "We have already bought the tickets.",
                                ),
                                (
                                    "yet",
                                    "już (pytanie) / jeszcze (przeczenie)",
                                    "na końcu zdania",
                                    "Have you finished yet? I haven't finished yet.",
                                ),
                            ),
                            heading("Pułapki"),
                            bullets(
                                [
                                    ("never", True),
                                    " już jest przeczeniem: I have never seen snow. Błędnie: I haven't never seen snow – po angielsku nie łączymy dwóch przeczeń.",
                                ],
                                [
                                    ("already", True),
                                    " i ",
                                    ("yet", True),
                                    " tłumaczymy jako „już”, ale already stoi w środku zdania twierdzącego, a yet – na końcu pytania.",
                                ],
                                [
                                    ("yet", True),
                                    " w przeczeniu znaczy „jeszcze”: Jeszcze nie jadłem obiadu = I haven't had lunch yet.",
                                ],
                                "Na pytanie z ever często odpowiadamy z never: Have you ever been to Japan? – No, I've never been there.",
                            ),
                        ),
                    ),
                    Image(
                        "v-slowka",
                        "Gdzie stoją ever, never, already i yet",
                        "e2_v_slowka.png",
                        "Cztery przykładowe zdania z zaznaczonym miejscem słówka: ever i never przed V3, already między have a V3, yet na końcu zdania",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie nagrania o słówkach ever, never, already i yet oraz powtórka na końcu. "
                        "Angielskie przykłady czytają lektorzy – powtarzaj je na głos."
                    ),
                    Audio(
                        "a-1",
                        "ever i never",
                        "e2_a1_ever_never.mp3",
                        (
                            say(
                                "Z",
                                "W tej lekcji poznasz cztery słówka, które często towarzyszą Present Perfect:",
                                en("ever, never, already, yet."),
                                "Zaczniemy od dwóch pierwszych.",
                            ),
                            say(
                                "Z",
                                en("Ever"),
                                "znaczy kiedykolwiek, czyli kiedykolwiek w życiu. Używamy go w pytaniach, przed trzecią formą:",
                                en2("Have you ever been to London?"),
                            ),
                            say("M", "Czyli: czy byłeś kiedykolwiek w Londynie?"),
                            say(
                                "Z",
                                "Tak. A gdy odpowiedź brzmi: nigdy, mówimy",
                                en("never."),
                                "Stoi w tym samym miejscu:",
                                en2("I have never been to London. I have never eaten sushi."),
                            ),
                        ),
                        "ever w pytaniach i never w odpowiedziach, przed trzecią formą.",
                    ),
                    Audio(
                        "a-2",
                        "already i yet",
                        "e2_a2_already_yet.mp3",
                        (
                            say("M", "A jak powiedzieć już i jeszcze?"),
                            say(
                                "Z",
                                "Już w zdaniu twierdzącym to",
                                en("already."),
                                "Stoi między",
                                en("have"),
                                "albo",
                                en("has"),
                                "a trzecią formą:",
                                en2("We have already bought the tickets."),
                            ),
                            say("M", "A słówko", en2("yet?")),
                            say(
                                "Z",
                                en("Yet"),
                                "stawiamy na końcu zdania. W pytaniu znaczy już:",
                                en2("Have you finished your homework yet?"),
                                "A w przeczeniu znaczy jeszcze:",
                                en2("I haven't finished yet."),
                                "Czyli: jeszcze nie skończyłem.",
                            ),
                            say(
                                "M",
                                "Czyli",
                                en2("already"),
                                "i",
                                en2("yet"),
                                "to po polsku już, ale stoją w innych miejscach.",
                            ),
                            say(
                                "Z",
                                "Właśnie.",
                                en("Already"),
                                "w środku zdania twierdzącego,",
                                en("yet"),
                                "na końcu pytania albo przeczenia.",
                            ),
                        ),
                        "already w środku zdania twierdzącego, yet na końcu pytań i przeczeń.",
                    ),
                    Audio(
                        "a-3",
                        "Pułapki",
                        "e2_a3_pulapki.mp3",
                        (
                            say(
                                "M",
                                "Po polsku mówię: nigdy nie jadłem. Czy po angielsku też dodaję",
                                en2("not?"),
                            ),
                            say(
                                "Z",
                                "Nie! To częsty błąd.",
                                en("Never"),
                                "już jest przeczeniem. Zdanie",
                                en("I haven't never eaten sushi"),
                                "jest błędne – po angielsku wystarcza jedno przeczenie. Posłuchaj krótkiej rozmowy:",
                            ),
                            say("EN", "Have you ever tried Polish pierogi?"),
                            say("EN2", "No, I've never tried them. Have you made them yet?"),
                            say("EN", "Yes, I've already made twenty!"),
                            say(
                                "Z",
                                "Usłyszałeś wszystkie cztery słówka, a w każdym zdaniu jest najwyżej jedno przeczenie.",
                            ),
                        ),
                        "Jedno przeczenie z never i krótka rozmowa ze wszystkimi czterema słówkami.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "e2_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka.",
                                en("Ever"),
                                "to kiedykolwiek, w pytaniach.",
                                en("Never"),
                                "to nigdy, bez",
                                en("not."),
                                en("Already"),
                                "to już, w środku zdania twierdzącego.",
                                en("Yet"),
                                "stoi na końcu: w pytaniu znaczy już, a w przeczeniu jeszcze:",
                                en2("I haven't finished yet."),
                                "I jeszcze dwa przykłady:",
                                en2(
                                    "We have already bought the tickets. Have you ever been to London?"
                                ),
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Przygotuj cztery małe karteczki (najlepiej samoprzylepne) i zeszyt."
                            ),
                            ordered(
                                "Na karteczkach napisz dużymi literami: ever, never, already, yet. Na odwrocie każdej zapisz znaczenie: kiedykolwiek, nigdy, już, już / jeszcze.",
                                "Zapisz w zeszycie pytanie: Have you been to London? Połóż karteczkę ever przed been i przeczytaj na głos: Have you ever been to London? (ever – w pytaniach, przed V3).",
                                "Zapisz: I have eaten sushi. Połóż never przed eaten: I have never eaten sushi. Zapamiętaj: never już jest przeczeniem – nie dopisuj not (błąd: I haven't never eaten).",
                                "Zapisz: We have bought the tickets. Wsuń already między have a bought: We have already bought the tickets (already – już, w zdaniu twierdzącym).",
                                "Zapisz pytanie: Have you finished your homework? Połóż yet na końcu: … finished your homework yet? – tu yet znaczy „już”.",
                                "Zapisz przeczenie: I haven't finished. Połóż yet na końcu: I haven't finished yet. – tu yet znaczy „jeszcze”.",
                                "Pomieszaj karteczki, wylosuj jedną i ułóż z nią własne zdanie. Powtórz 4 razy i za każdym razem przeczytaj zdanie na głos.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: ever, never, already, yet",
                        "e2_k_karta.pdf",
                        "Wstawianie słówek, układanie zdań, tłumaczenie i mini-wywiad.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Uzupełnij: Have you ___ been to London?",
                    "ever",
                    ("never", "yet", "already"),
                    "Ever (kiedykolwiek) stawiamy w pytaniach o doświadczenia, przed V3: Have you ever been to London?",
                ),
                Question(
                    "q2",
                    "Wybierz poprawne tłumaczenie: Nigdy nie jadłem sushi.",
                    "I have never eaten sushi.",
                    (
                        "I haven't never eaten sushi.",
                        "I have ever eaten sushi.",
                        "I have eaten never sushi.",
                    ),
                    "never = nigdy, stoi przed V3. Ponieważ never już jest przeczeniem, nie dodajemy not – po angielsku jest tylko jedno przeczenie.",
                ),
                Question(
                    "q3",
                    "Uzupełnij: She hasn't finished ___.",
                    "yet",
                    ("already", "ever", "never"),
                    "W przeczeniu yet stoi na końcu zdania i znaczy „jeszcze”: Jeszcze nie skończyła.",
                ),
                Question(
                    "q4",
                    "Które zdanie jest poprawne?",
                    "We have already bought the tickets.",
                    (
                        "We have yet bought the tickets.",
                        "We have ever bought the tickets.",
                        "We have bought already the tickets.",
                    ),
                    "Already (już) w zdaniu twierdzącym stoi między have/has a V3. Yet nie występuje w takich zdaniach twierdzących, a ever – to słówko pytań.",
                ),
                Question(
                    "q5",
                    "Które zdanie jest błędne?",
                    "I haven't never seen snow.",
                    (
                        "I have never seen snow.",
                        "I haven't seen snow yet.",
                        "Have you ever seen snow?",
                    ),
                    "Never już jest przeczeniem, więc nie łączymy go z haven't. Poprawnie: I have never seen snow.",
                ),
                Question(
                    "q6",
                    "Co znaczy pytanie Have you done your homework yet?",
                    "Czy już odrobiłeś lekcje?",
                    (
                        "Czy kiedykolwiek odrobiłeś lekcje?",
                        "Czy nigdy nie odrobiłeś lekcji?",
                        "Czy jeszcze odrabiasz lekcje?",
                    ),
                    "W pytaniu yet na końcu znaczy „już”. Kiedykolwiek to ever, a nigdy – never.",
                ),
                Question(
                    "q7",
                    "Jak powiesz po angielsku: Jeszcze nie jadłem obiadu?",
                    "I haven't had lunch yet.",
                    (
                        "I have already had lunch.",
                        "I have never had lunch.",
                        "I haven't had lunch already.",
                    ),
                    "„Jeszcze nie” to przeczenie haven't + V3 i yet na końcu zdania. Already oznacza „już” i pasuje do zdań twierdzących.",
                ),
                Question(
                    "q8",
                    "Co znaczy słówko ever w pytaniu Have you ever met a famous person?",
                    "kiedykolwiek (w życiu)",
                    ("nigdy", "już", "jeszcze"),
                    "Ever w pytaniach o doświadczenia znaczy „kiedykolwiek”: Czy kiedykolwiek spotkałeś kogoś sławnego?",
                ),
            ),
        ),
        # --- 3. for i since ---------------------------------------------------------------------
        Lesson(
            title="for i since",
            outline=doc(
                paragraph(
                    "Nauczysz się mówić, jak długo coś trwa – od przeszłości aż do teraz. "
                    "Poznasz różnicę między for (przez jaki okres) i since (od kiedy) oraz pytanie How long…?"
                )
            ),
            conclusions=doc(
                bullets(
                    "Present Perfect + for/since opisuje coś, co zaczęło się w przeszłości i trwa do teraz: I have lived here for five years.",
                    "for + okres (ile czasu?): for two days, for a month, for ages.",
                    "since + początek (od kiedy?): since 2019, since Monday, since I was six.",
                    "Polskie „mieszkam tu od pięciu lat” to Present Perfect: I have lived here for five years (nie: I live here for five years). Pytanie: How long have you…?",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Od przeszłości do teraz"),
                            paragraph(
                                "Gdy coś zaczęło się w przeszłości i trwa nadal, po angielsku używamy Present Perfect. "
                                "Po polsku mówimy w czasie teraźniejszym: ",
                                (
                                    "Mieszkam tu od pięciu lat = I have lived here for five years.",
                                    True,
                                ),
                            ),
                            table(
                                ("for – okres (ile czasu?)", "since – początek (od kiedy?)"),
                                ("for five years", "since 2019"),
                                ("for two weeks", "since Monday"),
                                ("for an hour", "since 8 o'clock"),
                                ("for ages", "since I was six"),
                            ),
                            paragraph(
                                "Test: jeśli pasuje pytanie „ile czasu?” – for. Jeśli „od kiedy?” – since. "
                                "Po since może stać całe zdanie w Past Simple: since I was six, since we moved here."
                            ),
                            heading("Pytanie How long…?"),
                            paragraph(
                                "How long have you had this phone? – I've had it for two years."
                            ),
                            heading("Uwaga"),
                            bullets(
                                "Nie mówimy: I live here for five years (brak Present Perfect) ani I have lived here since five years (pięć lat to okres).",
                                "Liczenie: Tom started this job in March. Now it's June. He has had this job for three months (since March).",
                            ),
                        ),
                    ),
                    Image(
                        "v-os",
                        "for i since na osi czasu",
                        "e3_v_for_since.png",
                        "Oś czasu: punkt since March i klamra for three months sięgająca do teraz (June) oraz listy wyrażeń z for i since",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie nagrania o tym, jak mówić, od jak dawna coś trwa – for, since i pytanie How long…? – oraz powtórka na końcu."
                    ),
                    Audio(
                        "a-1",
                        "Od przeszłości do teraz",
                        "e3_a1_do_teraz.mp3",
                        (
                            say(
                                "Z",
                                "Dzisiaj nauczysz się mówić, jak długo coś trwa. Pomogą nam dwa słówka:",
                                en("for"),
                                "i",
                                en("since."),
                            ),
                            say("M", "Po polsku mówię po prostu: mieszkam tu od pięciu lat."),
                            say(
                                "Z",
                                "No właśnie. Po polsku używasz czasu teraźniejszego. Po angielsku mówimy w Present Perfect, bo mieszkanie zaczęło się w przeszłości i trwa do teraz:",
                                en2("I have lived here for five years."),
                            ),
                            say("M", "Czyli nie", en2("I live here for five years?")),
                            say(
                                "Z",
                                "Nie. Gdy coś trwa od przeszłości aż do teraz, zawsze używamy Present Perfect.",
                            ),
                        ),
                        "Present Perfect dla czegoś, co trwa od przeszłości do teraz.",
                    ),
                    Audio(
                        "a-2",
                        "for czy since?",
                        "e3_a2_for_since.mp3",
                        (
                            say(
                                "Z",
                                en("For"),
                                "stawiamy przed okresem, czyli odpowiedzią na pytanie: ile czasu?",
                                en("For five years, for two weeks, for an hour."),
                            ),
                            say(
                                "Z",
                                en("Since"),
                                "stawiamy przed początkiem, czyli odpowiedzią na pytanie: od kiedy?",
                                en("Since 2019, since Monday, since eight o'clock."),
                            ),
                            say(
                                "M",
                                "Czyli pytam siebie: ile czasu? To",
                                en2("for."),
                                "Od kiedy? To",
                                en2("since."),
                            ),
                            say(
                                "Z",
                                "Świetny sposób. Dlatego nie mówimy",
                                en("since five years,"),
                                "bo pięć lat to okres, a nie początek. Po",
                                en("since"),
                                "może też stać całe zdanie:",
                                en2("We have been friends since we were six."),
                            ),
                        ),
                        "for + okres (ile czasu?), since + początek (od kiedy?).",
                    ),
                    Audio(
                        "a-3",
                        "Pytanie How long…?",
                        "e3_a3_how_long.mp3",
                        (
                            say("M", "A jak zapytać, jak długo ktoś coś robi?"),
                            say("Z", "Pytaniem", en("How long?"), "Posłuchaj:"),
                            say("EN", "How long have you had this phone?"),
                            say("EN2", "I've had it for two years."),
                            say(
                                "Z",
                                "Teraz zagadka. Tom zaczął nową pracę w marcu, a teraz jest czerwiec. Jak długo ma tę pracę?",
                            ),
                            say(
                                "M",
                                "Od marca do czerwca to trzy miesiące.",
                                en2("He has had this job for three months."),
                                "Albo:",
                                en2("since March."),
                            ),
                            say(
                                "Z",
                                "Doskonale. Obie odpowiedzi są poprawne:",
                                en("for"),
                                "z okresem,",
                                en("since"),
                                "z początkiem.",
                            ),
                        ),
                        "Pytanie How long have you…? i zagadka z pracą Toma.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "e3_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. Gdy coś trwa od przeszłości do teraz, mówimy w Present Perfect.",
                                en("For"),
                                "to okres, czyli ile czasu:",
                                en("for five years."),
                                en("Since"),
                                "to początek, czyli od kiedy:",
                                en("since Monday."),
                                "Pytamy:",
                                en("How long have you had it?"),
                                "I uważaj:",
                                en("since five years"),
                                "to błąd, bo pięć lat to okres. Poprawnie:",
                                en2("for five years."),
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph("Przygotuj zeszyt, linijkę i dwa kolorowe długopisy."),
                            ordered(
                                "Narysuj linijką poziomą oś czasu. Na prawym końcu napisz NOW (teraz) – niech to będzie czerwiec.",
                                "Nad osią zapisz zasadę: gdy coś zaczęło się w przeszłości i trwa do teraz, używamy Present Perfect (Mieszkam tu od 5 lat = I have lived here for five years).",
                                "Pierwszym kolorem postaw na osi kropkę, podpisz ją March i dopisz since March. Since to początek – odpowiedź na pytanie „od kiedy?”.",
                                "Drugim kolorem narysuj klamrę od March do NOW i podpisz ją for three months. For to okres – odpowiedź na pytanie „ile czasu?”.",
                                "Zrób dwie kolumny: for i since. Rozłóż do nich wyrażenia: five years, 2019, Monday, two weeks, an hour, 8 o'clock, ages, I was six. (for: five years, two weeks, an hour, ages; since: 2019, Monday, 8 o'clock, I was six).",
                                "Zapisz pytanie How long have you had your phone? i odpowiedz na nie na dwa sposoby: z for i z since.",
                                "Zapisz dwa błędy, których unikasz: I live here for five years (brak Present Perfect) oraz since five years (pięć lat to okres).",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: for i since",
                        "e3_k_karta.pdf",
                        "Wybór for lub since, zdania z How long i poprawianie błędów.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Uzupełnij: I have lived here ___ 2019.",
                    "since",
                    ("for", "from", "ago"),
                    "2019 to początek (od kiedy?), a z początkiem używamy since.",
                ),
                Question(
                    "q2",
                    "Uzupełnij: She has known him ___ three years.",
                    "for",
                    ("since", "ago", "from"),
                    "Trzy lata to okres (ile czasu?), więc for: for three years.",
                ),
                Question(
                    "q3",
                    "Które wyrażenie jest poprawne?",
                    "since last summer",
                    ("since three days", "for yesterday", "for 2015"),
                    "Last summer to moment początku, więc since. Three days to okres (for three days), a yesterday i 2015 to punkty w czasie, nie okresy.",
                ),
                Question(
                    "q4",
                    "Jak powiesz po angielsku: Mieszkam w Krakowie od pięciu lat?",
                    "I have lived in Kraków for five years.",
                    (
                        "I live in Kraków for five years.",
                        "I have lived in Kraków since five years.",
                        "I lived in Kraków since five years.",
                    ),
                    "Mieszkanie trwa od przeszłości do teraz, więc Present Perfect (have lived), a pięć lat to okres – for.",
                ),
                Question(
                    "q5",
                    "Które pytanie o czas trwania jest poprawne?",
                    "How long have you had this phone?",
                    (
                        "How long do you have this phone?",
                        "How long you have had this phone?",
                        "When have you had this phone?",
                    ),
                    "Pytamy o coś, co trwa do teraz: How long + have/has + osoba + V3. Have stoi przed osobą, jak w każdym pytaniu.",
                ),
                Question(
                    "q6",
                    "Na jakie pytanie odpowiada wyrażenie z for?",
                    "Ile czasu? (jak długi okres)",
                    ("Od kiedy? (początek)", "Kiedy dokładnie?", "Dlaczego?"),
                    "for + okres: for two weeks, for an hour. Na pytanie „od kiedy?” odpowiada since.",
                ),
                Question(
                    "q7",
                    "Uzupełnij: They have been friends ___ they were six.",
                    "since",
                    ("for", "ago", "from"),
                    "„They were six” to moment początku przyjaźni. Po since może stać całe zdanie w Past Simple.",
                ),
                Question(
                    "q8",
                    "Tom started this job in March. Now it's June. He has had this job ___.",
                    "for three months",
                    ("since three months", "for March", "since June"),
                    "Od marca do czerwca minęły trzy miesiące – to okres, więc for three months. Można też powiedzieć since March.",
                ),
            ),
        ),
        # --- 4. Present Perfect czy Past Simple? ------------------------------------------------
        Lesson(
            title="Present Perfect czy Past Simple?",
            outline=doc(
                paragraph(
                    "Porównasz Present Perfect z Past Simple i nauczysz się wybierać właściwy czas. "
                    "Kluczem jest pytanie: czy podajesz konkretny, zakończony czas wydarzenia?"
                )
            ),
            conclusions=doc(
                bullets(
                    "Past Simple – gdy podajesz zakończony czas: yesterday, last week, in 2019, two years ago. Pytanie When…? zawsze w Past Simple.",
                    "Present Perfect – gdy czas jest nieważny (doświadczenie, skutek teraz) albo okres trwa: ever, never, already, yet, for, since, today, this week, so far.",
                    "Typowa rozmowa: pytanie w Present Perfect (Have you ever been to Italy?), szczegóły w Past Simple (Yes, I went there last summer).",
                    "Błąd: She has visited Paris in 2019. Poprawnie: She visited Paris in 2019.",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Jedno pytanie rozstrzyga"),
                            paragraph(
                                "Czy w zdaniu jest (albo z rozmowy wiadomo) konkretny, zakończony czas? ",
                                ("Tak – Past Simple. Nie – Present Perfect.", True),
                            ),
                            table(
                                ("", "Past Simple", "Present Perfect"),
                                (
                                    "kiedy?",
                                    "zakończony, znany czas",
                                    "czas nieważny albo okres trwa",
                                ),
                                (
                                    "słówka",
                                    "yesterday, last week, in 2019, ago, When…?",
                                    "ever, never, already, yet, for, since, today, this week, so far",
                                ),
                                (
                                    "przykład",
                                    "I lost my keys yesterday.",
                                    "I have lost my keys (and I can't open the door).",
                                ),
                                (
                                    "forma",
                                    "V2: lost, went, saw",
                                    "have/has + V3: have lost, have gone, have seen",
                                ),
                            ),
                            heading("Typowa rozmowa"),
                            paragraph(
                                "Have you ever been to Italy? – Yes, I have. I went there last summer. "
                                "Pytanie o doświadczenie jest w Present Perfect, ale gdy podajemy, kiedy to było (last summer), przechodzimy na Past Simple."
                            ),
                            heading("Pułapki"),
                            bullets(
                                "When did you see that film? – po When zawsze Past Simple (nie: When have you seen…?).",
                                "We moved here two years ago – z ago zawsze Past Simple.",
                                "I have had three cups of tea so far today – dzień trwa, a so far (do tej pory) wymaga Present Perfect.",
                            ),
                        ),
                    ),
                    Image(
                        "v-os",
                        "Present Perfect czy Past Simple – oś czasu",
                        "e4_v_os_czasu.png",
                        "Oś czasu: Past Simple jako zakończony punkt w przeszłości z datą, Present Perfect jako łuk od przeszłości do teraz, pod spodem słówka-sygnały obu czasów",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie nagrania o wyborze między Present Perfect a Past Simple – jedno pytanie, typowa rozmowa i pułapki – oraz powtórka na końcu."
                    ),
                    Audio(
                        "a-1",
                        "Jedno pytanie rozstrzyga",
                        "e4_a1_pytanie.mp3",
                        (
                            say(
                                "Z",
                                "Oba czasy mówią o przeszłości. Jak wybrać? Zadaj sobie jedno pytanie: czy podaję konkretny, zakończony czas? Jeśli tak, to Past Simple:",
                                en2("I lost my keys yesterday."),
                            ),
                            say("M", "A gdy nie mówię, kiedy?"),
                            say(
                                "Z",
                                "Wtedy Present Perfect. Ważny jest skutek teraz:",
                                en2("I have lost my keys. I can't open the door!"),
                            ),
                            say(
                                "Z",
                                "Do Past Simple pasują",
                                en("yesterday, last week, in 2019, two years ago."),
                                "Do Present Perfect:",
                                en("ever, never, already, yet, for, since"),
                                "i",
                                en("so far."),
                            ),
                        ),
                        "Konkretny, zakończony czas – Past Simple; czas nieważny albo okres trwa – Present Perfect.",
                    ),
                    Audio(
                        "a-2",
                        "Typowa rozmowa",
                        "e4_a2_rozmowa.mp3",
                        (
                            say("M", "Słyszałem kiedyś taką rozmowę:"),
                            say("EN2", "Have you ever been to Italy?"),
                            say("EN", "Yes, I have. I went there last summer."),
                            say("M", "Dlaczego czas się zmienia?"),
                            say(
                                "Z",
                                "Najpierw pytamy o doświadczenie w ogóle, bez czasu, więc w Present Perfect. Gdy podajemy, kiedy to było,",
                                en("last summer,"),
                                "przechodzimy na Past Simple. Tak wygląda większość rozmów o doświadczeniach.",
                            ),
                            say("M", "Czyli najpierw pytam ogólnie, a potem podaję szczegóły."),
                            say("Z", "Tak. Posłuchaj jeszcze jednej pary:"),
                            say("EN2", "Have you seen this film?"),
                            say("EN", "Yes, I have. I saw it last week."),
                        ),
                        "Pytanie w Present Perfect, szczegóły w Past Simple.",
                    ),
                    Audio(
                        "a-3",
                        "Pułapki",
                        "e4_a3_pulapki.mp3",
                        (
                            say("M", "A pytanie zaczynające się od", en2("When?")),
                            say(
                                "Z",
                                en("When"),
                                "pyta o konkretny czas, więc zawsze łączy się z Past Simple:",
                                en("When did you see that film?"),
                                "Nie mówimy",
                                en("When have you seen it?"),
                            ),
                            say(
                                "M",
                                "Czyli zdanie",
                                en2("She has visited Paris in 2019"),
                                "jest błędne?",
                            ),
                            say(
                                "Z",
                                "Tak, bo rok {2019|dwa tysiące dziewiętnasty} to zakończony czas. Poprawnie:",
                                en("She visited Paris in 2019."),
                                "Tak samo ze słówkiem",
                                en("ago:"),
                                en2("We moved here two years ago."),
                            ),
                            say(
                                "M",
                                "Czyli",
                                en2("ago,"),
                                en2("yesterday"),
                                "albo rok w zdaniu to sygnał: Past Simple.",
                            ),
                        ),
                        "When…?, ago i rok w zdaniu – zawsze Past Simple.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "e4_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. Konkretny, zakończony czas, na przykład",
                                en("yesterday"),
                                "albo",
                                en("two years ago,"),
                                "to Past Simple. Brak czasu, skutek teraz albo okres, który trwa, to Present Perfect. Po",
                                en("When"),
                                "zawsze Past Simple. W rozmowie: pytanie w Present Perfect, szczegóły w Past Simple.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Przygotuj zeszyt i dwa kolory. Zrobisz własną ściągę i posortujesz zdania."
                            ),
                            ordered(
                                "Podziel stronę na dwie kolumny: Past Simple (V2) i Present Perfect (have/has + V3).",
                                "Nad kolumnami zapisz pytanie-klucz: Czy podaję konkretny, zakończony czas? Tak → Past Simple, nie → Present Perfect.",
                                "Wpisz słówka-podpowiedzi. Past Simple: yesterday, last week, in 2019, two years ago, When…? Present Perfect: ever, never, already, yet, for, since, today, this week, so far.",
                                "Przepisz do właściwej kolumny: I lost my keys yesterday. / I have lost my keys – I can't open the door. / We moved here two years ago. / I have had three cups of tea so far today.",
                                "Zapisz rozmowę: Have you ever been to Italy? – Yes, I have. I went there last summer. Zaznacz kolorem, gdzie zmienia się czas i dlaczego (last summer = konkretny czas).",
                                "Zapisz zasadę z When: When did you see that film? (nie: When have you seen…?).",
                                "Popraw błędne zdanie: She has visited Paris in 2019 → She visited Paris in 2019.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: Present Perfect czy Past Simple?",
                        "e4_k_karta.pdf",
                        "Wybór czasu, uzupełnianie dialogu i poprawianie błędów.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Uzupełnij: I ___ my keys yesterday.",
                    "lost",
                    ("have lost", "has lost", "lose"),
                    "Yesterday to konkretny, zakończony czas, więc Past Simple: I lost my keys yesterday.",
                ),
                Question(
                    "q2",
                    "Uzupełnij: I ___ my keys. I can't open the door!",
                    "have lost",
                    ("has lost", "losed", "lose"),
                    "Nie podajemy czasu, a ważny jest skutek teraz (nie mogę otworzyć drzwi), więc Present Perfect: I have lost.",
                ),
                Question(
                    "q3",
                    "Uzupełnij pytanie: When ___ you see that film?",
                    "did",
                    ("have", "has", "do"),
                    "When pyta o konkretny czas, więc łączy się z Past Simple: When did you see that film?",
                ),
                Question(
                    "q4",
                    "Które słówka zwykle wskazują na Past Simple?",
                    "yesterday, last week, two years ago",
                    ("ever, never, yet", "for, since, already", "so far, this week, today"),
                    "Yesterday, last week i ago określają zakończony czas – to sygnały Past Simple. Ever, never, yet, for, since, already i so far pasują do Present Perfect.",
                ),
                Question(
                    "q5",
                    "Have you ever been to Italy? – Yes, I have. I went there last summer. Dlaczego w odpowiedzi jest went?",
                    "Bo podano konkretny, zakończony czas: last summer.",
                    (
                        "Bo pytanie było w Present Perfect.",
                        "Bo went to trzecia forma czasownika go.",
                        "Bo po Yes, I have zawsze jest Past Simple.",
                    ),
                    "Pytanie o doświadczenie jest w Present Perfect, ale szczegół z określeniem czasu (last summer) mówimy w Past Simple. Went to druga forma; trzecia to gone.",
                ),
                Question(
                    "q6",
                    "Które zdanie jest poprawne?",
                    "She visited Paris in 2019.",
                    (
                        "She has visited Paris in 2019.",
                        "She has visit Paris in 2019.",
                        "She visit Paris in 2019.",
                    ),
                    "In 2019 to zakończony czas, więc Past Simple (V2: visited). Present Perfect nie łączy się z konkretną datą.",
                ),
                Question(
                    "q7",
                    "Uzupełnij: I ___ three cups of tea so far today.",
                    "have had",
                    ("had", "has had", "have have"),
                    "So far (do tej pory) oznacza, że dzień jeszcze trwa i liczba może wzrosnąć – to Present Perfect: I have had.",
                ),
                Question(
                    "q8",
                    "Które zdanie jest poprawne?",
                    "We moved here two years ago.",
                    (
                        "We have moved here two years ago.",
                        "We have moved here since two years.",
                        "We move here two years ago.",
                    ),
                    "Ago (temu) wskazuje zakończony moment w przeszłości, więc zawsze łączy się z Past Simple.",
                ),
            ),
        ),
    ),
)


# =================================================================================================
# Programowanie: pętle w Pythonie
# =================================================================================================

PYTHON = Course(
    code="p",
    title="Programowanie: pętle w Pythonie",
    description=(
        "Pętle w Pythonie dla początkujących (klasy 6–8): pętla for po listach i napisach, funkcja range(), "
        "pętla while oraz instrukcje break i continue. Każdą lekcję przerobisz ze schematami i kodem, "
        "z nagraniem albo przez samodzielne pisanie i uruchamianie programów z karty zadań. "
        "Przyda się dowolny edytor Pythona, np. IDLE. Quiz po lekcji otwiera następną."
    ),
    introduction=doc(
        paragraph(
            "Pętla pozwala powtórzyć instrukcje wiele razy bez przepisywania kodu. Dzięki niej program wypisze "
            "tabliczkę mnożenia, policzy sumę stu liczb albo będzie pytał o hasło, dopóki nie wpiszesz poprawnego."
        ),
        paragraph(
            "Kurs ma cztery lekcje: pętla for, funkcja range(), pętla while oraz break i continue. "
            "Po każdej lekcji rozwiązujesz quiz z 5 pytań – ",
            ("zaliczenie (co najmniej 4 dobre odpowiedzi) otwiera następną lekcję.", True),
        ),
        paragraph(
            "Przygotuj komputer z Pythonem 3 (np. z edytorem IDLE) albo stronę do uruchamiania kodu Pythona w przeglądarce. "
            "Kod przepisuj samodzielnie – w Pythonie wcięcia mają znaczenie."
        ),
    ),
    summary=doc(
        bullets(
            "`for` przechodzi po kolejnych elementach listy, napisu albo `range()`; zmienna pętli w każdym obrocie przyjmuje następny element.",
            "`range(start, stop, krok)` daje liczby od start do stop − 1; `range(n)` – n liczb od 0.",
            "`while` powtarza, dopóki warunek jest prawdziwy – w ciele zmieniaj zmienną z warunku, inaczej pętla nie skończy się sama.",
            "`break` kończy pętlę natychmiast, `continue` pomija resztę bieżącego obrotu; instrukcje należące do pętli rozpoznajemy po wcięciu.",
        ),
        paragraph(
            "Co dalej: połącz pętle z warunkami w małej grze – np. zgadywanie liczby z while True i break."
        ),
    ),
    lessons=(
        # --- 1. Pętla for -----------------------------------------------------------------------
        Lesson(
            title="Pętla for",
            outline=doc(
                paragraph(
                    "Poznasz pętlę for, która powtarza instrukcje dla każdego elementu listy albo napisu. "
                    "Dowiesz się, jak ją zapisać (dwukropek i wcięcie) i jak policzyć sumę liczb z listy."
                )
            ),
            conclusions=doc(
                bullets(
                    "`for element in sekwencja:` – powtarza wcięte instrukcje dla każdego elementu; zmienna pętli przyjmuje po kolei wszystkie wartości.",
                    "Ciało pętli to linie z wcięciem (4 spacje) pod linią zakończoną dwukropkiem. Linia bez wcięcia wykona się raz, po pętli.",
                    'Pętla po napisie przechodzi po literach: `for litera in "kot":` wypisze k, o, t.',
                    "Sumowanie: `suma = 0` przed pętlą, w pętli `suma = suma + liczba` (dla `[2, 4, 6]` wyjdzie 12).",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Powtórz dla każdego elementu"),
                            paragraph(
                                "Pętla for wykonuje te same instrukcje dla każdego elementu listy albo napisu. Zapis: ",
                                mono("for zmienna in sekwencja:"),
                                " – na końcu linii dwukropek, a instrukcje do powtarzania piszemy niżej z wcięciem (4 spacje).",
                            ),
                            code_block(
                                'owoce = ["jabłko", "gruszka", "śliwka"]',
                                "for owoc in owoce:",
                                "    print(owoc)",
                            ),
                            paragraph(
                                'W pierwszym obrocie `owoc = "jabłko"`, w drugim `"gruszka"`, w trzecim `"śliwka"` – program wypisze trzy linie. '
                                'Pętla po napisie przechodzi po literach: `for litera in "kot": print(litera)` wypisze k, o i t, każdą w osobnej linii.'
                            ),
                            heading("Wcięcie decyduje"),
                            paragraph(
                                "Python rozpoznaje ciało pętli po wcięciu. Linia bez wcięcia pod pętlą wykona się tylko raz – po zakończeniu pętli. "
                                "Bez dwukropka albo bez wcięcia Python zgłosi błąd."
                            ),
                            heading("Suma liczb z listy"),
                            paragraph(
                                "Przed pętlą ustaw `suma = 0`, a w pętli dodawaj kolejne liczby:"
                            ),
                            code_block(
                                "suma = 0",
                                "for liczba in [2, 4, 6]:",
                                "    suma = suma + liczba",
                                "print(suma)",
                            ),
                            paragraph(
                                "Po kolejnych obrotach `suma` wynosi 2, 6, 12. Program wypisze 12."
                            ),
                        ),
                    ),
                    Image(
                        "v-schemat",
                        "Jak działa pętla for",
                        "p1_v_schemat.png",
                        "Schemat blokowy pętli for: czy jest kolejny element? Tak – zmienna dostaje element i wykonuje się ciało pętli; nie – koniec pętli",
                    ),
                    Image(
                        "v-kod",
                        "Suma krok po kroku",
                        "p1_v_kod.png",
                        "Kod sumujący listę [2, 4, 6] i tabela obrotów: wartość zmiennej liczba i sumy po każdym obrocie, wynik 12",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie rozmowy o pętli for – zapis, wcięcia i sumowanie – a na końcu powtórka. "
                        "Po wysłuchaniu przepisz przykład z owocami i uruchom go."
                    ),
                    Audio(
                        "a-1",
                        "Jak zapisać pętlę for",
                        "p1_a1_zapis.mp3",
                        (
                            say(
                                "Z",
                                "Marek, masz wypisać na ekranie sto imion. Pisałbyś sto razy {print|print}?",
                            ),
                            say("M", "Wolałbym nie."),
                            say(
                                "Z",
                                "Do tego służy pętla {for|for}: dla każdego elementu listy wykonuje te same instrukcje. Mamy listę owoce: jabłko, gruszka i śliwka. "
                                "Piszemy {for owoc in owoce:|for owoc in owoce, a na końcu dwukropek}. W następnej linii, z wcięciem na cztery spacje: {print(owoc)|print, a w nawiasie owoc}.",
                            ),
                            say("M", "I co się stanie?"),
                            say(
                                "Z",
                                "W pierwszym obrocie zmienna {owoc|owoc} ma wartość jabłko, w drugim gruszka, a w trzecim śliwka. Elementy się skończyły, więc pętla też.",
                            ),
                        ),
                        "Zapis for owoc in owoce: i to, co dzieje się w kolejnych obrotach.",
                    ),
                    Audio(
                        "a-2",
                        "Wcięcie decyduje",
                        "p1_a2_wciecie.mp3",
                        (
                            say("M", "Po czym Python poznaje, co jest w środku pętli?"),
                            say(
                                "Z",
                                "Po wcięciu. Linie przesunięte w prawo pod linią z dwukropkiem to ciało pętli. Linia bez wcięcia wykona się tylko raz, kiedy pętla się skończy.",
                            ),
                            say("M", "A jeśli zapomnę dwukropka?"),
                            say(
                                "Z",
                                "To częsty błąd. Bez dwukropka albo bez wcięcia Python zgłosi błąd i nie uruchomi programu. "
                                'Pętla przejdzie też po napisie: {for litera in "kot":|for litera in kot} wypisze {k, o i t|ka, o i te}, każdą literę w osobnej linii.',
                            ),
                            say("M", "Czyli wcięcie to nie ozdoba, tylko część programu."),
                        ),
                        "Ciało pętli, częsty błąd i pętla po literach napisu.",
                    ),
                    Audio(
                        "a-3",
                        "Przykład: suma liczb z listy",
                        "p1_a3_suma.mp3",
                        (
                            say(
                                "Z",
                                "Policzmy sumę liczb {2, 4 i 6|dwa, cztery i sześć}. Przed pętlą piszemy {suma = 0|suma równa się zero}. "
                                "Potem {for liczba in [2, 4, 6]:|for liczba in lista, dwukropek}, a w środku {suma = suma + liczba|suma równa się suma plus liczba}.",
                            ),
                            say(
                                "M",
                                "Prześledzę to. Najpierw suma to {0|zero}. Po pierwszym obrocie {2|dwa}, potem {6|sześć}, a na końcu {12|dwanaście}.",
                            ),
                            say(
                                "Z",
                                "Świetnie. Gdy po pętli, bez wcięcia, napiszesz {print(suma)|print suma}, program wypisze {12|dwanaście}. Tylko raz, bo ta linia nie należy do pętli.",
                            ),
                        ),
                        "Sumowanie listy [2, 4, 6] obrót po obrocie.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "p1_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. Pętla {for|for} wykonuje ciało dla każdego elementu listy albo napisu. Na końcu pierwszej linii stawiamy dwukropek, "
                                "a ciało piszemy z wcięciem na cztery spacje. Zmienna pętli po kolei przyjmuje każdy element. Linia bez wcięcia wykona się raz, po pętli. "
                                "Sumowanie: {suma = 0|suma równa się zero} przed pętlą, a w pętli {suma = suma + liczba|suma równa się suma plus liczba}.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Otwórz edytor Pythona (np. IDLE). Każdy program najpierw przepisz, potem zapisz na kartce, "
                                "co według Ciebie wypisze, a na końcu uruchom i porównaj."
                            ),
                            ordered(
                                'Wpisz listę: `owoce = ["jabłko", "gruszka", "śliwka"]`.',
                                "Pod spodem napisz linię pętli z dwukropkiem na końcu: `for owoc in owoce:`",
                                "W następnej linii zrób wcięcie (4 spacje albo klawisz Tab) i wpisz `print(owoc)`. Wcięte linie to ciało pętli – wykonują się dla każdego elementu.",
                                "Zapisz przewidywanie i uruchom program. Każdy owoc pojawi się w osobnej linii: zmienna owoc przyjmuje po kolei wartość każdego elementu.",
                                'Dopisz na końcu linię bez wcięcia: `print("koniec")`. Uruchom – słowo koniec pojawi się tylko raz, po pętli.',
                                "Usuń dwukropek z linii `for` i uruchom program. Przeczytaj komunikat błędu (`SyntaxError`), a potem przywróć dwukropek.",
                                'Napisz pętlę po napisie: `for litera in "kot":` i w ciele `print(litera)`. Program wypisze k, o, t w osobnych liniach.',
                                "Policz sumę: `suma = 0`, potem `for liczba in [2, 4, 6]:` i w ciele `suma = suma + liczba`. Po pętli (bez wcięcia) `print(suma)`. Przed uruchomieniem zapisz w tabelce wartość sumy po każdym obrocie: 2, 6, 12.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: pętla for",
                        "p1_k_karta.pdf",
                        "Przewidywanie wyniku, tabela obrotów i własne programy z pętlą for.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    'Co wypisze program: for litera in "kot": print(litera)',
                    "k, o i t – każdą literę w osobnej linii",
                    (
                        "kot – raz, w jednej linii",
                        "kot kot kot – trzy razy całe słowo",
                        "nic, bo pętla for działa tylko z listą",
                    ),
                    "Pętla po napisie przechodzi po jego znakach. Zmienna litera przyjmuje kolejno k, o, t, a print wypisuje każdą w nowej linii.",
                ),
                Question(
                    "q2",
                    "Ile razy wykona się print(x) w pętli for x in [4, 8, 15]: print(x)?",
                    "3 razy",
                    ("15 razy", "4 razy", "1 raz"),
                    "Lista ma trzy elementy, więc pętla ma trzy obroty – po jednym na każdy element. Same wartości 4, 8 i 15 nie wpływają na liczbę obrotów.",
                ),
                Question(
                    "q3",
                    "Który zapis początku pętli jest poprawny?",
                    "for owoc in owoce:",
                    ("for owoc in owoce", "for (owoc in owoce):", "for owoc = owoce:"),
                    "Poprawnie: słowo for, nazwa zmiennej, słowo in, sekwencja i dwukropek na końcu. Bez dwukropka Python zgłosi błąd składni.",
                ),
                Question(
                    "q4",
                    "Po czym Python rozpoznaje, które instrukcje należą do ciała pętli?",
                    "po wcięciu pod linią z dwukropkiem",
                    (
                        "po nawiasach klamrowych { }",
                        "po średniku na końcu linii",
                        "po pustej linii za pętlą",
                    ),
                    "W Pythonie ciało pętli to linie z wcięciem (zwykle 4 spacje) pod linią for zakończoną dwukropkiem.",
                ),
                Question(
                    "q5",
                    "Zmienna suma ma wartość 0. Potem wykonuje się pętla for n in [2, 4, 6]: suma = suma + n. Ile wynosi suma po pętli?",
                    "12",
                    ("6", "0", "246"),
                    "Po kolejnych obrotach: 0 + 2 = 2, 2 + 4 = 6, 6 + 6 = 12.",
                ),
                Question(
                    "q6",
                    'Program ma pętlę for i in ["a", "b"]: z wciętym print(i), a pod nią linię bez wcięcia print("koniec"). Ile razy pojawi się słowo koniec?',
                    "1 raz",
                    ("2 razy", "ani razu", "3 razy"),
                    "Linia bez wcięcia nie należy do pętli, więc wykona się raz – po zakończeniu pętli.",
                ),
                Question(
                    "q7",
                    'Jaką wartość ma zmienna owoc w drugim obrocie pętli for owoc in ["jabłko", "gruszka", "śliwka"]?',
                    "gruszka",
                    ("jabłko", "śliwka", "cała lista"),
                    "Zmienna pętli przyjmuje po kolei każdy element: w pierwszym obrocie jabłko, w drugim gruszka, w trzecim śliwka.",
                ),
                Question(
                    "q8",
                    "Co wypisze for x in [1, 2, 3]: print(x * 2)?",
                    "2, 4, 6 (każdą liczbę w osobnej linii)",
                    ("1, 2, 3", "6", "2, 2, 2"),
                    "W każdym obrocie x to kolejny element, a print wypisuje x · 2: 1 · 2 = 2, 2 · 2 = 4, 3 · 2 = 6.",
                ),
            ),
        ),
        # --- 2. range() -------------------------------------------------------------------------
        Lesson(
            title="range()",
            outline=doc(
                paragraph(
                    "Poznasz funkcję range(), która tworzy ciąg liczb dla pętli for. Nauczysz się powtarzać instrukcje "
                    "zadaną liczbę razy, liczyć od dowolnej liczby, z krokiem i w dół."
                )
            ),
            conclusions=doc(
                bullets(
                    "`range(n)` daje n liczb: 0, 1, …, n − 1 (`range(4)` → 0, 1, 2, 3), więc `for i in range(n):` powtarza n razy.",
                    "`range(start, stop)` zaczyna od start i kończy przed stop: `range(2, 6)` → 2, 3, 4, 5. Liczby od 1 do 10: `range(1, 11)`.",
                    "Trzecia liczba to krok: `range(0, 10, 3)` → 0, 3, 6, 9; `range(2, 21, 2)` – parzyste od 2 do 20.",
                    "Ujemny krok liczy w dół: `range(5, 0, -1)` → 5, 4, 3, 2, 1.",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("range() – ciąg liczb dla pętli"),
                            paragraph(
                                "Funkcja `range()` tworzy ciąg liczb całkowitych. Razem z for pozwala powtórzyć instrukcje określoną liczbę razy: ",
                                mono("for i in range(5):"),
                                " wykona ciało 5 razy, a `i` przyjmie wartości 0, 1, 2, 3, 4.",
                            ),
                            table(
                                ("zapis", "liczby", "zasada"),
                                ("`range(4)`", "0, 1, 2, 3", "od 0, 4 liczby, bez 4"),
                                ("`range(2, 6)`", "2, 3, 4, 5", "od start do stop − 1"),
                                ("`range(1, 11)`", "1, 2, …, 10", "liczby od 1 do 10"),
                                ("`range(0, 10, 3)`", "0, 3, 6, 9", "krok 3"),
                                ("`range(2, 21, 2)`", "2, 4, …, 20", "parzyste od 2 do 20"),
                                ("`range(5, 0, -1)`", "5, 4, 3, 2, 1", "w dół (krok ujemny)"),
                            ),
                            paragraph(
                                (
                                    "Najważniejsza zasada: liczba stop nigdy nie należy do ciągu.",
                                    True,
                                ),
                                " Dlatego liczby od 1 do 10 to `range(1, 11)`.",
                            ),
                            heading("Przykład: suma"),
                            code_block(
                                "suma = 0",
                                "for i in range(1, 5):",
                                "    suma = suma + i",
                                "print(suma)",
                            ),
                            paragraph(
                                "`i` przyjmuje 1, 2, 3, 4, więc `suma` = 1 + 2 + 3 + 4 = 10. "
                                "Aby zobaczyć wszystkie liczby z `range` naraz, wpisz `print(list(range(2, 6)))`."
                            ),
                        ),
                    ),
                    Image(
                        "v-range",
                        "Co daje range()",
                        "p2_v_range.png",
                        "Osie liczbowe od 0 do 10 z zaznaczonymi liczbami dla range(4), range(2, 6), range(0, 10, 3) i range(5, 0, -1); liczba stop przekreślona",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie rozmowy o funkcji range() – powtarzanie n razy, start, stop i krok, przykład z sumą – a na końcu powtórka."
                    ),
                    Audio(
                        "a-1",
                        "range(n) – powtórz n razy",
                        "p2_a1_powtorz.mp3",
                        (
                            say(
                                "Z",
                                "Pętla {for|for} przechodziła po liście. A co, jeśli chcesz coś powtórzyć na przykład pięć razy?",
                            ),
                            say("M", "Mogę zrobić listę z pięcioma elementami."),
                            say(
                                "Z",
                                "Wygodniej użyć funkcji {range|rejndż}. Piszesz {for i in range(5):|for i in rejndż, w nawiasie pięć, dwukropek}. Ciało pętli wykona się pięć razy.",
                            ),
                            say("M", "A jakie wartości ma wtedy {i|i}?"),
                            say(
                                "Z",
                                "Tu jest haczyk: {0, 1, 2, 3, 4|zero, jeden, dwa, trzy, cztery}. Pięć liczb, ale bez piątki. W Pythonie liczba końcowa nigdy nie należy do ciągu.",
                            ),
                        ),
                        "for i in range(5): – pięć obrotów, i od 0 do 4.",
                    ),
                    Audio(
                        "a-2",
                        "Start, stop i krok",
                        "p2_a2_krok.mp3",
                        (
                            say(
                                "Z",
                                "Można też podać początek. {range(2, 6)|Rejndż od dwóch do sześciu} daje {2, 3, 4 i 5|dwa, trzy, cztery i pięć}.",
                            ),
                            say(
                                "M",
                                "Czyli liczby od jednego do dziesięciu to {range(1, 11)|rejndż od jednego do jedenastu}.",
                            ),
                            say(
                                "Z",
                                "Właśnie. Trzecia liczba to krok. {range(0, 10, 3)|Rejndż od zera do dziesięciu z krokiem trzy} daje {0, 3, 6 i 9|zero, trzy, sześć i dziewięć}. "
                                "Krok może być ujemny, wtedy liczymy w dół: {range(5, 0, -1)|rejndż od pięciu do zera z krokiem minus jeden} daje {5, 4, 3, 2, 1|pięć, cztery, trzy, dwa, jeden}.",
                            ),
                            say("M", "Jak odliczanie przed startem rakiety."),
                        ),
                        "range(start, stop, krok) i liczenie w dół.",
                    ),
                    Audio(
                        "a-3",
                        "Przykład: suma",
                        "p2_a3_suma.mp3",
                        (
                            say(
                                "Z",
                                "Policzmy sumę. Na początku {suma = 0|suma równa się zero}, potem {for i in range(1, 5):|for i in rejndż od jednego do pięciu}, "
                                "a w środku {suma = suma + i|suma równa się suma plus i}.",
                            ),
                            say(
                                "M",
                                "{range(1, 5)|Rejndż od jednego do pięciu} to {1, 2, 3 i 4|jeden, dwa, trzy i cztery}. Razem {10|dziesięć}.",
                            ),
                            say(
                                "Z",
                                "Świetnie. Liczby z {range|rejndż} zobaczysz naraz, gdy napiszesz {print(list(range(2, 6)))|print, a w środku list z rejndż od dwóch do sześciu}. "
                                "Częsty błąd to oczekiwanie, że wypisze się też szóstka.",
                            ),
                            say(
                                "M",
                                "A przecież szóstka to koniec zakresu, a koniec nigdy nie jest wliczany.",
                            ),
                        ),
                        "Suma 1 + 2 + 3 + 4 z range(1, 5) i podgląd liczb przez list().",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "p2_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. {range(n)|Rejndż od en} daje {n|en} liczb od zera do {n − 1|en minus jeden}, więc {for i in range(n):|for i in rejndż en} powtarza ciało {n|en} razy. "
                                "Liczba końcowa nigdy nie jest wliczana, dlatego od jednego do dziesięciu to {range(1, 11)|rejndż od jednego do jedenastu}. "
                                "Trzecia liczba to krok, a ujemny krok liczy w dół. Na przykład {range(4)|rejndż cztery} daje {0, 1, 2, 3|zero, jeden, dwa, trzy}.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Otwórz edytor Pythona. Najpierw zapisuj przewidywania na kartce, potem uruchamiaj kod."
                            ),
                            ordered(
                                "Wpisz i uruchom: `for i in range(5):` z wciętym `print(i)`. Policz linie wyniku: 5 liczb, od 0 do 4. Zapisz: `range(n)` daje n liczb od 0 do n − 1.",
                                "Zmień na `range(2, 6)` i uruchom. Wyjdzie 2, 3, 4, 5 – zapisz: koniec (stop) nie jest wliczany.",
                                "Spróbuj wypisać liczby od 1 do 10. Jeśli wyszło tylko do 9, popraw na `range(1, 11)`.",
                                "Dodaj krok: `range(0, 10, 3)`. Zanim uruchomisz, zapisz przewidywanie (0, 3, 6, 9).",
                                "Wypisz liczby parzyste od 2 do 20: `range(2, 21, 2)`.",
                                "Zrób odliczanie: `range(5, 0, -1)` – wyjdzie 5, 4, 3, 2, 1. Ujemny krok liczy w dół.",
                                "Napisz program sumy: `suma = 0`, `for i in range(1, 5):` i w ciele `suma = suma + i`, a po pętli `print(suma)`. Przed uruchomieniem policz na kartce: 1 + 2 + 3 + 4 = 10.",
                                "Sprawdzaj ciągi poleceniem `print(list(range(…)))` – pokazuje wszystkie liczby naraz.",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: range()",
                        "p2_k_karta.pdf",
                        "Wypisywanie ciągów z range, dobieranie zapisu i własne programy.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Jakie liczby daje range(4)?",
                    "0, 1, 2, 3",
                    ("1, 2, 3, 4", "0, 1, 2, 3, 4", "tylko 4"),
                    "range(n) zaczyna od 0 i daje n liczb, kończąc na n − 1. Dla 4: 0, 1, 2, 3 – sama 4 nie jest wliczana.",
                ),
                Question(
                    "q2",
                    "Jakie liczby daje range(2, 6)?",
                    "2, 3, 4, 5",
                    ("2, 3, 4, 5, 6", "3, 4, 5, 6", "2 i 6"),
                    "Ciąg zaczyna się od start (2) i kończy przed stop (6), więc ostatnia liczba to 5.",
                ),
                Question(
                    "q3",
                    "Jakie liczby daje range(0, 10, 3)?",
                    "0, 3, 6, 9",
                    ("3, 6, 9", "0, 3, 6, 9, 12", "0, 3, 6"),
                    "Start 0, krok 3: 0, 3, 6, 9. Następna byłaby 12, ale nie jest mniejsza od 10.",
                ),
                Question(
                    "q4",
                    'Ile razy wypisze się słowo Hej w pętli for i in range(7): print("Hej")?',
                    "7 razy",
                    ("6 razy", "8 razy", "ani razu"),
                    "range(7) daje 7 liczb (0–6), więc pętla ma 7 obrotów.",
                ),
                Question(
                    "q5",
                    "Którego zapisu użyjesz, żeby pętla przeszła po liczbach od 1 do 10?",
                    "range(1, 11)",
                    ("range(1, 10)", "range(10)", "range(0, 10)"),
                    "Liczba stop nie jest wliczana, więc żeby dostać 10, stop musi wynosić 11. range(1, 10) kończy się na 9, a range(10) daje 0–9.",
                ),
                Question(
                    "q6",
                    "Jakie liczby daje range(5, 0, -1)?",
                    "5, 4, 3, 2, 1",
                    ("5, 4, 3, 2, 1, 0", "0, 1, 2, 3, 4, 5", "żadnych – ciąg jest pusty"),
                    "Krok −1 liczy w dół od 5. Liczba stop (0) nie jest wliczana, więc ostatnia to 1.",
                ),
                Question(
                    "q7",
                    "Który zapis da wszystkie liczby parzyste od 2 do 20?",
                    "range(2, 21, 2)",
                    ("range(2, 20, 2)", "range(0, 20, 2)", "range(2, 20)"),
                    "Start 2, krok 2 i stop większy od 20 (21), żeby 20 się zmieściło. range(2, 20, 2) kończy się na 18.",
                ),
                Question(
                    "q8",
                    "Zmienna suma ma wartość 0. Potem wykonuje się pętla for i in range(1, 5): suma = suma + i. Ile wynosi suma po pętli?",
                    "10",
                    ("15", "4", "5"),
                    "range(1, 5) daje 1, 2, 3, 4, więc suma = 1 + 2 + 3 + 4 = 10. Piątka nie jest wliczana.",
                ),
            ),
        ),
        # --- 3. Pętla while ---------------------------------------------------------------------
        Lesson(
            title="Pętla while",
            outline=doc(
                paragraph(
                    "Poznasz pętlę while, która powtarza instrukcje, dopóki warunek jest prawdziwy. "
                    "Dowiesz się, jak uniknąć pętli nieskończonej i kiedy while jest lepsza od for."
                )
            ),
            conclusions=doc(
                bullets(
                    "`while warunek:` – przed każdym obrotem Python sprawdza warunek; gdy jest fałszywy, pętla się kończy (czasem już przed pierwszym obrotem).",
                    "W ciele trzeba zmieniać zmienną z warunku (np. `x = x + 1`), inaczej powstanie pętla nieskończona.",
                    "`while` wybieramy, gdy nie wiemy z góry, ile będzie powtórzeń: pytanie o hasło, podwajanie liczby, aż przekroczy 100.",
                    "`x = 1`, potem `while x < 4:` z wciętymi `print(x)` i `x = x + 1` – wypisze 1, 2, 3.",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("Powtarzaj, dopóki…"),
                            paragraph(
                                "Pętla `while` powtarza swoje ciało, ",
                                ("dopóki warunek jest prawdziwy", True),
                                ". Przed każdym obrotem Python sprawdza warunek: prawdziwy – wykonuje ciało; fałszywy – kończy pętlę i przechodzi dalej.",
                            ),
                            code_block(
                                "licznik = 1",
                                "while licznik <= 5:",
                                "    print(licznik)",
                                "    licznik = licznik + 1",
                            ),
                            paragraph(
                                "Program wypisze 1, 2, 3, 4, 5. Po piątym obrocie `licznik = 6`, warunek `6 <= 5` jest fałszywy i pętla się kończy."
                            ),
                            heading("Uwaga na pętlę nieskończoną"),
                            paragraph(
                                "Jeśli w ciele nie zmienisz zmiennej z warunku, warunek będzie zawsze prawdziwy i pętla nigdy się nie skończy "
                                "(przerwiesz ją skrótem Ctrl+C). Gdy warunek jest fałszywy od początku (np. `x = 10`, a potem `while x > 10:`), "
                                "ciało nie wykona się ani razu."
                            ),
                            heading("while czy for?"),
                            paragraph(
                                "`for` – gdy znasz liczbę powtórzeń albo przechodzisz po liście. `while` – gdy nie wiesz, ile razy trzeba powtórzyć, "
                                "np. pytanie o hasło albo podwajanie liczby, aż przekroczy 100:"
                            ),
                            code_block(
                                "n = 1",
                                "while n < 100:",
                                "    n = n * 2",
                                "print(n)",
                            ),
                            paragraph(
                                "`n` przyjmuje kolejno 2, 4, 8, 16, 32, 64, 128 – program wypisze 128."
                            ),
                        ),
                    ),
                    Image(
                        "v-schemat",
                        "Jak działa pętla while",
                        "p3_v_schemat.png",
                        "Schemat blokowy pętli while: sprawdzenie warunku, przy prawdzie ciało pętli i zmiana zmiennej, powrót do warunku; przy fałszu koniec",
                    ),
                    Image(
                        "v-kod",
                        "Pętla while krok po kroku",
                        "p3_v_kod.png",
                        "Kod z licznikiem od 1 do 5 i tabela: wartość licznika, czy warunek licznik <= 5 jest prawdziwy, co wypisze program",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie rozmowy o pętli while – jak działa, pętla nieskończona i wybór między while a for – a na końcu powtórka."
                    ),
                    Audio(
                        "a-1",
                        "Powtarzaj, dopóki…",
                        "p3_a1_dopoki.mp3",
                        (
                            say(
                                "Z",
                                "Marek, program ma pytać o hasło, aż użytkownik wpisze poprawne. Ile razy będzie pytał?",
                            ),
                            say("M", "Nie wiadomo. Może raz, a może dziesięć razy."),
                            say(
                                "Z",
                                "Gdy nie znamy liczby powtórzeń, używamy pętli {while|łajl}, czyli dopóki. Powtarza ciało, dopóki warunek jest prawdziwy. "
                                "Na przykład: {licznik = 1|licznik równa się jeden}, potem {while licznik <= 5:|łajl licznik mniejsze lub równe pięć, dwukropek}, "
                                "a w ciele {print(licznik)|print licznik} i {licznik = licznik + 1|licznik równa się licznik plus jeden}.",
                            ),
                            say(
                                "M",
                                "Wypisze {1, 2, 3, 4, 5|jeden, dwa, trzy, cztery, pięć}. Gdy licznik dojdzie do {6|sześciu}, warunek będzie fałszywy i pętla się skończy.",
                            ),
                        ),
                        "while licznik <= 5: – warunek sprawdzany przed każdym obrotem.",
                    ),
                    Audio(
                        "a-2",
                        "Uwaga na pętlę nieskończoną",
                        "p3_a2_nieskonczona.mp3",
                        (
                            say(
                                "M",
                                "A gdybym zapomniał o linii {licznik = licznik + 1|licznik plus jeden}?",
                            ),
                            say(
                                "Z",
                                "To bardzo częsty błąd. Licznik zostałby równy jeden, warunek byłby zawsze prawdziwy i program wypisywałby jedynkę bez końca. "
                                "To pętla nieskończona. Zatrzymasz ją skrótem {Ctrl+C|kontrol ce}.",
                            ),
                            say("M", "Czyli w ciele zawsze muszę zmienić zmienną z warunku."),
                            say(
                                "Z",
                                "Dokładnie. Jest też odwrotna sytuacja. Gdy {x = 10|iks równa się dziesięć}, a warunek to {while x > 10:|łajl iks większe od dziesięciu}, "
                                "ciało nie wykona się ani razu.",
                            ),
                        ),
                        "Częsty błąd: brak zmiany zmiennej z warunku; warunek fałszywy od początku.",
                    ),
                    Audio(
                        "a-3",
                        "while czy for?",
                        "p3_a3_while_for.mp3",
                        (
                            say(
                                "Z",
                                "{for|For} wybierasz, gdy wiesz, ile razy powtarzać, albo przechodzisz po liście. {while|Łajl} – gdy tego nie wiesz. "
                                "Zagadka: {n = 1|en równa się jeden}, a potem podwajamy {n|en}, dopóki jest mniejsze od stu. Co wypisze program?",
                            ),
                            say(
                                "M",
                                "{2, 4, 8, 16, 32, 64|Dwa, cztery, osiem, szesnaście, trzydzieści dwa, sześćdziesiąt cztery}. "
                                "{64|Sześćdziesiąt cztery} jest jeszcze mniejsze od stu, więc pętla robi kolejny obrót. Wyjdzie {128|sto dwadzieścia osiem}.",
                            ),
                            say(
                                "Z",
                                "Brawo. Nikt nie musiał z góry liczyć obrotów – o końcu zdecydował warunek.",
                            ),
                        ),
                        "Kiedy while, a kiedy for; podwajanie liczby, aż przekroczy 100.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "p3_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. Pętla {while|łajl} powtarza ciało, dopóki warunek jest prawdziwy, a warunek sprawdza przed każdym obrotem. "
                                "W ciele zmieniaj zmienną z warunku, inaczej powstanie pętla nieskończona. Gdy warunek jest fałszywy od początku, ciało nie wykona się ani razu. "
                                "{while|Łajl} wybierasz, gdy nie znasz liczby powtórzeń.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Otwórz edytor Pythona. Przy każdym programie prowadź na kartce tabelkę: wartość zmiennej i czy warunek jest prawdziwy."
                            ),
                            ordered(
                                "Wpisz: `licznik = 1`, a pod spodem `while licznik <= 5:` (z dwukropkiem na końcu).",
                                "W ciele, z wcięciem, wpisz dwie linie: `print(licznik)` oraz `licznik = licznik + 1`.",
                                "Zanim uruchomisz, zrób tabelkę z kolumnami: `licznik`, czy `licznik <= 5`, co wypisze. Wypełniaj ją, aż warunek będzie fałszywy (`licznik = 6`).",
                                "Uruchom i porównaj z tabelką: 1, 2, 3, 4, 5. `while` sprawdza warunek przed każdym obrotem i kończy się, gdy jest fałszywy.",
                                "Usuń linię `licznik = licznik + 1` i uruchom. Program wypisuje 1 bez końca – to pętla nieskończona. Zatrzymaj ją skrótem Ctrl+C i przywróć usuniętą linię.",
                                "Zmień początek na `licznik = 10` i uruchom – nic się nie wypisze, bo warunek jest fałszywy od początku i ciało nie wykona się ani razu.",
                                "Napisz program z podwajaniem: `n = 1`, `while n < 100:` z wciętym `n = n * 2`, a po pętli `print(n)`. Przewidź wynik na kartce (128) i sprawdź.",
                                "Zapisz zasadę: `for` – gdy znasz liczbę powtórzeń, `while` – gdy jej nie znasz (np. pytanie o hasło).",
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: pętla while",
                        "p3_k_karta.pdf",
                        "Tabela obrotów, odliczanie, pętla nieskończona i pytanie o hasło.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Kiedy pętla while kończy działanie?",
                    "gdy jej warunek staje się fałszywy",
                    (
                        "zawsze po 10 obrotach",
                        "gdy coś wypisze na ekran",
                        "nigdy, trzeba ją przerwać ręcznie",
                    ),
                    "while sprawdza warunek przed każdym obrotem. Dopóki jest prawdziwy – wykonuje ciało; gdy staje się fałszywy – pętla się kończy.",
                ),
                Question(
                    "q2",
                    "x = 1, potem pętla while x < 4: z wciętymi liniami print(x) i x = x + 1. Co wypisze program?",
                    "1, 2, 3",
                    ("1, 2, 3, 4", "2, 3, 4", "nic"),
                    "Wypisuje 1, 2, 3. Gdy x = 4, warunek 4 < 4 jest fałszywy, więc 4 już się nie wypisze.",
                ),
                Question(
                    "q3",
                    "i = 0, potem while i < 5: z wciętym tylko print(i). Co się stanie?",
                    "pętla nigdy się nie skończy i będzie wypisywać 0",
                    ("wypisze 0, 1, 2, 3, 4", "Python zgłosi błąd składni", "nic się nie wypisze"),
                    "W ciele nic nie zmienia i, więc warunek 0 < 5 jest zawsze prawdziwy – to pętla nieskończona. Brakuje linii i = i + 1.",
                ),
                Question(
                    "q4",
                    "x = 10, potem while x > 10: z wciętym print(x). Ile razy wykona się print?",
                    "ani razu",
                    ("raz", "10 razy", "bez końca"),
                    "Warunek 10 > 10 jest fałszywy już na początku, więc ciało pętli nie wykona się ani razu.",
                ),
                Question(
                    "q5",
                    "Kiedy lepiej użyć while niż for?",
                    "gdy nie wiadomo z góry, ile będzie powtórzeń (np. pytanie o hasło)",
                    (
                        "gdy przechodzimy po wszystkich elementach listy",
                        "gdy chcemy powtórzyć coś dokładnie 10 razy",
                        "zawsze – for jest przestarzałe",
                    ),
                    "for pasuje do znanej liczby powtórzeń i przechodzenia po listach, a while – do sytuacji, w których powtarzamy, dopóki coś się nie zmieni.",
                ),
                Question(
                    "q6",
                    "n = 1, potem while n < 100: z wciętym n = n * 2, a po pętli print(n). Co wypisze program?",
                    "128",
                    ("64", "100", "256"),
                    "n przyjmuje 2, 4, 8, 16, 32, 64. Ponieważ 64 < 100, jest jeszcze jeden obrót: n = 128. Teraz 128 < 100 jest fałszywe i pętla się kończy.",
                ),
                Question(
                    "q7",
                    'i = 3, potem while i > 0: z wciętymi print(i) i i = i - 1, a po pętli print("Start!"). Co wypisze program?',
                    "3, 2, 1, Start!",
                    ("3, 2, 1, 0, Start!", "1, 2, 3, Start!", "Start!, 3, 2, 1"),
                    'Wypisuje 3, 2, 1. Gdy i = 0, warunek 0 > 0 jest fałszywy, więc pętla się kończy i wykonuje się print("Start!").',
                ),
                Question(
                    "q8",
                    "k = 0, potem while k < 10: z wciętym k = k + 2. Ile razy wykona się ciało pętli?",
                    "5 razy",
                    ("10 razy", "4 razy", "6 razy"),
                    "k przyjmuje kolejno 0, 2, 4, 6, 8 – pięć obrotów. Po piątym k = 10 i warunek 10 < 10 jest fałszywy.",
                ),
            ),
        ),
        # --- 4. break i continue ----------------------------------------------------------------
        Lesson(
            title="break i continue",
            outline=doc(
                paragraph(
                    "Poznasz dwie instrukcje sterujące pętlą: break, która kończy pętlę od razu, i continue, która pomija resztę "
                    "bieżącego obrotu. Wykorzystasz je do szukania liczby i pomijania niepotrzebnych elementów."
                )
            ),
            conclusions=doc(
                bullets(
                    "`break` natychmiast kończy całą pętlę; program przechodzi do pierwszej instrukcji po pętli.",
                    "`continue` przerywa tylko bieżący obrót i przechodzi do następnego (pętla działa dalej).",
                    "Obie zwykle stoją w `if`, np. `if n % 2 == 0: continue` pomija liczby parzyste (`%` to reszta z dzielenia: `7 % 2` = 1).",
                    "`while True:` z `break` w środku – pętla działa, aż spełni się warunek wyjścia (np. poprawne hasło).",
                )
            ),
            versions={
                "V": (
                    Text(
                        "v-tekst",
                        doc(
                            heading("break – wyjdź z pętli"),
                            paragraph(
                                "Instrukcja ",
                                mono("break"),
                                " natychmiast kończy całą pętlę. Program przechodzi do pierwszej linii po pętli. "
                                "Przydaje się przy szukaniu: gdy znajdziesz to, czego szukasz, dalsze obroty są niepotrzebne.",
                            ),
                            code_block(
                                "for n in [3, 8, -1, 5]:",
                                "    if n < 0:",
                                "        break",
                                "    print(n)",
                                'print("koniec")',
                            ),
                            paragraph(
                                "Wypisze 3, 8 i koniec. Przy −1 pętla się kończy, więc 5 nie zostanie wypisane, ale linia po pętli wykona się normalnie."
                            ),
                            heading("continue – pomiń ten obrót"),
                            paragraph(
                                mono("continue"),
                                " przerywa tylko bieżący obrót: pomija resztę ciała i przechodzi do następnego elementu. "
                                "Operator `%` daje resztę z dzielenia (`7 % 2` = 1, `6 % 2` = 0), więc `n % 2 == 0` oznacza liczbę parzystą.",
                            ),
                            code_block(
                                "for n in range(1, 7):",
                                "    if n % 2 == 0:",
                                "        continue",
                                "    print(n)",
                            ),
                            paragraph("Wypisze 1, 3, 5 – liczby parzyste zostały pominięte."),
                            heading("while True i break"),
                            paragraph(
                                "`while True:` to pętla, której warunek jest zawsze prawdziwy. Kończy ją dopiero `break`, "
                                "np. gdy użytkownik wpisze poprawne hasło:"
                            ),
                            code_block(
                                "while True:",
                                '    haslo = input("Hasło: ")',
                                '    if haslo == "python":',
                                "        break",
                                'print("Witaj!")',
                            ),
                        ),
                    ),
                    Image(
                        "v-porownanie",
                        "break i continue obok siebie",
                        "p4_v_break_continue.png",
                        "Dwa programy obok siebie: z break wypisuje 3 i 8, z continue wypisuje 1, 3 i 5; strzałki pokazują wyjście z pętli i przejście do następnego obrotu",
                    ),
                ),
                "A": (
                    audio_intro(
                        "Trzy krótkie rozmowy o instrukcjach break i continue oraz pętli while True, a na końcu powtórka."
                    ),
                    Audio(
                        "a-1",
                        "break – wyjdź z pętli",
                        "p4_a1_break.mp3",
                        (
                            say(
                                "Z",
                                "Dziś poznasz dwie instrukcje: {break|brejk} i {continue|kontinju}. {break|Brejk} natychmiast kończy całą pętlę. "
                                "Przykład: pętla przechodzi po liście {[3, 8, -1, 5]|trzy, osiem, minus jeden, pięć}. W ciele: {if n < 0: break|jeśli en jest mniejsze od zera, to brejk}, a potem {print(n)|print en}.",
                            ),
                            say(
                                "M",
                                "Wypisze {3 i 8|trzy i osiem}. Przy {-1|minus jedynce} pętla się kończy, więc piątka się nie pojawi.",
                            ),
                            say(
                                "Z",
                                'A jeśli po pętli, bez wcięcia, stoi {print("koniec")|print koniec}?',
                            ),
                            say(
                                "M",
                                "Wykona się, bo {break|brejk} kończy tylko pętlę, a nie cały program.",
                            ),
                        ),
                        "break kończy pętlę, ale linia po pętli wykonuje się normalnie.",
                    ),
                    Audio(
                        "a-2",
                        "continue – pomiń ten obrót",
                        "p4_a2_continue.mp3",
                        (
                            say(
                                "Z",
                                "{continue|Kontinju} przerywa tylko bieżący obrót: pomija resztę ciała i przechodzi do następnego elementu. "
                                "Przyda się operator {%|procent}, czyli reszta z dzielenia: {7 % 2|siedem procent dwa} to {1|jeden}, a {6 % 2|sześć procent dwa} to {0|zero}.",
                            ),
                            say(
                                "M",
                                "Czyli {for n in range(1, 7):|for en in rejndż od jednego do siedmiu}, a w ciele {if n % 2 == 0: continue|jeśli en procent dwa równa się zero, to kontinju}. Potem {print(n)|print en}.",
                            ),
                            say("Z", "Co wypisze ten program?"),
                            say(
                                "M",
                                "{1, 3 i 5|Jeden, trzy i pięć}. Liczby parzyste zostaną pominięte.",
                            ),
                            say(
                                "Z",
                                "Dobrze. Pętla działała do końca, pominęła tylko resztę niektórych obrotów.",
                            ),
                        ),
                        "continue i reszta z dzielenia: pomijanie liczb parzystych.",
                    ),
                    Audio(
                        "a-3",
                        "while True i break",
                        "p4_a3_while_true.mp3",
                        (
                            say(
                                "Z",
                                "Jest jeszcze ważny wzór: {while True:|łajl tru}. Warunek {True|tru} jest zawsze prawdziwy, więc ta pętla sama się nie skończy. "
                                'Kończy ją {break|brejk}, na przykład gdy użytkownik wpisze poprawne hasło: {if haslo == "python": break|jeśli hasło równa się pyton, to brejk}.',
                            ),
                            say("M", "Czyli bez {break|brejk} to byłaby pętla nieskończona."),
                            say(
                                "Z",
                                "Tak. {break|Brejk} przydaje się też przy szukaniu. Szukasz pierwszej liczby od {20|dwudziestu} w górę, która dzieli się przez siedem. "
                                "Gdy znajdziesz {21|dwadzieścia jeden}, przerywasz pętlę.",
                            ),
                            say("M", "Czyli dalszych liczb pętla już nie sprawdza."),
                        ),
                        "Pętla while True zakończona przez break i szukanie liczby.",
                    ),
                    Audio(
                        "a-powtorka",
                        "Powtórka",
                        "p4_a4_powtorka.mp3",
                        (
                            say(
                                "Z",
                                "Powtórka. {break|Brejk} kończy całą pętlę, a program działa dalej od pierwszej linii po niej. "
                                "{continue|Kontinju} pomija tylko resztę bieżącego obrotu i pętla działa dalej. Operator {%|procent} daje resztę z dzielenia, "
                                "więc {n % 2 == 0|en procent dwa równa się zero} oznacza liczbę parzystą. Pętlę {while True|łajl tru} kończy dopiero {break|brejk}.",
                            ),
                        ),
                        "Najważniejsze z lekcji jeszcze raz – posłuchaj przed quizem.",
                        recap=True,
                    ),
                ),
                "K": (
                    Text(
                        "k-instrukcja",
                        doc(
                            paragraph(
                                "Otwórz edytor Pythona. Przepisuj programy, przewiduj wynik na kartce, potem uruchamiaj."
                            ),
                            ordered(
                                'Wpisz pętlę `for n in [3, 8, -1, 5]:`, a w jej ciele: `if n < 0:` z jeszcze głębiej wciętym `break`, potem (na poziomie `if`) `print(n)`. Na końcu, bez wcięcia, `print("koniec")`.',
                                "Przewidź wynik i uruchom: 3, 8, koniec. `break` kończy całą pętlę natychmiast, ale linia po pętli wykonuje się normalnie.",
                                "Sprawdź operator reszty z dzielenia: w konsoli wpisz `7 % 2` (wynik 1) i `6 % 2` (wynik 0). `n % 2 == 0` oznacza, że n jest parzyste.",
                                "Napisz: `for n in range(1, 7):`, w ciele `if n % 2 == 0:` z wciętym `continue`, a potem `print(n)`. Uruchom – wyjdzie 1, 3, 5. `continue` pominęło resztę obrotu dla liczb parzystych, ale pętla działała dalej.",
                                "Zamień `continue` na `break` i uruchom ponownie. Wyjdzie tylko 1 – porównaj: `break` kończy pętlę, `continue` pomija jeden obrót.",
                                "Napisz szukanie: `for n in range(20, 40):`, w ciele `if n % 7 == 0:`, a w nim `print(n)` i `break`. Wypisze 21 – pierwszą liczbę podzielną przez 7.",
                                'Napisz pętlę z hasłem: `while True:`, w ciele `haslo = input("Hasło: ")` oraz `if haslo == "python":` z wciętym `break`. Po pętli `print("Witaj!")`. Bez `break` ta pętla nigdy by się nie skończyła.',
                                WORKSHEET_STEP,
                            ),
                        ),
                    ),
                    Pdf(
                        "k-karta",
                        "Karta zadania: break i continue",
                        "p4_k_karta.pdf",
                        "Przewidywanie wyniku, reszta z dzielenia, szukanie i mała gra z while True.",
                    ),
                ),
            },
            questions=(
                Question(
                    "q1",
                    "Co robi instrukcja break w pętli?",
                    "natychmiast kończy całą pętlę",
                    (
                        "pomija tylko bieżący obrót",
                        "zatrzymuje cały program",
                        "zaczyna pętlę od nowa",
                    ),
                    "break przerywa pętlę od razu – kolejne obroty już się nie wykonają, a program przechodzi do pierwszej linii po pętli.",
                ),
                Question(
                    "q2",
                    "Co robi instrukcja continue w pętli?",
                    "pomija resztę bieżącego obrotu i przechodzi do następnego",
                    (
                        "kończy całą pętlę",
                        "powtarza bieżący obrót jeszcze raz",
                        "kończy cały program",
                    ),
                    "continue nie kończy pętli – tylko przeskakuje resztę ciała w tym obrocie. Pętla działa dalej z kolejnym elementem.",
                ),
                Question(
                    "q3",
                    "Pętla przechodzi po liście [3, 8, -1, 5]. W każdym obrocie: jeśli n < 0, wykonuje break, a w przeciwnym razie wypisuje n. Co zobaczysz?",
                    "3 i 8",
                    ("3, 8 i 5", "3, 8 i -1", "nic"),
                    "3 i 8 są wypisane. Przy -1 warunek n < 0 jest prawdziwy, więc break kończy pętlę – 5 nie zostanie już sprawdzone ani wypisane.",
                ),
                Question(
                    "q4",
                    "Pętla for n in range(1, 7): w ciele – jeśli n % 2 == 0, to continue; potem print(n). Co wypisze?",
                    "1, 3, 5",
                    ("2, 4, 6", "1, 2, 3, 4, 5, 6", "tylko 1"),
                    "continue pomija print dla liczb parzystych (reszta z dzielenia przez 2 równa 0). Zostają nieparzyste: 1, 3, 5. Samo 1 wyszłoby, gdyby zamiast continue było break.",
                ),
                Question(
                    "q5",
                    "Jak kończy się pętla while True:?",
                    "instrukcją break, gdy spełniony jest warunek wyjścia",
                    (
                        "sama, po 100 obrotach",
                        "instrukcją continue",
                        "nie da się jej zakończyć w kodzie",
                    ),
                    "Warunek True jest zawsze prawdziwy, więc pętla nie skończy się sama. Wychodzi się z niej przez break, np. po wpisaniu poprawnego hasła.",
                ),
                Question(
                    "q6",
                    "Ile wynosi 7 % 2 w Pythonie?",
                    "1",
                    ("3", "3.5", "0"),
                    "% to reszta z dzielenia: 7 = 3 · 2 + 1, więc reszta wynosi 1. Wynik 3.5 dałoby zwykłe dzielenie 7 / 2.",
                ),
                Question(
                    "q7",
                    "Pętla for n in range(20, 40): w ciele – jeśli n % 7 == 0, to print(n) i break. Co wypisze?",
                    "21",
                    ("28", "20", "21, 28, 35"),
                    "Pierwsza liczba od 20 podzielna przez 7 to 21. Po jej wypisaniu break kończy pętlę, więc 28 i 35 się nie pojawią.",
                ),
                Question(
                    "q8",
                    'W pętli wykonało się break. Czy linia print("koniec") umieszczona po pętli (bez wcięcia) się wykona?',
                    "Tak – break kończy tylko pętlę, program działa dalej.",
                    (
                        "Nie – break kończy cały program.",
                        "Tylko wtedy, gdy break się nie wykonał.",
                        "Nie – linia po pętli wykonuje się tylko przy continue.",
                    ),
                    'break wychodzi wyłącznie z pętli. Program przechodzi do pierwszej linii po niej, więc print("koniec") się wykona.',
                ),
            ),
        ),
    ),
)


COURSES: tuple[Course, ...] = (MATH, ENGLISH, PYTHON)
