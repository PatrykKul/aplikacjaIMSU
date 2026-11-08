from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from app.modules.identity.models import User
from tests.learning_style.conftest import choices


def test_migration_has_twenty_questions_with_v_a_k_answers(answer_key):
    assert len(answer_key) == 20
    assert all(set(by_style) == {"V", "A", "K"} for by_style in answer_key.values())


def test_questions_do_not_reveal_answer_styles(client: TestClient, login, student: User):
    login(student)
    questions = client.get("/survey/questions").json()
    assert len(questions) == 20
    assert all(len(q["answers"]) == 3 for q in questions)
    assert all(set(a) == {"id", "text"} for q in questions for a in q["answers"])


def test_questions_need_login(client: TestClient):
    assert client.get("/survey/questions").status_code == 401


def test_submit_creates_profile_and_result(fill_survey: Callable[..., dict[str, Any]], student):
    profile = fill_survey(student, "VVA")
    assert profile["survey_completed"] is True
    assert profile["style"] == "V"
    assert profile["style_source"] == "survey"
    points = profile["last_result"]["points"]
    assert points == {"V": 14, "A": 6, "K": 0}
    assert profile["weights"] == points
    assert "V 14 / A 6 / K 0" in profile["explanation"]
    assert profile["proposal"] is None


def test_tie_gives_mixed_style(fill_survey, student):
    assert fill_survey(student, "VA")["style"] == "VA"


def test_missing_answer(client: TestClient, login, student, answer_key):
    login(student)
    answers = choices(answer_key, "V")[:-1]
    response = client.post("/survey/answers", json={"answers": answers})
    assert response.status_code == 400
    assert response.json() == {"code": "SURVEY_INCOMPLETE"}


def test_duplicate_answer(client: TestClient, login, student, answer_key):
    login(student)
    answers = choices(answer_key, "V")
    response = client.post("/survey/answers", json={"answers": [*answers, answers[0]]})
    assert response.json() == {"code": "SURVEY_DUPLICATE_ANSWER"}


def test_answer_from_another_question(client: TestClient, login, student, answer_key):
    login(student)
    answers = choices(answer_key, "V")
    answers[0]["answer_id"] = answers[1]["answer_id"]
    response = client.post("/survey/answers", json={"answers": answers})
    assert response.status_code == 400
    assert response.json() == {"code": "SURVEY_ANSWER_MISMATCH"}


def test_teacher_cannot_fill_in_the_survey(client: TestClient, login, teacher, answer_key):
    login(teacher)
    response = client.post("/survey/answers", json={"answers": choices(answer_key, "V")})
    assert response.status_code == 403


def test_new_survey_replaces_style_and_keeps_history(client: TestClient, fill_survey, student):
    fill_survey(student, "V")
    client.put("/profile/learning-style", json={"style": "A"})
    profile = fill_survey(student, "K")
    assert profile["style"] == "K"
    assert profile["style_source"] == "survey"
    history = client.get("/survey/results").json()
    assert [r["dominant_style"] for r in history] == ["K", "V"]
