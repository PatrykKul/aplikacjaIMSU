"""Content checks run on every course package in `content/courses/`.

The import validates the format of a package; these tests check that its content is right:
every number answer is recalculated independently from its `check` data, and the
teaching rules for questions and formulas hold. A new course is covered automatically.
"""

from collections import Counter
from pathlib import Path

import pytest

from app.modules.content.package import (
    CoursePackage,
    LessonDefinition,
    PackageError,
    load_package,
)
from app.modules.content.steps import ChoiceAnswer, NumberAnswer, QuestionStep, TextStep
from tests.content.checks import OPERATIONS, evaluate, number

COURSES_DIR = Path(__file__).resolve().parents[2] / "content" / "courses"
PACKAGE_DIRS = sorted(path.parent for path in COURSES_DIR.glob("*/course.yaml"))

MIN_QUESTIONS, MAX_QUESTIONS = 4, 8
# The correct option may sit in the same position in at most this share of choice questions
MAX_SAME_POSITION = 0.6


def _load_valid() -> dict[str, CoursePackage]:
    """Packages that load; invalid ones are reported by test_package_is_valid."""
    packages = {}
    for path in PACKAGE_DIRS:
        try:
            packages[path.name] = load_package(path)
        except PackageError:
            pass
    return packages


PACKAGES = _load_valid()
LESSONS = [
    (f"{course}/{lesson.file_name}", lesson)
    for course, package in PACKAGES.items()
    for lesson in package.lessons
]


def _questions(answer_type: type) -> list[tuple[str, QuestionStep]]:
    return [
        (f"{name}:{step.key}", step)
        for name, lesson in LESSONS
        for step in lesson.steps
        if isinstance(step, QuestionStep) and isinstance(step.answer, answer_type)
    ]


NUMBER_QUESTIONS = _questions(NumberAnswer)
CHOICE_QUESTIONS = _questions(ChoiceAnswer)


def _ids(items: list[tuple[str, object]]) -> list[str]:
    return [name for name, _ in items]


def test_there_is_at_least_one_course():
    assert PACKAGE_DIRS, f"no course packages in {COURSES_DIR}"


@pytest.mark.parametrize("path", PACKAGE_DIRS, ids=lambda path: path.name)
def test_package_is_valid(path: Path):
    try:
        load_package(path)
    except PackageError as error:
        pytest.fail("\n".join(error.errors))


@pytest.mark.parametrize(("name", "lesson"), LESSONS, ids=_ids(LESSONS))
def test_lesson_has_enough_questions(name: str, lesson: LessonDefinition):
    count = sum(isinstance(step, QuestionStep) for step in lesson.steps)
    assert MIN_QUESTIONS <= count <= MAX_QUESTIONS


@pytest.mark.parametrize(("name", "step"), NUMBER_QUESTIONS, ids=_ids(NUMBER_QUESTIONS))
def test_number_answer_matches_independent_calculation(name: str, step: QuestionStep):
    check = step.answer.check
    assert check is not None, "every number question needs `check` data"
    assert check.get("op") in OPERATIONS, f"unknown op; known: {', '.join(sorted(OPERATIONS))}"
    assert evaluate(check) == number(step.answer.value)


@pytest.mark.parametrize(("name", "step"), CHOICE_QUESTIONS, ids=_ids(CHOICE_QUESTIONS))
def test_every_wrong_option_explains_the_mistake(name: str, step: QuestionStep):
    answer = step.answer
    wrong = [option for i, option in enumerate(answer.options) if i != answer.correct]
    assert all(option.feedback for option in wrong)


@pytest.mark.parametrize("course", sorted(PACKAGES))
def test_correct_option_is_not_always_in_the_same_place(course: str):
    positions = Counter(
        step.answer.correct for name, step in CHOICE_QUESTIONS if name.startswith(f"{course}/")
    )
    total = sum(positions.values())
    if total < 3:
        pytest.skip("too few choice questions to compare positions")
    assert max(positions.values()) <= MAX_SAME_POSITION * total, dict(positions)


@pytest.mark.parametrize(("name", "lesson"), LESSONS, ids=_ids(LESSONS))
def test_display_formulas_are_on_their_own_lines(name: str, lesson: LessonDefinition):
    for step in lesson.steps:
        texts = [step.body] if isinstance(step, TextStep) else [step.prompt, step.explanation]
        for text in texts:
            for line in text.splitlines():
                assert "$$" not in line or line.strip() == "$$", f"{step.key}: {line}"
