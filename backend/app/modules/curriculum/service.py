from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import exists, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.modules.curriculum import progress, readiness
from app.modules.curriculum.models import (
    Course,
    CourseOwnerChange,
    Enrollment,
    EnrollmentStatus,
    Lesson,
    LessonCompletion,
)
from app.modules.curriculum.schemas import (
    CourseCreateRequest,
    CourseEnrollmentResponse,
    CourseLessonResponse,
    CourseOwnerResponse,
    CourseProgressResponse,
    CourseResponse,
    CourseSummaryResponse,
    CourseUpdateRequest,
    LessonCourseResponse,
    LessonResponse,
    LessonUpdateRequest,
)
from app.modules.identity import service as identity
from app.modules.identity.models import User, UserRole
from app.modules.identity.schemas import StudentResponse

# --- Visibility and ownership ------------------------------------------------------------------


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


def is_manager(course: Course, user: User) -> bool:
    """The author or the admin: sees every active lesson, not only the published ones."""
    return user.role == UserRole.ADMIN or course.owner_id == user.id


def list_courses(db: Session, user: User) -> list[Course]:
    """Teacher: own courses; student: published ones and those accepted in; admin: all."""
    identity.require_approved(user)
    query = (
        select(Course)
        .options(selectinload(Course.lessons))
        .order_by(Course.created_at.desc(), Course.id.desc())
    )
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
    identity.require_approved(user)
    course = db.get(Course, course_id)
    if course is None or not can_view_course(db, course, user):
        raise AppError(404, "COURSE_NOT_FOUND")
    return course


def get_owned_course(db: Session, course_id: int, user: User) -> Course:
    identity.require_approved(user)
    course = db.get(Course, course_id)
    if course is None or course.is_archived or course.owner_id != user.id:
        raise AppError(404, "COURSE_NOT_FOUND")
    return course


def active_lessons(course: Course) -> list[Lesson]:
    return [lesson for lesson in course.lessons if not lesson.is_archived]


def _shown_lessons(course: Course, user: User) -> list[Lesson]:
    """Lessons the user sees in the course: all active ones for a manager, else published."""
    return active_lessons(course) if is_manager(course, user) else published_lessons(course)


# --- Course responses --------------------------------------------------------------------------


def course_summaries(
    db: Session, courses: Sequence[Course], user: User
) -> list[CourseSummaryResponse]:
    """Course list items with the viewer's data (enrollment, progress, pending requests)."""
    course_ids = [course.id for course in courses]
    owners = {
        owner.id: owner for owner in identity.get_users(db, {course.owner_id for course in courses})
    }
    statuses: dict[int, EnrollmentStatus] = {}
    passed: set[int] = set()
    pending: dict[int, int] = {}
    if user.role == UserRole.STUDENT and course_ids:
        statuses = dict(
            db.execute(
                select(Enrollment.course_id, Enrollment.status).where(
                    Enrollment.student_id == user.id, Enrollment.course_id.in_(course_ids)
                )
            ).all()
        )
        lesson_ids = [lesson.id for course in courses for lesson in published_lessons(course)]
        passed = passed_lesson_ids(db, user.id, lesson_ids)
    owned = [course.id for course in courses if course.owner_id == user.id]
    if owned:
        pending = dict(
            db.execute(
                select(Enrollment.course_id, func.count())
                .where(
                    Enrollment.course_id.in_(owned),
                    Enrollment.status == EnrollmentStatus.PENDING,
                )
                .group_by(Enrollment.course_id)
            ).all()
        )

    summaries = []
    for course in courses:
        owner = owners.get(course.owner_id)
        status = statuses.get(course.id)
        course_progress_value = None
        if status == EnrollmentStatus.ACCEPTED:
            ids = [lesson.id for lesson in published_lessons(course)]
            course_progress_value = CourseProgressResponse(
                passed=len(passed.intersection(ids)), total=len(ids)
            )
        summaries.append(
            CourseSummaryResponse(
                id=course.id,
                title=course.title,
                description=course.description,
                owner=CourseOwnerResponse(
                    id=course.owner_id, display_name=owner.display_name if owner else ""
                ),
                is_published=course.is_published,
                is_archived=course.is_archived,
                lesson_count=len(_shown_lessons(course, user)),
                enrollment_status=status,
                progress=course_progress_value,
                pending_requests=pending.get(course.id, 0) if course.owner_id == user.id else None,
                updated_at=course.updated_at,
            )
        )
    return summaries


def course_detail(db: Session, course: Course, user: User) -> CourseResponse:
    """The course page: summary data, texts and numbered lessons (states for a student)."""
    summary = course_summaries(db, [course], user)[0]
    manager = is_manager(course, user)
    states: dict[int, progress.LessonState] = {}
    if summary.enrollment_status == EnrollmentStatus.ACCEPTED:
        states = {s.lesson_id: s for s in student_lesson_states(db, course, user.id)}
    lessons = []
    for number, lesson in enumerate(_shown_lessons(course, user), start=1):
        state = states.get(lesson.id)
        lessons.append(
            CourseLessonResponse(
                id=lesson.id,
                title=lesson.title,
                number=number,
                outline=lesson.outline,
                is_published=lesson.is_published if manager else None,
                state=state.state if state else None,
                required_lesson_number=state.required_number if state else None,
            )
        )
    return CourseResponse(
        **summary.model_dump(),
        introduction=course.introduction,
        summary=course.summary,
        lessons=lessons,
    )


# --- Course changes ----------------------------------------------------------------------------


def create_course(db: Session, owner: User, data: CourseCreateRequest) -> Course:
    course = Course(owner_id=owner.id, title=data.title, description=data.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course_id: int, user: User, data: CourseUpdateRequest) -> Course:
    course = get_owned_course(db, course_id, user)
    if data.is_published and not published_lessons(course):
        raise AppError(409, "COURSE_HAS_NO_PUBLISHED_LESSONS")
    # Only the fields sent; `null` (allowed in the texts only) clears them
    for field in data.model_fields_set:
        setattr(course, field, getattr(data, field))
    db.commit()
    db.refresh(course)
    return course


def change_owner(db: Session, course_id: int, admin: User, owner_id: int) -> Course:
    """The admin moves a course to another approved teacher (D56); every change is logged.

    Enrollments, completions and results stay with the course. The same owner: no change.
    """
    if admin.role != UserRole.ADMIN:
        raise AppError(403, "FORBIDDEN")
    course = db.get(Course, course_id)
    if course is None:
        raise AppError(404, "COURSE_NOT_FOUND")
    owner = identity.get_approved_teacher(db, owner_id)
    if owner.id == course.owner_id:
        return course
    db.add(
        CourseOwnerChange(
            course_id=course.id,
            from_owner_id=course.owner_id,
            to_owner_id=owner.id,
            changed_by_id=admin.id,
        )
    )
    course.owner_id = owner.id
    db.commit()
    db.refresh(course)
    return course


def archive_course(db: Session, course_id: int, user: User) -> None:
    course = get_owned_course(db, course_id, user)
    course.is_archived = True
    db.commit()


# --- Lessons -----------------------------------------------------------------------------------


def create_lesson(db: Session, course_id: int, user: User, title: str) -> Lesson:
    """A new unpublished lesson at the end of the course."""
    course = get_owned_course(db, course_id, user)
    last = db.scalar(select(func.max(Lesson.position)).where(Lesson.course_id == course.id))
    lesson = Lesson(title=title, position=0 if last is None else last + 1, is_published=False)
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
    """For other modules too: a lesson of a course the user can see (no study rules)."""
    identity.require_approved(user)
    lesson = _lesson_with_course(db, lesson_id)
    if lesson is None or not can_view_course(db, lesson.course, user):
        raise AppError(404, "LESSON_NOT_FOUND")
    return lesson


def get_owned_lesson(db: Session, lesson_id: int, user: User) -> Lesson:
    """For other modules too: a lesson the user may edit."""
    identity.require_approved(user)
    lesson = _lesson_with_course(db, lesson_id)
    if lesson is None or lesson.course.is_archived or lesson.course.owner_id != user.id:
        raise AppError(404, "LESSON_NOT_FOUND")
    return lesson


def lesson_detail(db: Session, lesson: Lesson, user: User) -> LessonResponse:
    """The lesson as the user sees it: numbering and neighbours among the lessons they see."""
    course = lesson.course
    ids = [item.id for item in _shown_lessons(course, user)]
    if lesson.id not in ids:  # an unpublished lesson is never shown to a student
        raise AppError(404, "LESSON_NOT_FOUND")
    index = ids.index(lesson.id)
    next_id = ids[index + 1] if index + 1 < len(ids) else None
    next_unlocked = None
    if user.role == UserRole.STUDENT:
        states = {s.lesson_id: s.state for s in student_lesson_states(db, course, user.id)}
        next_unlocked = next_id is not None and states.get(next_id) != progress.LOCKED
    return LessonResponse(
        id=lesson.id,
        title=lesson.title,
        number=index + 1,
        outline=lesson.outline,
        conclusions=lesson.conclusions,
        is_published=lesson.is_published,
        course=LessonCourseResponse(id=course.id, title=course.title, owner_id=course.owner_id),
        previous_lesson_id=ids[index - 1] if index > 0 else None,
        next_lesson_id=next_id,
        next_lesson_unlocked=next_unlocked,
    )


def lesson_issues(lesson: Lesson) -> list[readiness.Issue]:
    """For authoring: what the outline and conclusions lack before publication (R11)."""
    return readiness.lesson_issues(lesson.outline, lesson.conclusions)


def _new_issues(before: list[readiness.Issue], after: list[readiness.Issue]) -> list:
    return [issue for issue in after if issue not in before]


def update_lesson(db: Session, lesson_id: int, user: User, data: LessonUpdateRequest) -> Lesson:
    """Title, outline and conclusions; a published lesson must stay complete (R11)."""
    lesson = get_owned_lesson(db, lesson_id, user)
    fields = data.model_fields_set
    outline = data.outline if "outline" in fields else lesson.outline
    conclusions = data.conclusions if "conclusions" in fields else lesson.conclusions
    if lesson.is_published:
        missing = _new_issues(lesson_issues(lesson), readiness.lesson_issues(outline, conclusions))
        if missing:
            raise AppError(409, "PUBLISHED_LESSON_INCOMPLETE", issues=missing)
    if "title" in fields and data.title is not None:
        lesson.title = data.title
    lesson.outline = outline
    lesson.conclusions = conclusions
    db.commit()
    db.refresh(lesson)
    return lesson


def _check_not_last_published(lesson: Lesson) -> None:
    """A published course keeps at least one published lesson."""
    course = lesson.course
    if course.is_published and [item.id for item in published_lessons(course)] == [lesson.id]:
        raise AppError(409, "LAST_PUBLISHED_LESSON")


def set_lesson_published(db: Session, lesson: Lesson, is_published: bool) -> Lesson:
    """For authoring (which checks readiness first): publish or withdraw an owned lesson."""
    if lesson.is_published == is_published:
        return lesson
    if not is_published:
        _check_not_last_published(lesson)
    lesson.is_published = is_published
    db.commit()
    db.refresh(lesson)
    return lesson


def archive_lesson(db: Session, lesson_id: int, user: User) -> None:
    lesson = get_owned_lesson(db, lesson_id, user)
    if lesson.is_published:
        _check_not_last_published(lesson)
    lesson.is_archived = True
    db.commit()


# --- Enrollments -------------------------------------------------------------------------------


def _enrollment(db: Session, course_id: int, student_id: int) -> Enrollment | None:
    return db.scalar(
        select(Enrollment).where(
            Enrollment.course_id == course_id, Enrollment.student_id == student_id
        )
    )


def request_enrollment(db: Session, course_id: int, student: User) -> tuple[Enrollment, bool]:
    """A student asks to join a visible course; returns (enrollment, whether it changed).

    Pending request: no change. Rejected one: asks again (pending, no decision).
    """
    course = get_visible_course(db, course_id, student)
    enrollment = _enrollment(db, course.id, student.id)
    if enrollment is not None and enrollment.status == EnrollmentStatus.ACCEPTED:
        raise AppError(409, "ALREADY_ENROLLED")
    if enrollment is not None and enrollment.status == EnrollmentStatus.PENDING:
        return enrollment, False
    if enrollment is None:
        enrollment = Enrollment(
            course_id=course.id, student_id=student.id, status=EnrollmentStatus.PENDING
        )
        db.add(enrollment)
    else:
        enrollment.status = EnrollmentStatus.PENDING
        enrollment.requested_at = func.now()
        enrollment.decided_at = None
    db.commit()
    db.refresh(enrollment)
    return enrollment, True


def course_enrollments(
    db: Session, course_id: int, user: User, status: EnrollmentStatus | None = None
) -> list[CourseEnrollmentResponse]:
    """Enrollment requests of an owned course, oldest request first."""
    course = get_owned_course(db, course_id, user)
    query = select(Enrollment).where(Enrollment.course_id == course.id)
    if status is not None:
        query = query.where(Enrollment.status == status)
    enrollments = list(db.scalars(query.order_by(Enrollment.requested_at, Enrollment.id)))
    students = {
        student.id: student
        for student in identity.get_users(db, {enrollment.student_id for enrollment in enrollments})
    }
    return [
        CourseEnrollmentResponse(
            student=StudentResponse.model_validate(students[enrollment.student_id]),
            status=enrollment.status,
            requested_at=enrollment.requested_at,
            decided_at=enrollment.decided_at,
        )
        for enrollment in enrollments
        if enrollment.student_id in students
    ]


def decide_enrollment(
    db: Session, course_id: int, student_id: int, user: User, status: EnrollmentStatus
) -> Enrollment:
    """The author accepts or rejects a request; repeating a decision changes nothing."""
    course = get_owned_course(db, course_id, user)
    enrollment = _enrollment(db, course.id, student_id)
    if enrollment is None:
        raise AppError(404, "ENROLLMENT_NOT_FOUND")
    if enrollment.status != status:
        enrollment.status = status
        enrollment.decided_at = func.now()
        db.commit()
        db.refresh(enrollment)
    return enrollment


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


def pending_request_count(db: Session, course_id: int) -> int:
    """For other modules: number of enrollment requests waiting for the author."""
    query = select(func.count()).where(
        Enrollment.course_id == course_id, Enrollment.status == EnrollmentStatus.PENDING
    )
    return db.scalar(query) or 0
