"""Statistics aggregates (pure functions)."""

from datetime import UTC, datetime

from app.modules.learning_style.rules import CourseResult
from app.modules.learning_style.stats import (
    Attempt,
    FormEffect,
    LessonInfo,
    counted_average,
    form_effectiveness,
    lesson_results,
    style_distribution,
)


def test_form_effectiveness():
    results = [
        CourseResult(1, "A", 80, True),
        CourseResult(1, "A", 100, False),
        CourseResult(2, "A", 61, True),
        CourseResult(3, "V", 40, True),
    ]
    effects = form_effectiveness(results)
    assert effects["A"] == FormEffect(average=71, counted_results=2, attempts=3, students=2)
    assert effects["V"] == FormEffect(average=40, counted_results=1, attempts=1, students=1)
    assert effects["K"] == FormEffect(average=None, counted_results=0, attempts=0, students=0)


def test_style_distribution_counts_missing_styles_as_none():
    assert style_distribution(["V", "A", "A", None]) == {"V": 1, "A": 2, "K": 0, "none": 1}
    assert style_distribution([]) == {"V": 0, "A": 0, "K": 0, "none": 0}


def test_counted_average_ignores_retries():
    results = [CourseResult(1, "V", 40, True), CourseResult(1, "V", 100, False)]
    assert counted_average(results) == 40
    assert counted_average([]) is None


def test_lesson_results_only_attempted_lessons_in_order():
    at = datetime(2026, 11, 12, tzinfo=UTC)
    lessons = [
        LessonInfo(1, "Matematyka", 10, "Lekcja 1", 1),
        LessonInfo(1, "Matematyka", 11, "Lekcja 2", 2),
        LessonInfo(1, "Matematyka", 12, "Lekcja 3", None),
    ]
    attempts = [
        Attempt(12, at, "A", 80, True, True),
        Attempt(10, at, "V", 40, False, True),
        Attempt(10, at, "V", 80, True, False),
    ]
    rows = lesson_results(lessons, attempts, passed_ids={10})
    assert [(row["lesson_id"], row["passed"], row["number"]) for row in rows] == [
        (10, True, 1),
        (12, False, None),
    ]
    assert rows[0]["attempts"] == [
        {"at": at, "form": "V", "percent": 40, "passed": False, "counted": True},
        {"at": at, "form": "V", "percent": 80, "passed": True, "counted": False},
    ]
    assert rows[0]["course_title"] == "Matematyka"
