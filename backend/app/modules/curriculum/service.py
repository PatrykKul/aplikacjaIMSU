from dataclasses import dataclass

from sqlalchemy import exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.curriculum import progress
from app.modules.curriculum.models import (
    Course,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonCompletion,
)
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


def is_accepted(db: Session, course_id: int, student_id: int) -> bool:
    """Whether the student's enrollment in the course is accepted."""
    return bool(
        db.scalar(
            select(
                exists().where(
                    Enrollment.course_id == course_id,
                    Enrollment.student_id == student_id,
                    Enrollment.status == EnrollmentStatus.ACCEPTED,
                )
            )
        )
    )


def can_view_course(db: Session, course: Course, user: User) -> bool:
    """Admin: every course; teacher: own; student: published or accepted in it."""
    if user.role == UserRole.ADMIN:
        return True
    if course.is_archived:
        return False
    if course.owner_id == user.id:
        return True
    if user.role != UserRole.STUDENT:
        return False
    return course.is_published or is_accepted(db, course.id, user.id)


def list_courses(db: Session, user: User) -> list[Course]:
    """Teacher: own courses; student: published ones and those accepted in; admin: all."""
    query = select(Course).order_by(Course.created_at.desc(), Course.id.desc())
    if user.role == UserRole.TEACHER:
        query = query.where(Course.owner_id == user.id, Course.is_archived.is_(False))
    elif user.role == UserRole.STUDENT:
        accepted = exists().where(
            Enrollment.course_id == Course.id,
            Enrollment.student_id == user.id,
            Enrollment.status == EnrollmentStatus.ACCEPTED,
        )
        query = query.where(Course.is_archived.is_(False), Course.is_published | accepted)
    return list(db.scalars(query))


def get_visible_course(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if course is None or not can_view_course(db, course, user):
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
    if lesson is None or not can_view_course(db, lesson.course, user):
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


# --- Study access and progress (used by learning_style and assessment) -------------------------


@dataclass(frozen=True)
class UnlockedLesson:
    id: int
    title: str
    number: int


def published_lessons(course: Course) -> list[Lesson]:
    """Lessons a student can study, in course order."""
    return [lesson for lesson in active_lessons(course) if lesson.is_published]


def passed_lesson_ids(db: Session, user_id: int, lesson_ids: list[int]) -> set[int]:
    if not lesson_ids:
        return set()
    return set(
        db.scalars(
            select(LessonCompletion.lesson_id).where(
                LessonCompletion.user_id == user_id, LessonCompletion.lesson_id.in_(lesson_ids)
            )
        )
    )


def student_lesson_states(db: Session, course: Course, user_id: int) -> list[progress.LessonState]:
    ids = [lesson.id for lesson in published_lessons(course)]
    return progress.lesson_states(ids, passed_lesson_ids(db, user_id, ids))


def get_study_lesson(db: Session, lesson_id: int, user: User) -> Lesson:
    """A lesson whose content the user may study.

    Student: published lesson of a course they are accepted in, unlocked (R10).
    Author and admin: any visible lesson (preview).
    """
    lesson = get_visible_lesson(db, lesson_id, user)
    if user.role != UserRole.STUDENT:
        return lesson
    if not lesson.is_published:
        raise AppError(404, "LESSON_NOT_FOUND")
    if not is_accepted(db, lesson.course_id, user.id):
        raise AppError(403, "ENROLLMENT_REQUIRED")
    state = next(
        s for s in student_lesson_states(db, lesson.course, user.id) if s.lesson_id == lesson.id
    )
    if state.state == progress.LOCKED:
        required = db.get(Lesson, state.required_lesson_id)
        raise AppError(
            403,
            "LESSON_LOCKED",
            required_lesson={
                "id": state.required_lesson_id,
                "title": required.title if required else "",
                "number": state.required_number,
            },
        )
    return lesson


def mark_lesson_passed(db: Session, user_id: int, lesson_id: int) -> UnlockedLesson | None:
    """Record the first pass of a lesson (no commit); returns the lesson it newly unlocks."""
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise ValueError(f"lesson {lesson_id} does not exist")
    inserted = db.execute(
        insert(LessonCompletion)
        .values(user_id=user_id, lesson_id=lesson_id)
        .on_conflict_do_nothing()
        .returning(LessonCompletion.lesson_id)
    ).first()
    if inserted is None:
        return None
    ids = [item.id for item in published_lessons(lesson.course)]
    next_id = progress.next_lesson_id(ids, lesson_id)
    if next_id is None or next_id in passed_lesson_ids(db, user_id, [next_id]):
        return None
    next_lesson = db.get(Lesson, next_id)
    assert next_lesson is not None
    return UnlockedLesson(id=next_id, title=next_lesson.title, number=ids.index(next_id) + 1)


def accepted_student_ids(db: Session, course_id: int) -> list[int]:
    return list(
        db.scalars(
            select(Enrollment.student_id)
            .where(
                Enrollment.course_id == course_id, Enrollment.status == EnrollmentStatus.ACCEPTED
            )
            .order_by(Enrollment.student_id)
        )
    )


def course_progress(db: Session, course: Course, user_id: int) -> tuple[int, int]:
    """(passed, total) published lessons of the course."""
    ids = [lesson.id for lesson in published_lessons(course)]
    return len(passed_lesson_ids(db, user_id, ids)), len(ids)


def lesson_number(lesson: Lesson) -> int | None:
    """1-based position among the published lessons (None for an unpublished lesson)."""
    ids = [item.id for item in published_lessons(lesson.course)]
    return ids.index(lesson.id) + 1 if lesson.id in ids else None
