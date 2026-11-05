import pytest
from sqlalchemy.orm import Session

from app.modules.curriculum.models import Course, Skill, Unit


@pytest.fixture
def skill(db: Session) -> Skill:
    course = Course(key="test-course", title="Kurs")
    unit = Unit(key="basics", title="Podstawy", course=course)
    db.add(course)
    db.flush()
    skill = Skill(
        course_id=course.id,
        unit_id=unit.id,
        key="percent-of-number",
        title="Procent danej liczby",
    )
    db.add(skill)
    db.flush()
    return skill
