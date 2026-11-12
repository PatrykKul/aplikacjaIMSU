"""Learning-style service (v3 skeleton; the engine is built in stage B, see docs/08)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.modules.learning_style.models import SurveyQuestion


def active_questions(db: Session) -> list[SurveyQuestion]:
    return list(
        db.scalars(
            select(SurveyQuestion)
            .options(selectinload(SurveyQuestion.answers))
            .where(SurveyQuestion.is_active)
            .order_by(SurveyQuestion.position, SurveyQuestion.id)
        )
    )
