"""Lesson publication: gathers what each module says is missing (R11)."""

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.assessment import service as assessment
from app.modules.assessment.readiness import quiz_issues
from app.modules.content import service as content
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Lesson
from app.modules.curriculum.readiness import Issue
from app.modules.identity.models import User


def lesson_readiness(db: Session, lesson: Lesson) -> list[Issue]:
    """Missing parts in a fixed order: outline and conclusions, versions V, A, K, quiz pool."""
    return [
        *curriculum.lesson_issues(lesson),
        *content.version_issues(db, lesson.id),
        *quiz_issues(assessment.question_count(db, lesson.id)),
    ]


def get_readiness(db: Session, lesson_id: int, user: User) -> list[Issue]:
    lesson = curriculum.get_owned_lesson(db, lesson_id, user)
    return lesson_readiness(db, lesson)


def set_publication(db: Session, lesson_id: int, user: User, is_published: bool) -> Lesson:
    """Publish a complete lesson or withdraw it (not the last one of a published course)."""
    lesson = curriculum.get_owned_lesson(db, lesson_id, user)
    if is_published and not lesson.is_published:
        issues = lesson_readiness(db, lesson)
        if issues:
            raise AppError(409, "LESSON_NOT_READY", issues=issues)
    return curriculum.set_lesson_published(db, lesson, is_published)
