"""Studying a lesson: version in the lesson form, explicit form choice, suggestion."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.content.models import LessonContent
from app.modules.learning_style.models import LessonForm
from tests.learning_style.conftest import journal_types, last_event, set_form, take_quiz


def text_block(text: str) -> dict[str, Any]:
    paragraph = {"type": "paragraph", "content": [{"type": "text", "text": text}]}
    return {"id": "t1", "type": "text", "doc": {"type": "doc", "content": [paragraph]}}


@pytest.fixture
def versions(db: Session, course) -> int:
    """Three versions of the first lesson (stored directly; content has its own tests)."""
    lesson_id = course["lessons"][0]["id"]
    for form in ("V", "A", "K"):
        db.add(LessonContent(lesson_id=lesson_id, form=form, blocks=[text_block(f"Wersja {form}")]))
    db.commit()
    return lesson_id


def block_text(study: dict[str, Any]) -> str:
    return study["blocks"][0]["doc"]["content"][0]["content"][0]["text"]


def test_student_gets_the_version_of_the_active_style(
    client: TestClient, course, versions, learner
):
    learner(course["id"], "A")
    study = client.get(f"/lessons/{versions}/study").json()
    assert study["lesson_id"] == versions
    assert (study["form"], study["form_source"], study["style"]) == ("A", "style", "A")
    assert block_text(study) == "Wersja A"
    assert study["other_forms"] == ["V", "K"]
    assert study["suggestion"] is None and study["last_result"] is None


def test_choosing_another_form(client: TestClient, db: Session, course, versions, learner):
    student = learner(course["id"], "V")
    study = set_form(client, versions, "K", "manual")
    assert (study["form"], study["form_source"], study["style"]) == ("K", "choice", "V")
    assert block_text(study) == "Wersja K"
    assert study["other_forms"] == ["V", "A"]
    event = last_event(client, "lesson_form_changed")
    assert event["data"] == {"from": "V", "to": "K", "source": "manual"}
    assert event["lesson"]["id"] == versions and event["course"]["id"] == course["id"]
    # the same form again changes nothing
    set_form(client, versions, "K", "manual")
    assert journal_types(client).count("lesson_form_changed") == 1
    # back to the style form: not an explicit choice (D57), the choice row goes away
    back = set_form(client, versions, "V", "manual")
    assert (back["form"], back["form_source"]) == ("V", "style")
    assert db.get(LessonForm, (student.id, versions)) is None
    assert last_event(client, "lesson_form_changed")["data"] == {
        "from": "K",
        "to": "V",
        "source": "manual",
    }
    assert client.get(f"/lessons/{versions}/quiz").json()["form"] == "V"
    # choosing the style again changes nothing
    set_form(client, versions, "V", "manual")
    assert journal_types(client).count("lesson_form_changed") == 2


def test_choice_equal_to_a_new_style_reads_as_style(
    client: TestClient, db: Session, course, versions, learner
):
    # Marta's path in the demo: lesson 1 redone (and passed) in V, then the style becomes V;
    # the choice stays in the passed lesson, but it is the style now
    student = learner(course["id"], "K")
    take_quiz(client, versions, 40)
    set_form(client, versions, "V")
    take_quiz(client, versions, 80)
    assert client.put("/profile/learning-style", json={"style": "V"}).status_code == 200
    assert db.get(LessonForm, (student.id, versions)) is not None  # passed: kept as history

    study = client.get(f"/lessons/{versions}/study").json()

    assert (study["form"], study["form_source"], study["style"]) == ("V", "style", "V")
    # after the next change of style the passed lesson shows the chosen form again
    client.put("/profile/learning-style", json={"style": "A"})
    study = client.get(f"/lessons/{versions}/study").json()
    assert (study["form"], study["form_source"]) == ("V", "choice")


def test_missing_version_gives_no_blocks(client: TestClient, course, learner):
    learner(course["id"], "V")
    assert client.get(f"/lessons/{course['lessons'][0]['id']}/study").json()["blocks"] == []


def test_suggestion_shown_until_the_student_switches(client: TestClient, course, learner):
    learner(course["id"], "V")
    lesson_id = course["lessons"][0]["id"]
    take_quiz(client, lesson_id, 20)
    study = client.get(f"/lessons/{lesson_id}/study").json()
    assert study["last_result"] == {"percent": 20, "passed": False, "form": "V"}
    suggested = study["suggestion"]["suggested"]["form"]
    assert study["suggestion"]["failed"]["form"] == "V"
    assert set_form(client, lesson_id, suggested)["suggestion"] is None
    take_quiz(client, lesson_id, 100)
    study = client.get(f"/lessons/{lesson_id}/study").json()
    assert study["suggestion"] is None
    assert study["last_result"] == {"percent": 100, "passed": True, "form": suggested}


def test_study_access(client: TestClient, course, make_user, login, enroll, fill_survey, teacher):
    first, second = (lesson["id"] for lesson in course["lessons"][:2])
    login(teacher)
    assert client.get(f"/lessons/{first}/study").json() == {"code": "FORBIDDEN"}
    put = client.put(f"/lessons/{first}/study/form", json={"form": "A"})
    assert put.json() == {"code": "FORBIDDEN"}
    student = make_user()
    login(student)
    assert client.get(f"/lessons/{first}/study").json() == {"code": "SURVEY_REQUIRED"}
    fill_survey(student, "V")
    assert client.get(f"/lessons/{first}/study").json() == {"code": "ENROLLMENT_REQUIRED"}
    put = client.put(f"/lessons/{first}/study/form", json={"form": "A"})
    assert put.json() == {"code": "ENROLLMENT_REQUIRED"}
    enroll(student, course["id"])
    assert client.get(f"/lessons/{second}/study").json()["code"] == "LESSON_LOCKED"
    assert client.get("/lessons/999999/study").status_code == 404
    assert client.put(f"/lessons/{first}/study/form", json={"form": "X"}).status_code == 422
    assert client.get(f"/lessons/{first}/study").status_code == 200
