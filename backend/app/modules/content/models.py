from datetime import datetime
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class File(Base):
    """Uploaded file: metadata here, bytes on disk in `UPLOAD_DIR/<storage_name>`."""

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    original_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size: Mapped[int]
    storage_name: Mapped[str] = mapped_column(String(64), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LessonContent(Base):
    """One version (V / A / K) of a lesson: blocks saved as a whole (`blocks.LessonBlocks`)."""

    __tablename__ = "lesson_contents"
    __table_args__ = (
        UniqueConstraint("lesson_id", "form"),
        CheckConstraint("form IN ('V', 'A', 'K')", name="form"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id"))
    form: Mapped[str] = mapped_column(String(1))
    blocks: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default=text("'[]'"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
