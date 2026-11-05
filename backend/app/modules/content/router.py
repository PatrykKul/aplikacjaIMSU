from fastapi import APIRouter

from app.core.db import DbSession
from app.modules.content import service
from app.modules.content.schemas import (
    CheckRequest,
    CheckResponse,
    LessonResponse,
    LessonSummaryResponse,
)
from app.modules.identity.dependencies import CurrentUser

router = APIRouter(tags=["lessons"])


@router.get("/skills/{skill_id}/lessons")
def list_lessons(skill_id: int, db: DbSession, user: CurrentUser) -> list[LessonSummaryResponse]:
    return [service.lesson_summary(lesson) for lesson in service.list_lessons(db, skill_id, user)]


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int, db: DbSession, user: CurrentUser) -> LessonResponse:
    return service.lesson_response(service.get_lesson(db, lesson_id, user))


@router.post("/lessons/{lesson_id}/steps/{step_key}/check")
def check_step(
    lesson_id: int, step_key: str, data: CheckRequest, db: DbSession, user: CurrentUser
) -> CheckResponse:
    result = service.check_step(db, lesson_id, step_key, data.answer, data.reveal, user)
    return CheckResponse.model_validate(result)
