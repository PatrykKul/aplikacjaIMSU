from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

KEY_LENGTH = 64
TITLE_LENGTH = 120


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(KEY_LENGTH), unique=True)
    title: Mapped[str] = mapped_column(String(TITLE_LENGTH))
    description: Mapped[str] = mapped_column(Text, server_default="")
    position: Mapped[int] = mapped_column(server_default=text("0"))
    is_published: Mapped[bool] = mapped_column(server_default=false())
    is_archived: Mapped[bool] = mapped_column(server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    units: Mapped[list["Unit"]] = relationship(back_populates="course", order_by="Unit.position")


class Unit(Base):
    __tablename__ = "units"
    __table_args__ = (UniqueConstraint("course_id", "key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    key: Mapped[str] = mapped_column(String(KEY_LENGTH))
    title: Mapped[str] = mapped_column(String(TITLE_LENGTH))
    position: Mapped[int] = mapped_column(server_default=text("0"))
    is_archived: Mapped[bool] = mapped_column(server_default=false())

    course: Mapped[Course] = relationship(back_populates="units")
    skills: Mapped[list["Skill"]] = relationship(back_populates="unit", order_by="Skill.position")


class Skill(Base):
    """Unit of the knowledge model: something a student can master and can be tested on."""

    __tablename__ = "skills"
    __table_args__ = (UniqueConstraint("course_id", "key"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    # Redundant with unit.course_id: makes the key unique per course, and graph queries simple
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units.id"), index=True)
    key: Mapped[str] = mapped_column(String(KEY_LENGTH))
    title: Mapped[str] = mapped_column(String(TITLE_LENGTH))
    goal: Mapped[str] = mapped_column(Text, server_default="")
    position: Mapped[int] = mapped_column(server_default=text("0"))
    is_archived: Mapped[bool] = mapped_column(server_default=false())

    unit: Mapped[Unit] = relationship(back_populates="skills")


class SkillPrerequisite(Base):
    """Edge of the prerequisite graph: `skill_id` requires `prerequisite_id`.

    Both skills belong to the same course; this is enforced by course package validation.
    """

    __tablename__ = "skill_prerequisites"
    __table_args__ = (CheckConstraint("skill_id <> prerequisite_id", name="not_self"),)

    skill_id: Mapped[int] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    prerequisite_id: Mapped[int] = mapped_column(
        ForeignKey("skills.id"), primary_key=True, index=True
    )
