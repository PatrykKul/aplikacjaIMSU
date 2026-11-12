from fastapi import APIRouter, Response, status

from app.core.db import DbSession
from app.modules.curriculum import service
from app.modules.curriculum.models import EnrollmentStatus
from app.modules.curriculum.schemas import (
    CourseCreateRequest,
    CourseEnrollmentResponse,
    CourseResponse,
    CourseSummaryResponse,
    CourseUpdateRequest,
    EnrollmentResponse,
    LessonCreateRequest,
    LessonOrderRequest,
    LessonResponse,
    LessonUpdateRequest,
)
from app.modules.identity.dependencies import CurrentUser, StudentUser, TeacherUser

courses_router = APIRouter(prefix="/courses", tags=["curriculum"])
lessons_router = APIRouter(prefix="/lessons", tags=["curriculum"])


# --- Courses -----------------------------------------------------------------------------------


@courses_router.get("")
def list_courses(db: DbSession, user: CurrentUser) -> list[CourseSummaryResponse]:
    return service.course_summaries(db, service.list_courses(db, user), user)


@courses_router.post("", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreateRequest, db: DbSession, user: TeacherUser) -> CourseResponse:
    return service.course_detail(db, service.create_course(db, user, data), user)


@courses_router.get("/{course_id}")
def get_course(course_id: int, db: DbSession, user: CurrentUser) -> CourseResponse:
    return service.course_detail(db, service.get_visible_course(db, course_id, user), user)


@courses_router.patch("/{course_id}")
def update_course(
    course_id: int, data: CourseUpdateRequest, db: DbSession, user: CurrentUser
) -> CourseResponse:
    return service.course_detail(db, service.update_course(db, course_id, user, data), user)


@courses_router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_course(course_id: int, db: DbSession, user: CurrentUser) -> None:
    service.archive_course(db, course_id, user)


@courses_router.post("/{course_id}/lessons", status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: int, data: LessonCreateRequest, db: DbSession, user: CurrentUser
) -> LessonResponse:
    lesson = service.create_lesson(db, course_id, user, data.title)
    return service.lesson_detail(db, lesson, user)


@courses_router.put("/{course_id}/lessons/order")
def reorder_lessons(
    course_id: int, data: LessonOrderRequest, db: DbSession, user: CurrentUser
) -> CourseResponse:
    course = service.reorder_lessons(db, course_id, user, data.lesson_ids)
    return service.course_detail(db, course, user)


# --- Enrollments -------------------------------------------------------------------------------


@courses_router.post("/{course_id}/enrollment", status_code=status.HTTP_201_CREATED)
def request_enrollment(
    course_id: int, response: Response, db: DbSession, user: StudentUser
) -> EnrollmentResponse:
    enrollment, changed = service.request_enrollment(db, course_id, user)
    if not changed:
        response.status_code = status.HTTP_200_OK
    return EnrollmentResponse.model_validate(enrollment)


@courses_router.get("/{course_id}/enrollments")
def list_enrollments(
    course_id: int, db: DbSession, user: CurrentUser, status: EnrollmentStatus | None = None
) -> list[CourseEnrollmentResponse]:
    return service.course_enrollments(db, course_id, user, status)


@courses_router.post("/{course_id}/enrollments/{student_id}/accept")
def accept_enrollment(
    course_id: int, student_id: int, db: DbSession, user: CurrentUser
) -> EnrollmentResponse:
    enrollment = service.decide_enrollment(
        db, course_id, student_id, user, EnrollmentStatus.ACCEPTED
    )
    return EnrollmentResponse.model_validate(enrollment)


@courses_router.post("/{course_id}/enrollments/{student_id}/reject")
def reject_enrollment(
    course_id: int, student_id: int, db: DbSession, user: CurrentUser
) -> EnrollmentResponse:
    enrollment = service.decide_enrollment(
        db, course_id, student_id, user, EnrollmentStatus.REJECTED
    )
    return EnrollmentResponse.model_validate(enrollment)


# --- Lessons -----------------------------------------------------------------------------------


@lessons_router.get("/{lesson_id}")
def get_lesson(lesson_id: int, db: DbSession, user: CurrentUser) -> LessonResponse:
    # Student: accepted in the course and the lesson unlocked (R10); author and admin: preview
    return service.lesson_detail(db, service.get_study_lesson(db, lesson_id, user), user)


@lessons_router.patch("/{lesson_id}")
def update_lesson(
    lesson_id: int, data: LessonUpdateRequest, db: DbSession, user: CurrentUser
) -> LessonResponse:
    return service.lesson_detail(db, service.update_lesson(db, lesson_id, user, data), user)


@lessons_router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_lesson(lesson_id: int, db: DbSession, user: CurrentUser) -> None:
    service.archive_lesson(db, lesson_id, user)
