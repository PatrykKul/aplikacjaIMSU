from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
    text,
    true,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

FORM_LENGTH = 1  # "V", "A" or "K"
TIE_LENGTH = 3  # survey result with a tie, e.g. "VA"
TEXT_LENGTH = 300

# --- Survey --------------------------------------------------------------------------------------


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
    """The filled-in survey (once per student in v3)."""

    __tablename__ = "survey_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    points_v: Mapped[int]
    points_a: Mapped[int]
    points_k: Mapped[int]
    # Leader(s) by points, e.g. "A" or "VA" for a tie
    dominant_style: Mapped[str] = mapped_column(String(TIE_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- Learning profile ----------------------------------------------------------------------------


class LearningProfile(Base):
    """Active style and percentage profile; no row = survey not filled in yet."""

    __tablename__ = "learning_profiles"
    __table_args__ = (
        CheckConstraint("style IS NULL OR style IN ('V', 'A', 'K')", name="style"),
        CheckConstraint(
            "style_source IN ('survey', 'tie_choice', 'manual', 'proposal')", name="style_source"
        ),
        CheckConstraint(
            "percent_v BETWEEN 5 AND 90 AND percent_a BETWEEN 5 AND 90 "
            "AND percent_k BETWEEN 5 AND 90 AND percent_v + percent_a + percent_k = 100",
            name="percentages",
        ),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    # None = survey tie not resolved yet (the student must choose)
    style: Mapped[str | None] = mapped_column(String(FORM_LENGTH))
    style_source: Mapped[str] = mapped_column(String(12))
    percent_v: Mapped[int]
    percent_a: Mapped[int]
    percent_k: Mapped[int]
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    @property
    def percentages(self) -> dict[str, int]:
        return {"V": self.percent_v, "A": self.percent_a, "K": self.percent_k}

    @percentages.setter
    def percentages(self, value: dict[str, int]) -> None:
        self.percent_v, self.percent_a, self.percent_k = value["V"], value["A"], value["K"]


class StyleHistory(Base):
    """Profile after every change (survey, counted quiz result, style change) — for the chart."""

    __tablename__ = "style_history"
    __table_args__ = (Index("ix_style_history_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    percent_v: Mapped[int]
    percent_a: Mapped[int]
    percent_k: Mapped[int]
    style: Mapped[str | None] = mapped_column(String(FORM_LENGTH))
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("decision_events.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# --- Results and lesson forms --------------------------------------------------------------------


class QuizResult(Base):
    """Quiz result in the student model: lesson form, score, whether it changed the profile."""

    __tablename__ = "quiz_results"
    __table_args__ = (
        CheckConstraint("percent BETWEEN 0 AND 100", name="percent"),
        CheckConstraint("form IN ('V', 'A', 'K')", name="form"),
        Index("ix_quiz_results_user_id_lesson_id", "user_id", "lesson_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"))
    draw_id: Mapped[int | None] = mapped_column(ForeignKey("quiz_draws.id", ondelete="SET NULL"))
    form: Mapped[str] = mapped_column(String(FORM_LENGTH))
    percent: Mapped[int]
    passed: Mapped[bool]
    # First attempt in this form in this lesson: the only one that changes the percentages (R2)
    counted: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LessonForm(Base):
    """Explicit form chosen for a lesson; no row = the lesson follows the active style."""

    __tablename__ = "lesson_forms"
    __table_args__ = (CheckConstraint("form IN ('V', 'A', 'K')", name="form"),)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    lesson_id: Mapped[int] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    form: Mapped[str] = mapped_column(String(FORM_LENGTH))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


# --- Proposals, trials, decision log -------------------------------------------------------------


class StyleProposal(Base):
    """Proposal to change the active style for good (R6) or to go back after a trial (R7)."""

    __tablename__ = "style_proposals"
    __table_args__ = (
        CheckConstraint("kind IN ('switch', 'revert')", name="kind"),
        CheckConstraint(
            "status IN ('open', 'accepted', 'rejected', 'expired', 'superseded')", name="status"
        ),
        Index(
            "uq_style_proposals_open_user_id",
            "user_id",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(10))
    from_style: Mapped[str] = mapped_column(String(FORM_LENGTH))
    to_style: Mapped[str] = mapped_column(String(FORM_LENGTH))
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(12), server_default="open")
    # Number of the student's counted results when decided (a rejection waits for 2 new ones)
    counted_at_decision: Mapped[int | None]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StyleTrial(Base):
    """Two lessons after a style change, compared with the average before it (R7)."""

    __tablename__ = "style_trials"
    __table_args__ = (
        CheckConstraint("source IN ('proposal', 'manual')", name="source"),
        CheckConstraint(
            "result IS NULL OR result IN "
            "('helped', 'neutral', 'worse', 'no_baseline', 'cancelled')",
            name="result",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    from_style: Mapped[str] = mapped_column(String(FORM_LENGTH))
    to_style: Mapped[str] = mapped_column(String(FORM_LENGTH))
    source: Mapped[str] = mapped_column(String(10))
    before_average: Mapped[int | None]
    after_average: Mapped[int | None]
    # None while running or when interrupted after counted lessons; "cancelled" (R7a)
    result: Mapped[str | None] = mapped_column(String(12))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # None = trial still running
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class DecisionEvent(Base):
    """Decision log: every event with the data it came from (types in docs/moduly)."""

    __tablename__ = "decision_events"
    __table_args__ = (Index("ix_decision_events_user_id_created_at", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(40))
    course_id: Mapped[int | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), index=True
    )
    lesson_id: Mapped[int | None] = mapped_column(ForeignKey("lessons.id", ondelete="SET NULL"))
    data: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
