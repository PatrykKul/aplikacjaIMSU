from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LessonQuiz(Base):
    """Question pool of one lesson, saved as a whole (validated by `schemas.QuizContent`)."""

    __tablename__ = "lesson_quizzes"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), unique=True
    )
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default=text("'[]'"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class QuizDraw(Base):
    """Questions drawn for one attempt; graded only against this set (R9)."""

    __tablename__ = "quiz_draws"
    __table_args__ = (
        CheckConstraint("percent BETWEEN 0 AND 100", name="percent"),
        Index("ix_quiz_draws_user_id_lesson_id", "user_id", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    # Question ids in the order shown to the student
    question_ids: Mapped[list[str]] = mapped_column(JSONB)
    # question id -> chosen answer id; None until submitted
    answers: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    percent: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # None = attempt still open
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
