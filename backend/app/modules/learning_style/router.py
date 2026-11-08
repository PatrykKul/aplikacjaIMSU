from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.db import DbSession
from app.modules.identity.dependencies import CurrentUser, require_role
from app.modules.identity.models import User, UserRole
from app.modules.learning_style import service
from app.modules.learning_style.schemas import (
    LearningProfileResponse,
    PersonalizedBlocksResponse,
    StyleChangeRequest,
    SurveyQuestionResponse,
    SurveyResultResponse,
    SurveySubmitRequest,
)

StudentUser = Annotated[User, Depends(require_role(UserRole.STUDENT))]

survey_router = APIRouter(prefix="/survey", tags=["learning-style"])
profile_router = APIRouter(prefix="/profile/learning-style", tags=["learning-style"])
personalized_router = APIRouter(prefix="/lessons", tags=["learning-style"])


# --- Survey --------------------------------------------------------------------------------------


@survey_router.get("/questions")
def get_questions(db: DbSession, _user: CurrentUser) -> list[SurveyQuestionResponse]:
    # The response schema has no `style`, so the answer key is never sent
    return [SurveyQuestionResponse.model_validate(q) for q in service.active_questions(db)]


@survey_router.post("/answers")
def submit_answers(
    data: SurveySubmitRequest, db: DbSession, user: StudentUser
) -> LearningProfileResponse:
    service.submit_survey(db, user, data.answers)
    return service.profile_response(db, user)


@survey_router.get("/results")
def get_results(db: DbSession, user: StudentUser) -> list[SurveyResultResponse]:
    return [service.result_response(r) for r in service.results_history(db, user.id)]


# --- Profile -------------------------------------------------------------------------------------


@profile_router.get("")
def get_profile(db: DbSession, user: CurrentUser) -> LearningProfileResponse:
    return service.profile_response(db, user)


@profile_router.put("")
def change_style(
    data: StyleChangeRequest, db: DbSession, user: StudentUser
) -> LearningProfileResponse:
    service.set_manual_style(db, user, data.style)
    return service.profile_response(db, user)


@profile_router.delete("")
def restore_style(db: DbSession, user: StudentUser) -> LearningProfileResponse:
    service.restore_survey_style(db, user)
    return service.profile_response(db, user)


@profile_router.post("/proposal/accept")
def accept_proposal(db: DbSession, user: StudentUser) -> LearningProfileResponse:
    service.accept_proposal(db, user)
    return service.profile_response(db, user)


@profile_router.post("/proposal/reject")
def reject_proposal(db: DbSession, user: StudentUser) -> LearningProfileResponse:
    service.reject_proposal(db, user)
    return service.profile_response(db, user)


# --- Lessons -------------------------------------------------------------------------------------


@personalized_router.get("/{lesson_id}/personalized-blocks")
def get_personalized_blocks(
    lesson_id: int, db: DbSession, user: CurrentUser
) -> PersonalizedBlocksResponse:
    return service.personalized_blocks(db, lesson_id, user)
