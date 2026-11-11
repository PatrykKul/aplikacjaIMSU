from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.db import DbSession
from app.modules.curriculum import classrooms, service
from app.modules.curriculum.schemas import (
    ClassroomCreateRequest,
    ClassroomResponse,
    ClassroomSummaryResponse,
    ClassroomUpdateRequest,
    CourseCreateRequest,
    CourseResponse,
    CourseSummaryResponse,
    CourseUpdateRequest,
    LessonCreateRequest,
    LessonOrderRequest,
    LessonResponse,
    LessonUpdateRequest,
)
from app.modules.identity.dependencies import CurrentUser, TeacherUser, require_role
from app.modules.identity.models import User, UserRole

courses_router = APIRouter(prefix="/courses", tags=["curriculum"])
lessons_router = APIRouter(prefix="/lessons", tags=["curriculum"])
classrooms_router = APIRouter(prefix="/classrooms", tags=["curriculum"])

ClassroomUser = Annotated[User, Depends(require_role(UserRole.TEACHER, UserRole.STUDENT))]
"""Who opens classrooms: the teacher and the classroom's students (admins have no classrooms)."""


@courses_router.get("")
def list_courses(db: DbSession, user: CurrentUser) -> list[CourseSummaryResponse]:
    return [CourseSummaryResponse.model_validate(c) for c in service.list_courses(db, user)]


@courses_router.post("", status_code=status.HTTP_201_CREATED)
def create_course(data: CourseCreateRequest, db: DbSession, user: TeacherUser) -> CourseResponse:
    return service.course_detail(service.create_course(db, user, data))


@courses_router.get("/{course_id}")
def get_course(course_id: int, db: DbSession, user: CurrentUser) -> CourseResponse:
    return service.course_detail(service.get_visible_course(db, course_id, user))


@courses_router.patch("/{course_id}")
def update_course(
    course_id: int, data: CourseUpdateRequest, db: DbSession, user: CurrentUser
) -> CourseResponse:
    return service.course_detail(service.update_course(db, course_id, user, data))


@courses_router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_course(course_id: int, db: DbSession, user: CurrentUser) -> None:
    service.archive_course(db, course_id, user)


@courses_router.post("/{course_id}/lessons", status_code=status.HTTP_201_CREATED)
def create_lesson(
    course_id: int, data: LessonCreateRequest, db: DbSession, user: CurrentUser
) -> LessonResponse:
    return service.lesson_detail(service.create_lesson(db, course_id, user, data.title))


@courses_router.put("/{course_id}/lessons/order")
def reorder_lessons(
    course_id: int, data: LessonOrderRequest, db: DbSession, user: CurrentUser
) -> CourseResponse:
    return service.course_detail(service.reorder_lessons(db, course_id, user, data.lesson_ids))


@lessons_router.get("/{lesson_id}")
def get_lesson(lesson_id: int, db: DbSession, user: CurrentUser) -> LessonResponse:
    return service.lesson_detail(service.get_visible_lesson(db, lesson_id, user))


@lessons_router.patch("/{lesson_id}")
def rename_lesson(
    lesson_id: int, data: LessonUpdateRequest, db: DbSession, user: CurrentUser
) -> LessonResponse:
    return service.lesson_detail(service.rename_lesson(db, lesson_id, user, data.title))


@lessons_router.delete("/{lesson_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_lesson(lesson_id: int, db: DbSession, user: CurrentUser) -> None:
    service.archive_lesson(db, lesson_id, user)


# --- Classrooms --------------------------------------------------------------------------------


@classrooms_router.get("")
def list_classrooms(db: DbSession, user: ClassroomUser) -> list[ClassroomSummaryResponse]:
    return classrooms.list_classrooms(db, user)


@classrooms_router.post("", status_code=status.HTTP_201_CREATED)
def create_classroom(
    data: ClassroomCreateRequest, db: DbSession, user: TeacherUser
) -> ClassroomResponse:
    classroom = classrooms.create_classroom(db, user, data.name)
    return classrooms.teacher_classroom_detail(db, classroom, user)


@classrooms_router.get("/{classroom_id}")
def get_classroom(classroom_id: int, db: DbSession, user: ClassroomUser) -> ClassroomResponse:
    classroom = classrooms.get_visible_classroom(db, classroom_id, user)
    return classrooms.classroom_detail(db, classroom, user)


@classrooms_router.patch("/{classroom_id}")
def rename_classroom(
    classroom_id: int, data: ClassroomUpdateRequest, db: DbSession, user: TeacherUser
) -> ClassroomResponse:
    classroom = classrooms.rename_classroom(db, classroom_id, user, data.name)
    return classrooms.teacher_classroom_detail(db, classroom, user)


@classrooms_router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_classroom(classroom_id: int, db: DbSession, user: TeacherUser) -> None:
    classrooms.delete_classroom(db, classroom_id, user)


@classrooms_router.put(
    "/{classroom_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT
)
def add_student(classroom_id: int, student_id: int, db: DbSession, user: TeacherUser) -> None:
    classrooms.add_student(db, classroom_id, user, student_id)


@classrooms_router.delete(
    "/{classroom_id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_student(classroom_id: int, student_id: int, db: DbSession, user: TeacherUser) -> None:
    classrooms.remove_student(db, classroom_id, user, student_id)


@classrooms_router.put(
    "/{classroom_id}/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT
)
def assign_course(classroom_id: int, course_id: int, db: DbSession, user: TeacherUser) -> None:
    classrooms.assign_course(db, classroom_id, user, course_id)


@classrooms_router.delete(
    "/{classroom_id}/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT
)
def unassign_course(classroom_id: int, course_id: int, db: DbSession, user: TeacherUser) -> None:
    classrooms.unassign_course(db, classroom_id, user, course_id)
