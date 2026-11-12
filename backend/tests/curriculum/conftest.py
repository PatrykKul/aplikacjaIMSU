from collections.abc import Callable
from typing import Any

import pytest
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.modules.curriculum import service
from app.modules.curriculum.models import Lesson


def doc(text: str) -> dict[str, Any]:
    """A TipTap document with one paragraph."""
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
    }


INTRODUCTION = doc("Witaj w kursie")
SUMMARY = doc("Najważniejsze wnioski z kursu")
OUTLINE = doc("O czym jest lekcja")
CONCLUSIONS = doc("Co zapamiętać")
EMPTY_DOC: dict[str, Any] = {"type": "doc", "content": [{"type": "paragraph"}]}


@pytest.fixture
def set_published(db: Session) -> Callable[..., None]:
    """Publish or withdraw a lesson straight in the database (no readiness rules)."""

    def _set(lesson_id: int, published: bool = True) -> None:
        db.execute(update(Lesson).where(Lesson.id == lesson_id).values(is_published=published))
        db.commit()

    return _set


@pytest.fixture
def pass_lesson(db: Session) -> Callable[[int, int], None]:
    """Record a passed quiz of a lesson, as `learning_style` does after grading."""

    def _pass(user_id: int, lesson_id: int) -> None:
        service.mark_lesson_passed(db, user_id, lesson_id)
        db.commit()

    return _pass
