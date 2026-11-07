from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.curriculum.models import Course, Lesson
from app.modules.curriculum.schemas import (
    CourseCreateRequest,
    CourseResponse,
    CourseSummaryResponse,
    CourseUpdateRequest,
    LessonCourseResponse,
    LessonResponse,
    LessonSummaryResponse,
)
from app.modules.identity.models import User, UserRole


def can_view_course(course: Course, user: User) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    if course.is_archived:
        return False
    if course.owner_id == user.id:
        return True
    return user.role == UserRole.STUDENT and course.is_published


def list_courses(db: Session, user: User) -> list[Course]:
    query = select(Course).order_by(Course.created_at.desc(), Course.id.desc())
    if user.role == UserRole.TEACHER:
        query = query.where(Course.owner_id == user.id, Course.is_archived.is_(False))
    elif user.role == UserRole.STUDENT:
        query = query.where(Course.is_published, Course.is_archived.is_(False))
    return list(db.scalars(query))


def get_visible_course(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if course is None or not can_view_course(course, user):
        raise AppError(404, "COURSE_NOT_FOUND")
    return course


def get_owned_course(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if course is None or course.is_archived or course.owner_id != user.id:
        raise AppError(404, "COURSE_NOT_FOUND")
    return course


def active_lessons(course: Course) -> list[Lesson]:
    return [lesson for lesson in course.lessons if not lesson.is_archived]


def course_detail(course: Course) -> CourseResponse:
    return CourseResponse(
        **CourseSummaryResponse.model_validate(course).model_dump(),
        introduction=course.introduction,
        lessons=[LessonSummaryResponse.model_validate(lesson) for lesson in active_lessons(course)],
    )


def create_course(db: Session, owner: User, data: CourseCreateRequest) -> Course:
    course = Course(owner_id=owner.id, title=data.title, description=data.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course_id: int, user: User, data: CourseUpdateRequest) -> Course:
    course = get_owned_course(db, course_id, user)
    if data.title is not None:
        course.title = data.title
    if data.description is not None:
        course.description = data.description
    if data.introduction is not None:
        course.introduction = data.introduction
    if data.is_published is not None:
        course.is_published = data.is_published
    db.commit()
    db.refresh(course)
    return course


def archive_course(db: Session, course_id: int, user: User) -> None:
    course = get_owned_course(db, course_id, user)
    course.is_archived = True
    db.commit()


# --- Lessons -----------------------------------------------------------------------------------


def create_lesson(db: Session, course_id: int, user: User, title: str) -> Lesson:
    course = get_owned_course(db, course_id, user)
    last = db.scalar(select(func.max(Lesson.position)).where(Lesson.course_id == course.id))
    lesson = Lesson(title=title, position=0 if last is None else last + 1)
    course.lessons.append(lesson)  # keeps the loaded collection in sync
    db.commit()
    db.refresh(lesson)
    return lesson


def reorder_lessons(db: Session, course_id: int, user: User, lesson_ids: list[int]) -> Course:
    """Set the order of all active lessons; the list must name each of them exactly once."""
    course = get_owned_course(db, course_id, user)
    lessons = {lesson.id: lesson for lesson in active_lessons(course)}
    if len(lesson_ids) != len(lessons) or set(lesson_ids) != lessons.keys():
        raise AppError(400, "LESSON_ORDER_MISMATCH")
    for position, lesson_id in enumerate(lesson_ids):
        lessons[lesson_id].position = position
    db.commit()
    db.refresh(course, ["lessons"])  # reload the collection in the new order
    return course


def _lesson_with_course(db: Session, lesson_id: int) -> Lesson | None:
    lesson = db.get(Lesson, lesson_id)
    return None if lesson is None or lesson.is_archived else lesson


def get_visible_lesson(db: Session, lesson_id: int, user: User) -> Lesson:
    """For other modules too: a lesson the user may open."""
    lesson = _lesson_with_course(db, lesson_id)
    if lesson is None or not can_view_course(lesson.course, user):
        raise AppError(404, "LESSON_NOT_FOUND")
    return lesson


def get_owned_lesson(db: Session, lesson_id: int, user: User) -> Lesson:
    """For other modules too: a lesson the user may edit."""
    lesson = _lesson_with_course(db, lesson_id)
    if lesson is None or lesson.course.is_archived or lesson.course.owner_id != user.id:
        raise AppError(404, "LESSON_NOT_FOUND")
    return lesson


def lesson_detail(lesson: Lesson) -> LessonResponse:
    course = lesson.course
    ids = [item.id for item in active_lessons(course)]
    index = ids.index(lesson.id)
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        course=LessonCourseResponse(id=course.id, title=course.title, owner_id=course.owner_id),
        previous_lesson_id=ids[index - 1] if index > 0 else None,
        next_lesson_id=ids[index + 1] if index + 1 < len(ids) else None,
    )


def rename_lesson(db: Session, lesson_id: int, user: User, title: str) -> Lesson:
    lesson = get_owned_lesson(db, lesson_id, user)
    lesson.title = title
    db.commit()
    db.refresh(lesson)
    return lesson


def archive_lesson(db: Session, lesson_id: int, user: User) -> None:
    lesson = get_owned_lesson(db, lesson_id, user)
    lesson.is_archived = True
    db.commit()
