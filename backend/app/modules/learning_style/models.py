from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

STYLE_LENGTH = 3  # "V", "VA", "VAK"
TEXT_LENGTH = 300


class SurveyQuestion(Base):
    __tablename__ = "survey_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(TEXT_LENGTH))
    position: Mapped[int]
    is_active: Mapped[bool] = mapped_column(server_default=true())

    answers: Mapped[list["SurveyAnswer"]] = relationship(
        back_populates="question",
        order_by=lambda: (SurveyAnswer.position, SurveyAnswer.id),
        cascade="all, delete-orphan",
    )


class SurveyAnswer(Base):
    __tablename__ = "survey_answers"
    __table_args__ = (CheckConstraint("style IN ('V', 'A', 'K')", name="style"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("survey_questions.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(String(TEXT_LENGTH))
    style: Mapped[str] = mapped_column(String(1))
    position: Mapped[int]

    question: Mapped[SurveyQuestion] = relationship(back_populates="answers")


class SurveyResult(Base):
    """One filled-in survey; every attempt is kept as history."""

    __tablename__ = "survey_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    points_v: Mapped[int]
    points_a: Mapped[int]
    points_k: Mapped[int]
    dominant_style: Mapped[str] = mapped_column(String(STYLE_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LearningProfile(Base):
    """Current learning style of a student; no row = survey not filled in yet."""

    __tablename__ = "learning_profiles"
    __table_args__ = (
        CheckConstraint("style_source IN ('survey', 'manual', 'adaptation')", name="style_source"),
        CheckConstraint(
            "weight_v BETWEEN 0 AND 30 AND weight_a BETWEEN 0 AND 30 AND weight_k BETWEEN 0 AND 30",
            name="weights",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    style: Mapped[str] = mapped_column(String(STYLE_LENGTH))
    style_source: Mapped[str] = mapped_column(String(12))
    weight_v: Mapped[int]
    weight_a: Mapped[int]
    weight_k: Mapped[int]
    rejected_proposal: Mapped[str | None] = mapped_column(String(1))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def weights(self) -> dict[str, int]:
        return {"V": self.weight_v, "A": self.weight_a, "K": self.weight_k}

    @weights.setter
    def weights(self, value: dict[str, int]) -> None:
        self.weight_v, self.weight_a, self.weight_k = value["V"], value["A"], value["K"]


class QuizAttempt(Base):
    """Quiz score reported by the quiz module (see `hooks.record_quiz_result`)."""

    __tablename__ = "quiz_attempts"
    __table_args__ = (
        CheckConstraint("percent BETWEEN 0 AND 100", name="percent"),
        Index("ix_quiz_attempts_user_id_lesson_id", "user_id", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    block_id: Mapped[str] = mapped_column(String(40))
    percent: Mapped[int]
    style: Mapped[str] = mapped_column(String(STYLE_LENGTH))
    counted_for_weights: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
