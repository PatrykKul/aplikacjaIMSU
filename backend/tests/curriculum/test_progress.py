"""R10: lesson unlocking (pure functions)."""

from app.modules.curriculum.progress import (
    AVAILABLE,
    LOCKED,
    PASSED,
    LessonState,
    lesson_states,
    next_lesson_id,
)


def test_only_first_lesson_is_available_at_start() -> None:
    assert lesson_states([10, 20, 30], set()) == [
        LessonState(10, 1, AVAILABLE),
        LessonState(20, 2, LOCKED, required_lesson_id=10, required_number=1),
        LessonState(30, 3, LOCKED, required_lesson_id=20, required_number=2),
    ]


def test_passing_a_lesson_unlocks_the_next_one() -> None:
    states = lesson_states([10, 20, 30], {10})
    assert [s.state for s in states] == [PASSED, AVAILABLE, LOCKED]
    assert (states[2].required_lesson_id, states[2].required_number) == (20, 2)


def test_all_passed() -> None:
    assert [s.state for s in lesson_states([10, 20], {10, 20})] == [PASSED, PASSED]


def test_reordering_keeps_passed_lesson_available() -> None:
    # Lesson 30 was passed as the 2nd lesson; the teacher moves it to the end
    states = lesson_states([10, 20, 30], {10, 30})
    assert [s.state for s in states] == [PASSED, AVAILABLE, PASSED]


def test_new_first_lesson_after_reordering() -> None:
    # A new lesson put first is available; the passed one stays passed
    states = lesson_states([40, 10, 20], {10})
    assert [s.state for s in states] == [AVAILABLE, PASSED, AVAILABLE]


def test_numbers_follow_the_given_order() -> None:
    assert [s.number for s in lesson_states([7, 3, 5], set())] == [1, 2, 3]


def test_no_lessons() -> None:
    assert lesson_states([], set()) == []


def test_next_lesson() -> None:
    assert next_lesson_id([10, 20, 30], 10) == 20
    assert next_lesson_id([10, 20, 30], 30) is None
    assert next_lesson_id([10, 20, 30], 99) is None  # e.g. an unpublished lesson
