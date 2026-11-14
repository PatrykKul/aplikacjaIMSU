"""Statistics for the student and the teacher: pure functions, no database and no FastAPI.

Below a data threshold a share is `None` and the count it would come from is returned next to
it, so the screen can say "too little data (n = 2)".
"""

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from math import floor
from typing import Any

from app.modules.learning_style.rules import (
    FORMS,
    CourseResult,
    Result,
    average,
    form_stats,
    rate,
)

# --- Constants (docs/08 "Stałe"; repeated in the frontend's explain.ts) --------------------------

FIRST_TRY_MIN_LESSONS = 2  # form table: "first time" pass rate
LESSON_MIN_STUDENTS = 3  # lesson statistics: pass rate, first average, the hardest lesson
MATRIX_MIN_RESULTS = 2  # lesson x form matrix: a cell's average and the conclusions
FORM_GAP = 20  # matrix conclusion: best minus worst form (points)


def mean_tenths(values: Iterable[int]) -> float | None:
    """Mean with one decimal, rounded half up (exact); None without values."""
    items = list(values)
    if not items:
        return None
    return floor(Fraction(10 * sum(items), len(items)) + Fraction(1, 2)) / 10


def _rank(form: str) -> int:
    return FORMS.index(form)


# --- Student: summary and form table -------------------------------------------------------------


@dataclass(frozen=True)
class StudentSummary:
    attempts: int  # submitted attempts (all results)
    average: int | None  # of counted results
    counted: int  # counted results
    streak: int  # counted passes in a row, from the newest backwards


def student_summary(results: Sequence[Result]) -> StudentSummary:
    """The student's results in order (all courses) -> the summary line of "My progress".

    The streak counts counted passes from the newest result back to the first counted failure;
    not counted attempts are skipped.
    """
    counted = [r for r in results if r.counted]
    streak = 0
    for result in reversed(counted):
        if not result.passed:
            break
        streak += 1
    return StudentSummary(
        attempts=len(results),
        average=average(r.percent for r in counted),
        counted=len(counted),
        streak=streak,
    )


@dataclass(frozen=True)
class FormTableRow:
    lessons: int  # distinct lessons with an attempt in the form
    attempts: int  # attempts in the form
    passed_lessons: int  # distinct lessons with a passed attempt in the form
    first_try_lessons: int  # counted results in the form (first attempt in it in a lesson)
    first_try_passed: int  # of them passed
    first_try_rate: int | None  # percent passed; None below FIRST_TRY_MIN_LESSONS
    average: int | None  # of counted results
    best: int | None  # highest result in the form, any attempt
    confirmed: bool  # R3: passed at least once
    percent: int | None  # the form's profile percentage; None without a profile


def form_table(
    results: Sequence[Result], percentages: Mapping[str, int] | None
) -> dict[str, FormTableRow]:
    """ "In which form it goes best": one row per form from all the student's results."""
    stats = form_stats(results)
    rows = {}
    for form in FORMS:
        in_form = [r for r in results if r.form == form]
        first = [r for r in in_form if r.counted]
        first_passed = sum(1 for r in first if r.passed)
        rows[form] = FormTableRow(
            lessons=len({r.lesson_id for r in in_form}),
            attempts=len(in_form),
            passed_lessons=len({r.lesson_id for r in in_form if r.passed}),
            first_try_lessons=len(first),
            first_try_passed=first_passed,
            first_try_rate=(
                rate(first_passed, len(first)) if len(first) >= FIRST_TRY_MIN_LESSONS else None
            ),
            average=stats[form].average,
            best=max((r.percent for r in in_form), default=None),
            confirmed=stats[form].confirmed,
            percent=None if percentages is None else percentages[form],
        )
    return rows


# --- Course: lessons, the hardest one, lesson x form matrix --------------------------------------


@dataclass(frozen=True)
class LessonRef:
    lesson_id: int
    title: str
    number: int


@dataclass(frozen=True)
class LessonResult:
    """A result of any student of the course, in the order it was recorded."""

    student_id: int
    lesson_id: int
    form: str
    percent: int
    passed: bool
    counted: bool


@dataclass(frozen=True)
class LessonStatsRow:
    lesson_id: int
    title: str
    number: int
    started: int  # students with at least one attempt
    passed: int  # students with a passed attempt
    pass_rate: int | None  # passed / started; None below LESSON_MIN_STUDENTS started
    first_average: int | None  # of counted results; None below LESSON_MIN_STUDENTS started
    first_results: int  # counted results
    attempts_to_pass: float | None  # mean attempts up to the first pass; None without a pass


def _attempts_to_pass(attempts: Sequence[LessonResult]) -> int | None:
    """1-based number of the first passed attempt of one student (None without a pass)."""
    return next((index for index, r in enumerate(attempts, 1) if r.passed), None)


def lesson_stats(
    lessons: Sequence[LessonRef], results: Sequence[LessonResult]
) -> list[LessonStatsRow]:
    """ "Which lessons are difficult": one row per lesson, in the given (course) order."""
    rows = []
    for lesson in lessons:
        own = [r for r in results if r.lesson_id == lesson.lesson_id]
        by_student: dict[int, list[LessonResult]] = {}
        for result in own:
            by_student.setdefault(result.student_id, []).append(result)
        to_pass = [n for a in by_student.values() if (n := _attempts_to_pass(a)) is not None]
        counted = [r.percent for r in own if r.counted]
        started = len(by_student)
        enough = started >= LESSON_MIN_STUDENTS
        rows.append(
            LessonStatsRow(
                lesson_id=lesson.lesson_id,
                title=lesson.title,
                number=lesson.number,
                started=started,
                passed=len(to_pass),
                pass_rate=rate(len(to_pass), started) if enough else None,
                first_average=average(counted) if enough else None,
                first_results=len(counted),
                attempts_to_pass=mean_tenths(to_pass),
            )
        )
    return rows


def hardest_lesson(rows: Iterable[LessonStatsRow]) -> LessonStatsRow | None:
    """Lowest pass rate among lessons with enough students; tie: lower first average, then
    the earlier lesson. None without such a lesson or when all of them are passed by everyone.
    """
    candidates = [row for row in rows if row.pass_rate is not None]
    if not candidates:
        return None
    hardest = min(
        candidates,
        key=lambda row: (
            row.pass_rate,
            101 if row.first_average is None else row.first_average,
            row.number,
        ),
    )
    return None if hardest.pass_rate == 100 else hardest


@dataclass(frozen=True)
class MatrixCell:
    average: int | None  # of counted results in the form; None below MATRIX_MIN_RESULTS
    n: int  # counted results in the form


@dataclass(frozen=True)
class MatrixRow:
    lesson_id: int
    title: str
    number: int
    cells: dict[str, MatrixCell]


def lesson_form_matrix(
    lessons: Sequence[LessonRef], results: Sequence[LessonResult]
) -> list[MatrixRow]:
    """ "How each lesson works in each form": average of counted results per lesson and form."""
    rows = []
    for lesson in lessons:
        cells = {}
        for form in FORMS:
            counted = [
                r.percent
                for r in results
                if r.lesson_id == lesson.lesson_id and r.form == form and r.counted
            ]
            enough = len(counted) >= MATRIX_MIN_RESULTS
            cells[form] = MatrixCell(average(counted) if enough else None, len(counted))
        rows.append(MatrixRow(lesson.lesson_id, lesson.title, lesson.number, cells))
    return rows


@dataclass(frozen=True)
class FormMean:
    form: str
    average: int
    n: int


@dataclass(frozen=True)
class FormGap:
    lesson_id: int
    title: str
    number: int
    best: FormMean
    worst: FormMean


def form_gaps(matrix: Iterable[MatrixRow]) -> list[FormGap]:
    """Lessons where the best and the worst form (both with enough results) differ by at least
    FORM_GAP points; a tie of forms goes in V, A, K order. Keeps the matrix (course) order.
    """
    gaps = []
    for row in matrix:
        means = [
            FormMean(form, cell.average, cell.n)
            for form, cell in row.cells.items()
            if cell.average is not None
        ]
        if len(means) < 2:
            continue
        best = min(means, key=lambda m: (-m.average, _rank(m.form)))
        worst = min(means, key=lambda m: (m.average, _rank(m.form)))
        if best.average - worst.average >= FORM_GAP:
            gaps.append(FormGap(row.lesson_id, row.title, row.number, best, worst))
    return gaps


# --- Course: form effectiveness and styles -------------------------------------------------------


@dataclass(frozen=True)
class FormEffect:
    average: int | None  # of counted results
    counted_results: int
    attempts: int  # all attempts, also not counted
    students: int  # students with at least one attempt in the form


def form_effectiveness(results: Iterable[CourseResult]) -> dict[str, FormEffect]:
    """How well each form works in a course: counted average, results, attempts, students."""
    items = list(results)
    effects = {}
    for form in FORMS:
        in_form = [r for r in items if r.form == form]
        counted = [r.percent for r in in_form if r.counted]
        effects[form] = FormEffect(
            average=average(counted),
            counted_results=len(counted),
            attempts=len(in_form),
            students=len({r.student_id for r in in_form}),
        )
    return effects


def style_distribution(styles: Iterable[str | None]) -> dict[str, int]:
    """Active styles of the course's students; `none` = no survey or an unresolved tie."""
    counts = dict.fromkeys((*FORMS, "none"), 0)
    for style in styles:
        counts[style if style in FORMS else "none"] += 1
    return counts


def counted_average(results: Iterable[CourseResult]) -> int | None:
    """Average of a student's counted results (e.g. in one course)."""
    return average(r.percent for r in results if r.counted)


# --- Student: results per lesson -----------------------------------------------------------------


@dataclass(frozen=True)
class LessonInfo:
    course_id: int
    course_title: str
    lesson_id: int
    lesson_title: str
    number: int | None  # among published lessons; None for a lesson no longer published


@dataclass(frozen=True)
class Attempt:
    lesson_id: int
    at: datetime
    form: str
    percent: int
    passed: bool
    counted: bool


def lesson_results(
    lessons: Sequence[LessonInfo], attempts: Sequence[Attempt], passed_ids: Collection[int]
) -> list[dict[str, Any]]:
    """Lessons with at least one attempt, in the given order, each with all its attempts.

    `counted` marks the first attempt in each form (the one that changed the percentages).
    """
    rows = []
    for lesson in lessons:
        own = [a for a in attempts if a.lesson_id == lesson.lesson_id]
        if not own:
            continue
        rows.append(
            {
                "course_id": lesson.course_id,
                "course_title": lesson.course_title,
                "lesson_id": lesson.lesson_id,
                "lesson_title": lesson.lesson_title,
                "number": lesson.number,
                "passed": lesson.lesson_id in passed_ids,
                "attempts": [
                    {
                        "at": a.at,
                        "form": a.form,
                        "percent": a.percent,
                        "passed": a.passed,
                        "counted": a.counted,
                    }
                    for a in own
                ],
            }
        )
    return rows
