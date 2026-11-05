from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Lesson(Base):
    """The lesson of a skill: an ordered list of steps (see steps.py)."""

    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Foreign key into the curriculum module: allowed in the database,
    # but queries about skills go through curriculum.service
    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), unique=True)
    title: Mapped[str] = mapped_column(String(120))
    # Always written as LessonSteps(...).to_json();
    # assign a new list, in-place edits are not tracked
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB)
    is_archived: Mapped[bool] = mapped_column(server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
