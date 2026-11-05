import enum
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, String, UniqueConstraint, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LessonMethod(enum.StrEnum):
    """Teaching method of a lesson variant (Alfa-Delta profiles). COMMON is the fallback."""

    COMMON = "common"
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    DELTA = "delta"


class Lesson(Base):
    """One variant of the lesson for a skill: an ordered list of steps (see steps.py)."""

    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("skill_id", "method"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Foreign key into the curriculum module: allowed in the database,
    # but queries about skills go through curriculum.service
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"))
    method: Mapped[LessonMethod] = mapped_column(
        Enum(
            LessonMethod,
            name="lesson_method",
            native_enum=False,
            create_constraint=True,
            length=10,
            values_callable=lambda methods: [method.value for method in methods],
        )
    )
    title: Mapped[str] = mapped_column(String(120))
    # Always written as LessonSteps(...).to_json();
    # assign a new list, in-place edits are not tracked
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    is_archived: Mapped[bool] = mapped_column(server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
