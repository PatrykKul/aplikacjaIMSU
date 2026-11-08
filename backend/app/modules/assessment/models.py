from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LessonQuiz(Base):
    """Quiz of one lesson, saved as a whole (validated by `schemas.QuizContent`)."""

    __tablename__ = "lesson_quizzes"

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), unique=True
    )
    questions: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default=text("'[]'"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
