"""Statistics for the student and the teacher: pure functions, no database and no FastAPI."""

from collections.abc import Collection, Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.modules.learning_style.rules import FORMS, CourseResult, average

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
