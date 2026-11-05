import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.curriculum.models import Course, Skill, Unit


def make_course(db: Session, key: str = "test-course") -> Course:
    course = Course(key=key, title="Kurs")
    Unit(key="basics", title="Podstawy", course=course)
    db.add(course)
    db.flush()
    return course


def make_skill(db: Session, course: Course, key: str) -> Skill:
    skill = Skill(course_id=course.id, unit_id=course.units[0].id, key=key, title=key)
    db.add(skill)
    db.flush()
    return skill


def test_course_defaults(db: Session):
    course = make_course(db)
    db.refresh(course)
    assert course.is_published is False
    assert course.is_archived is False
    assert course.description == ""
    assert course.position == 0


def test_skill_key_is_unique_within_course(db: Session):
    course = make_course(db)
    make_skill(db, course, "percent-of-number")
    with pytest.raises(IntegrityError):
        make_skill(db, course, "percent-of-number")


def test_same_skill_key_allowed_in_different_courses(db: Session):
    first, second = make_course(db, "first"), make_course(db, "second")
    make_skill(db, first, "basics-skill")
    make_skill(db, second, "basics-skill")
