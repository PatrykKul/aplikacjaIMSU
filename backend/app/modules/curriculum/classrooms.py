"""Classrooms: a teacher's students and the courses assigned to them."""

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.curriculum.models import Classroom, ClassroomCourse, ClassroomStudent, Course
from app.modules.curriculum.schemas import (
    ClassroomResponse,
    ClassroomSummaryResponse,
    ClassroomTeacherResponse,
    CourseSummaryResponse,
)
from app.modules.curriculum.service import get_owned_course
from app.modules.identity import service as identity_service
from app.modules.identity.models import User
from app.modules.identity.schemas import StudentResponse


def get_owned_classroom(db: Session, classroom_id: int, user: User) -> Classroom:
    classroom = db.get(Classroom, classroom_id)
    if classroom is None or classroom.teacher_id != user.id:
        raise AppError(404, "CLASSROOM_NOT_FOUND")
    return classroom


def _counts(
    db: Session, link: type[ClassroomStudent | ClassroomCourse], ids: list[int]
) -> dict[int, int]:
    rows = db.execute(
        select(link.classroom_id, func.count())
        .where(link.classroom_id.in_(ids))
        .group_by(link.classroom_id)
    )
    return {classroom_id: count for classroom_id, count in rows}


def list_teacher_classrooms(db: Session, teacher: User) -> list[ClassroomSummaryResponse]:
    query = select(Classroom).where(Classroom.teacher_id == teacher.id)
    classrooms = list(db.scalars(query.order_by(Classroom.name, Classroom.id)))
    ids = [classroom.id for classroom in classrooms]
    student_counts = _counts(db, ClassroomStudent, ids)
    course_counts = _counts(db, ClassroomCourse, ids)
    return [
        ClassroomSummaryResponse(
            id=classroom.id,
            name=classroom.name,
            teacher=ClassroomTeacherResponse.model_validate(teacher),
            course_count=course_counts.get(classroom.id, 0),
            student_count=student_counts.get(classroom.id, 0),
        )
        for classroom in classrooms
    ]


def _assigned_courses(db: Session, classroom_id: int) -> list[Course]:
    query = (
        select(Course)
        .join(ClassroomCourse, ClassroomCourse.course_id == Course.id)
        .where(ClassroomCourse.classroom_id == classroom_id)
        .order_by(Course.title, Course.id)
    )
    return list(db.scalars(query))


def teacher_classroom_detail(db: Session, classroom: Classroom, teacher: User) -> ClassroomResponse:
    """The classroom as its teacher sees it: all assigned courses (archived too) and students."""
    student_ids = db.scalars(
        select(ClassroomStudent.student_id).where(ClassroomStudent.classroom_id == classroom.id)
    ).all()
    return ClassroomResponse(
        id=classroom.id,
        name=classroom.name,
        teacher=ClassroomTeacherResponse.model_validate(teacher),
        courses=[
            CourseSummaryResponse.model_validate(c) for c in _assigned_courses(db, classroom.id)
        ],
        students=[
            StudentResponse.model_validate(student)
            for student in identity_service.get_users(db, student_ids)
        ],
    )


def create_classroom(db: Session, teacher: User, name: str) -> Classroom:
    classroom = Classroom(teacher_id=teacher.id, name=name)
    db.add(classroom)
    db.commit()
    db.refresh(classroom)
    return classroom


def rename_classroom(db: Session, classroom_id: int, teacher: User, name: str) -> Classroom:
    classroom = get_owned_classroom(db, classroom_id, teacher)
    classroom.name = name
    db.commit()
    db.refresh(classroom)
    return classroom


def delete_classroom(db: Session, classroom_id: int, teacher: User) -> None:
    """Delete the classroom; the database removes its student and course links (CASCADE)."""
    classroom = get_owned_classroom(db, classroom_id, teacher)
    db.delete(classroom)
    db.commit()


# --- Students and courses of a classroom ---------------------------------------------------------


def add_student(db: Session, classroom_id: int, teacher: User, student_id: int) -> None:
    """Add an active student; adding a member again changes nothing."""
    classroom = get_owned_classroom(db, classroom_id, teacher)
    if identity_service.get_active_student(db, student_id) is None:
        raise AppError(404, "STUDENT_NOT_FOUND")
    db.execute(
        insert(ClassroomStudent)
        .values(classroom_id=classroom.id, student_id=student_id)
        .on_conflict_do_nothing()
    )
    db.commit()


def remove_student(db: Session, classroom_id: int, teacher: User, student_id: int) -> None:
    """Remove a student; removing a non-member changes nothing."""
    classroom = get_owned_classroom(db, classroom_id, teacher)
    db.execute(
        delete(ClassroomStudent).where(
            ClassroomStudent.classroom_id == classroom.id,
            ClassroomStudent.student_id == student_id,
        )
    )
    db.commit()


def assign_course(db: Session, classroom_id: int, teacher: User, course_id: int) -> None:
    """Assign one of the teacher's active courses; assigning it again changes nothing."""
    classroom = get_owned_classroom(db, classroom_id, teacher)
    course = get_owned_course(db, course_id, teacher)
    db.execute(
        insert(ClassroomCourse)
        .values(classroom_id=classroom.id, course_id=course.id)
        .on_conflict_do_nothing()
    )
    db.commit()


def unassign_course(db: Session, classroom_id: int, teacher: User, course_id: int) -> None:
    """Unassign a course (archived too); a course that is not assigned changes nothing."""
    classroom = get_owned_classroom(db, classroom_id, teacher)
    db.execute(
        delete(ClassroomCourse).where(
            ClassroomCourse.classroom_id == classroom.id,
            ClassroomCourse.course_id == course_id,
        )
    )
    db.commit()
