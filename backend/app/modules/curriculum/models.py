from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

TITLE_LENGTH = 120


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(TITLE_LENGTH))
    description: Mapped[str] = mapped_column(Text, server_default="")
    # TipTap document; None until the teacher writes an introduction
    introduction: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    is_published: Mapped[bool] = mapped_column(server_default=false())
    is_archived: Mapped[bool] = mapped_column(server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lessons: Mapped[list["Lesson"]] = relationship(
        back_populates="course", order_by=lambda: (Lesson.position, Lesson.id)
    )


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), index=True)
    title: Mapped[str] = mapped_column(String(TITLE_LENGTH))
    position: Mapped[int]
    is_archived: Mapped[bool] = mapped_column(server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    course: Mapped[Course] = relationship(back_populates="lessons")
