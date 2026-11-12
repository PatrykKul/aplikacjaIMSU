"""Lesson unlocking (R10): pure functions, no database and no FastAPI.

A lesson is available when it is the first published one or the previous published lesson
is passed; a lesson the student already passed stays available (also after reordering).
"""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Literal

PASSED = "passed"
AVAILABLE = "available"
LOCKED = "locked"

State = Literal["passed", "available", "locked"]


@dataclass(frozen=True)
class LessonState:
    lesson_id: int
    number: int  # 1-based position among published lessons
    state: State
    # The lesson to pass first (only for a locked lesson)
    required_lesson_id: int | None = None
    required_number: int | None = None


def lesson_states(lesson_ids: Sequence[int], passed: Collection[int]) -> list[LessonState]:
    """States of the published lessons of a course, in course order."""
    states = []
    for index, lesson_id in enumerate(lesson_ids):
        number = index + 1
        if lesson_id in passed:
            states.append(LessonState(lesson_id, number, PASSED))
        elif index == 0 or lesson_ids[index - 1] in passed:
            states.append(LessonState(lesson_id, number, AVAILABLE))
        else:
            states.append(
                LessonState(
                    lesson_id,
                    number,
                    LOCKED,
                    required_lesson_id=lesson_ids[index - 1],
                    required_number=index,
                )
            )
    return states


def next_lesson_id(lesson_ids: Sequence[int], lesson_id: int) -> int | None:
    """The published lesson after `lesson_id`, or None for the last one."""
    if lesson_id not in lesson_ids:
        return None
    index = lesson_ids.index(lesson_id)
    return lesson_ids[index + 1] if index + 1 < len(lesson_ids) else None
