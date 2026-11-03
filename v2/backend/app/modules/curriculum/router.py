from fastapi import APIRouter

from app.core.db import DbSession
from app.modules.curriculum import service
from app.modules.curriculum.schemas import (
    CourseResponse,
    CourseSummaryResponse,
    CourseUpdateRequest,
    SkillResponse,
)
from app.modules.identity.dependencies import AdminUser, CurrentUser

router = APIRouter(tags=["curriculum"])


@router.get("/courses")
def list_courses(db: DbSession, user: CurrentUser) -> list[CourseSummaryResponse]:
    return [CourseSummaryResponse.model_validate(c) for c in service.list_courses(db, user)]


@router.get("/courses/{course_id}")
def get_course(course_id: int, db: DbSession, user: CurrentUser) -> CourseResponse:
    return service.get_course_detail(db, course_id, user)


@router.patch("/courses/{course_id}")
def update_course(
    course_id: int, data: CourseUpdateRequest, db: DbSession, _admin: AdminUser
) -> CourseSummaryResponse:
    course = service.set_published(db, course_id, data.is_published)
    return CourseSummaryResponse.model_validate(course)


@router.get("/skills/{skill_id}")
def get_skill(skill_id: int, db: DbSession, user: CurrentUser) -> SkillResponse:
    return service.get_skill_detail(db, skill_id, user)
