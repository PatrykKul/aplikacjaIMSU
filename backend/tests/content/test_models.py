import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.content.models import Lesson
from app.modules.content.steps import LessonSteps
from app.modules.curriculum.models import Skill
from tests.content.builders import TEXT_STEP, number_question


def make_lesson(skill: Skill) -> Lesson:
    steps = LessonSteps.model_validate({"steps": [TEXT_STEP, number_question()]})
    return Lesson(skill_id=skill.id, title="Ile oszczędzasz?", steps=steps.to_json())


def test_lesson_round_trip(db: Session, skill: Skill):
    lesson = make_lesson(skill)
    db.add(lesson)
    db.flush()
    db.expire(lesson)  # force reading the row back from the database

    assert lesson.is_archived is False
    stored = LessonSteps.model_validate({"steps": lesson.steps})
    assert stored.find("q-saving") is not None
    assert stored.to_json() == make_lesson(skill).steps


def test_one_lesson_per_skill(db: Session, skill: Skill):
    db.add_all([make_lesson(skill), make_lesson(skill)])
    with pytest.raises(IntegrityError):
        db.flush()
