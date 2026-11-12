from fastapi import APIRouter

from app.core.db import DbSession
from app.modules.identity.dependencies import CurrentUser
from app.modules.learning_style import service
from app.modules.learning_style.schemas import SurveyQuestionResponse

survey_router = APIRouter(prefix="/survey", tags=["learning-style"])


@survey_router.get("/questions")
def get_questions(db: DbSession, _user: CurrentUser) -> list[SurveyQuestionResponse]:
    # The response schema has no `style`, so the answer key is never sent
    return [SurveyQuestionResponse.model_validate(q) for q in service.active_questions(db)]
