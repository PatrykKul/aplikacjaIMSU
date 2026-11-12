from fastapi import APIRouter

from app.core.db import DbSession
from app.modules.authoring import service
from app.modules.authoring.schemas import PublicationRequest, ReadinessResponse
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.schemas import LessonResponse
from app.modules.identity.dependencies import CurrentUser

authoring_router = APIRouter(prefix="/lessons", tags=["authoring"])


@authoring_router.get("/{lesson_id}/readiness", response_model_exclude_none=True)
def get_readiness(lesson_id: int, db: DbSession, user: CurrentUser) -> ReadinessResponse:
    issues = service.get_readiness(db, lesson_id, user)
    return ReadinessResponse.model_validate({"ready": not issues, "issues": issues})


@authoring_router.put("/{lesson_id}/publication")
def set_publication(
    lesson_id: int, data: PublicationRequest, db: DbSession, user: CurrentUser
) -> LessonResponse:
    lesson = service.set_publication(db, lesson_id, user, data.is_published)
    return curriculum.lesson_detail(db, lesson, user)
