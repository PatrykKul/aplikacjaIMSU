from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.content.importer import import_package
from app.modules.content.models import Lesson
from app.modules.content.package import load_package
from app.modules.curriculum.models import Course, Skill
from app.modules.identity.models import User, UserRole
from tests.content.builders import (
    TEXT_STEP,
    choice_question,
    lesson,
    number_question,
    write_package,
)

# Fields that must never be sent with a lesson
SECRET_KEYS = {"value", "correct", "feedback", "explanation", "check", "when"}


class Imported:
    def __init__(self, db: Session, course_id: int) -> None:
        self.db = db
        self.course = db.get(Course, course_id)
        self.skills = {
            s.key: s for s in db.scalars(select(Skill).where(Skill.course_id == course_id))
        }

    def lesson(self, skill: str) -> Lesson:
        return self.db.scalars(select(Lesson).where(Lesson.skill_id == self.skills[skill].id)).one()


@pytest.fixture
def course(db: Session, tmp_path: Path) -> Imported:
    lessons = [
        lesson("base", steps=[TEXT_STEP, number_question(), choice_question()]),
        lesson("advanced"),
    ]
    report = import_package(db, load_package(write_package(tmp_path, lessons=lessons)))
    imported = Imported(db, report.course_id)
    imported.course.is_published = True
    db.commit()
    return imported


@pytest.fixture
def student(make_user: Callable[..., User], login: Callable[[User], None]) -> User:
    user = make_user(UserRole.STUDENT)
    login(user)
    return user


def keys_in(data: Any) -> set[str]:
    if isinstance(data, dict):
        return set(data) | {key for value in data.values() for key in keys_in(value)}
    if isinstance(data, list):
        return {key for item in data for key in keys_in(item)}
    return set()


def check(client: TestClient, item: Lesson, step: str, **body: Any):
    return client.post(f"/lessons/{item.id}/steps/{step}/check", json=body)


def skill_lesson(client: TestClient, course: Imported, skill: str = "base"):
    return client.get(f"/skills/{course.skills[skill].id}/lesson")


def test_anonymous_gets_401(client: TestClient, course: Imported):
    assert skill_lesson(client, course).status_code == 401


def test_lesson_of_skill_has_no_answer_keys(client: TestClient, course: Imported, student: User):
    response = skill_lesson(client, course)

    assert response.status_code == 200
    data = response.json()
    assert (data["id"], data["skill_id"]) == (course.lesson("base").id, course.skills["base"].id)
    assert [step["type"] for step in data["steps"]] == ["text", "question", "question"]
    number, choice = data["steps"][1]["answer"], data["steps"][2]["answer"]
    assert number == {"type": "number", "unit": "zł"}
    assert choice["type"] == "choice"
    assert len(choice["options"]) == 3
    assert data["steps"][1]["hint"] == "25% to jedna czwarta."
    assert keys_in(data) & SECRET_KEYS == set()


def test_archived_lesson_is_hidden(
    client: TestClient, course: Imported, student: User, db: Session
):
    base = course.lesson("base")
    base.is_archived = True
    db.flush()

    response = skill_lesson(client, course)
    assert (response.status_code, response.json()) == (404, {"code": "LESSON_NOT_FOUND"})
    response = check(client, base, "q-saving", answer="30")
    assert (response.status_code, response.json()) == (404, {"code": "LESSON_NOT_FOUND"})


def test_lessons_of_draft_course_are_hidden(
    client: TestClient, course: Imported, student: User, db: Session
):
    course.course.is_published = False
    db.flush()

    response = skill_lesson(client, course)
    assert (response.status_code, response.json()) == (404, {"code": "SKILL_NOT_FOUND"})
    assert check(client, course.lesson("base"), "q-saving", answer="30").status_code == 404


def test_check_correct_answer(client: TestClient, course: Imported, student: User):
    response = check(client, course.lesson("base"), "q-saving", answer="30 zł")

    assert response.status_code == 200
    assert response.json() == {
        "correct": True,
        "feedback": None,
        "explanation": "25% ze 120 zł to 30 zł.",
        "correct_answer": "30 zł",
    }


def test_check_typical_mistake(client: TestClient, course: Imported, student: User):
    data = check(client, course.lesson("base"), "q-saving", answer="90").json()
    assert data == {
        "correct": False,
        "feedback": "To cena po rabacie.",
        "explanation": None,
        "correct_answer": None,
    }


def test_reveal_after_wrong_answer(client: TestClient, course: Imported, student: User):
    data = check(client, course.lesson("base"), "q-saving", answer="31", reveal=True).json()
    assert (data["correct"], data["correct_answer"]) == (False, "30 zł")


def test_check_choice(client: TestClient, course: Imported, student: User):
    base = course.lesson("base")
    assert check(client, base, "q-rule", answer=0).json()["correct"] is True
    assert check(client, base, "q-rule", answer=1).json()["feedback"] == "Sprawdź na bluzie."


@pytest.mark.parametrize(
    ("step", "answer", "status", "code"),
    [
        ("hook", "30", 400, "STEP_NOT_A_QUESTION"),
        ("missing", "30", 404, "STEP_NOT_FOUND"),
        ("q-saving", "abc", 400, "ANSWER_NOT_A_NUMBER"),
        ("q-rule", 7, 400, "INVALID_CHOICE"),
        ("q-rule", "0", 400, "INVALID_CHOICE"),
    ],
)
def test_check_errors(
    client: TestClient,
    course: Imported,
    student: User,
    step: str,
    answer: Any,
    status: int,
    code: str,
):
    response = check(client, course.lesson("base"), step, answer=answer)
    assert (response.status_code, response.json()) == (status, {"code": code})


def test_check_rejects_boolean_answer(client: TestClient, course: Imported, student: User):
    response = check(client, course.lesson("base"), "q-rule", answer=True)
    assert response.status_code == 422


def test_check_unknown_lesson(client: TestClient, course: Imported, student: User):
    response = client.post("/lessons/999999/steps/q/check", json={"answer": "1"})
    assert (response.status_code, response.json()) == (404, {"code": "LESSON_NOT_FOUND"})
