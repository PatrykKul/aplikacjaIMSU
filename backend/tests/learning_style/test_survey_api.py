"""Survey (once), profile from the survey (R1) and the choice after a tie."""

from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from app.modules.identity.models import User
from tests.learning_style.conftest import choices, journal_types, last_event, survey_styles

FillSurvey = Callable[..., dict[str, Any]]


def test_migration_has_twenty_questions_with_v_a_k_answers(answer_key):
    assert len(answer_key) == 20
    assert all(set(by_style) == {"V", "A", "K"} for by_style in answer_key.values())


def test_questions_do_not_reveal_answer_styles(client: TestClient, login, student: User):
    login(student)
    questions = client.get("/survey/questions").json()
    assert len(questions) == 20
    assert all(set(a) == {"id", "text"} for q in questions for a in q["answers"])


def test_questions_need_login(client: TestClient):
    assert client.get("/survey/questions").status_code == 401


def test_survey_gives_percentages_and_style(client: TestClient, fill_survey: FillSurvey, student):
    profile = fill_survey(student, survey_styles(9, 8, 3))
    assert profile["survey_completed"] is True
    assert (profile["style"], profile["style_source"]) == ("V", "survey")
    assert profile["tie_styles"] == []
    assert profile["percentages"] == {"V": 45, "A": 40, "K": 15}
    assert profile["survey"]["points"] == {"V": 9, "A": 8, "K": 3}
    assert profile["survey"]["percentages"] == {"V": 45, "A": 40, "K": 15}
    assert profile["forms"]["V"] == {"confirmed": False, "lessons": 0, "average": None}
    assert profile["open_proposal"] is None and profile["trial"] is None
    # the history has its first point, the journal its first event
    history = client.get("/me/progress").json()["history"]
    assert [point["percentages"] for point in history] == [{"V": 45, "A": 40, "K": 15}]
    event = last_event(client, "survey_completed")
    assert event["data"] == {
        "points": {"V": 9, "A": 8, "K": 3},
        "percentages": {"V": 45, "A": 40, "K": 15},
        "style": "V",
        "tie_styles": [],
    }
    assert event["course"] is None and event["lesson"] is None


def test_survey_with_minimum_percentages(fill_survey: FillSurvey, student):
    profile = fill_survey(student, "V")
    assert profile["percentages"] == {"V": 90, "A": 5, "K": 5}


def test_survey_only_once(client: TestClient, fill_survey: FillSurvey, student, answer_key):
    fill_survey(student, "V")
    response = client.post("/survey/answers", json={"answers": choices(answer_key, "K")})
    assert (response.status_code, response.json()) == (409, {"code": "SURVEY_ALREADY_DONE"})
    assert client.get("/profile/learning-style").json()["style"] == "V"


def test_tie_leaves_the_style_open(client: TestClient, fill_survey: FillSurvey, student, course):
    profile = fill_survey(student, survey_styles(8, 8, 4))
    assert profile["style"] is None
    assert profile["tie_styles"] == ["V", "A"]
    assert profile["percentages"] == {"V": 40, "A": 40, "K": 20}
    assert last_event(client, "survey_completed")["data"]["tie_styles"] == ["V", "A"]
    # without a style the student cannot study yet
    lesson_id = course["lessons"][0]["id"]
    assert client.get(f"/lessons/{lesson_id}/study").json() == {"code": "SURVEY_REQUIRED"}
    assert client.put("/profile/learning-style", json={"style": "K"}).status_code == 403


def test_tie_choice(client: TestClient, fill_survey: FillSurvey, student):
    fill_survey(student, survey_styles(8, 8, 4))
    response = client.post("/profile/learning-style/tie-choice", json={"style": "K"})
    assert (response.status_code, response.json()) == (400, {"code": "STYLE_NOT_TIED"})
    profile = client.post("/profile/learning-style/tie-choice", json={"style": "A"}).json()
    assert (profile["style"], profile["style_source"]) == ("A", "tie_choice")
    assert profile["tie_styles"] == []
    assert profile["percentages"] == {"V": 40, "A": 40, "K": 20}
    assert last_event(client, "tie_resolved")["data"] == {"style": "A", "tie_styles": ["V", "A"]}
    assert len(client.get("/me/progress").json()["history"]) == 2
    again = client.post("/profile/learning-style/tie-choice", json={"style": "V"})
    assert (again.status_code, again.json()) == (409, {"code": "NO_TIE"})


def test_tie_choice_without_survey_or_tie(client: TestClient, login, student, fill_survey):
    login(student)
    response = client.post("/profile/learning-style/tie-choice", json={"style": "V"})
    assert response.json() == {"code": "SURVEY_REQUIRED"}
    fill_survey(student, "V")
    response = client.post("/profile/learning-style/tie-choice", json={"style": "V"})
    assert response.json() == {"code": "NO_TIE"}


def test_survey_validation(client: TestClient, login, student, answer_key):
    login(student)
    answers = choices(answer_key, "V")
    for payload, code in (
        (answers[:-1], "SURVEY_INCOMPLETE"),
        ([*answers, answers[0]], "SURVEY_DUPLICATE_ANSWER"),
        (
            [answers[0] | {"answer_id": answers[1]["answer_id"]}, *answers[1:]],
            "SURVEY_ANSWER_MISMATCH",
        ),
    ):
        response = client.post("/survey/answers", json={"answers": payload})
        assert (response.status_code, response.json()) == (400, {"code": code})
    assert client.get("/profile/learning-style").json()["survey_completed"] is False


def test_other_roles(client: TestClient, login, teacher, admin, answer_key):
    for user in (teacher, admin):
        login(user)
        response = client.post("/survey/answers", json={"answers": choices(answer_key, "V")})
        assert response.status_code == 403
        profile = client.get("/profile/learning-style").json()
        assert profile["survey_completed"] is False
        assert profile["style"] is None and profile["percentages"] is None
        assert client.put("/profile/learning-style", json={"style": "V"}).status_code == 403


def test_journal_has_only_the_students_own_events(client: TestClient, fill_survey, make_user):
    fill_survey(make_user(), "V")
    fill_survey(make_user(), "K")
    assert journal_types(client) == ["survey_completed"]
