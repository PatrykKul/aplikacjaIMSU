"""Question pool (teacher) and drawn quiz attempts (student)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.modules.curriculum.models import Lesson
from app.modules.identity.models import User
from tests.assessment.conftest import question
from tests.learning_style.conftest import pool, take_quiz

Login = Callable[[User], None]


def _edit_url(lesson_id: int) -> str:
    return f"/lessons/{lesson_id}/quiz/edit"


# --- Teacher: pool editor ------------------------------------------------------------------------


@pytest.fixture
def draft_lesson(make_course, teacher: User) -> int:
    """An unpublished lesson of the `teacher` (logged in)."""
    return make_course(teacher, lessons=("Szkic",))["lessons"][0]["id"]


def test_author_saves_and_reads_the_pool_with_explanations(client: TestClient, draft_lesson):
    response = client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": pool(6)})
    assert response.status_code == 200
    questions = client.get(_edit_url(draft_lesson)).json()["questions"]
    assert len(questions) == 6
    assert questions[0]["correct_answer_id"] == "a"
    assert questions[0]["explanation"] == "Wyjaśnienie 1"


def test_lesson_without_pool_has_empty_editor(client: TestClient, draft_lesson):
    assert client.get(_edit_url(draft_lesson)).json() == {"questions": []}


def test_admin_reads_the_pool(client: TestClient, draft_lesson, login: Login, admin: User):
    client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": pool(5)})
    login(admin)
    assert len(client.get(_edit_url(draft_lesson)).json()["questions"]) == 5
    assert (
        client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": pool(5)}).status_code == 403
    )


def test_only_the_author_edits(
    client: TestClient, draft_lesson, login: Login, other_teacher: User, student: User
):
    login(other_teacher)
    assert client.get(_edit_url(draft_lesson)).status_code == 404
    assert (
        client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": pool(5)}).status_code == 404
    )
    assert client.delete(f"/lessons/{draft_lesson}/quiz").status_code == 404
    login(student)
    assert client.get(_edit_url(draft_lesson)).status_code == 403
    assert (
        client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": pool(5)}).status_code == 403
    )


def test_pool_validation(client: TestClient, draft_lesson):
    no_explanation = {k: v for k, v in question("q1").items() if k != "explanation"}
    empty_explanation = question("q2") | {"explanation": " "}
    long_explanation = question("q3") | {"explanation": "x" * 1001}
    bad_correct = question("q4", correct="zzz")
    two_answers = question("q5") | {"answers": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]}
    too_many = [question(f"q{i}") for i in range(51)]
    for questions in (
        [],
        [no_explanation],
        [empty_explanation],
        [long_explanation],
        [bad_correct],
        [two_answers],
        [question("q"), question("q")],
        too_many,
    ):
        response = client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": questions})
        assert response.status_code == 422, questions
    fifty = [question(f"q{i}") for i in range(50)]
    assert client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": fifty}).status_code == 200


def test_draft_lesson_pool_can_be_small_and_deleted(client: TestClient, draft_lesson):
    assert (
        client.put(f"/lessons/{draft_lesson}/quiz", json={"questions": pool(2)}).status_code == 200
    )
    assert client.delete(f"/lessons/{draft_lesson}/quiz").status_code == 204
    assert client.get(_edit_url(draft_lesson)).json() == {"questions": []}


def test_published_lesson_keeps_a_full_pool(client: TestClient, quiz_course):
    lesson_id = quiz_course(lessons=("L1",))["lessons"][0]["id"]
    response = client.put(f"/lessons/{lesson_id}/quiz", json={"questions": pool(4)})
    assert response.status_code == 409
    assert response.json() == {
        "code": "PUBLISHED_LESSON_INCOMPLETE",
        "issues": [{"area": "quiz", "code": "QUIZ_TOO_FEW_QUESTIONS", "count": 4, "min": 5}],
    }
    assert client.put(f"/lessons/{lesson_id}/quiz", json={"questions": pool(5)}).status_code == 200
    response = client.delete(f"/lessons/{lesson_id}/quiz")
    assert response.status_code == 409
    assert response.json()["code"] == "PUBLISHED_LESSON_INCOMPLETE"
    assert len(client.get(_edit_url(lesson_id)).json()["questions"]) == 5


# --- Student: drawing ----------------------------------------------------------------------------


@pytest.fixture
def course(quiz_course) -> dict[str, Any]:
    return quiz_course()


def test_student_gets_five_questions_without_the_key(client: TestClient, course, learner):
    learner(course["id"], "V")
    quiz = client.get(f"/lessons/{course['lessons'][0]['id']}/quiz").json()
    assert quiz["pool_size"] == 8
    assert quiz["form"] == "V"
    assert len(quiz["questions"]) == 5
    for item in quiz["questions"]:
        assert set(item) == {"id", "text", "answers"}
        assert all(set(answer) == {"id", "text"} for answer in item["answers"])


def test_refresh_returns_the_same_open_draw(client: TestClient, course, learner):
    learner(course["id"])
    url = f"/lessons/{course['lessons'][0]['id']}/quiz"
    first, second = client.get(url).json(), client.get(url).json()
    assert first == second


def test_retry_draws_questions_outside_the_last_set(client: TestClient, course, learner):
    learner(course["id"])
    lesson_id = course["lessons"][0]["id"]
    first = take_quiz(client, lesson_id, 40)
    second = client.get(f"/lessons/{lesson_id}/quiz").json()
    assert second["draw_id"] != first["draw_id"]
    shown_first = {item["question_id"] for item in first["results"]}
    shown_second = {item["id"] for item in second["questions"]}
    # pool of 8: all 3 questions not shown before + 2 from the previous set
    assert shown_second - shown_first == {f"q{i}" for i in range(1, 9)} - shown_first
    assert len(shown_second & shown_first) == 2


def test_quiz_needs_survey_enrollment_and_unlocked_lesson(
    client: TestClient, course, make_user, login: Login, enroll, fill_survey
):
    first, second = (lesson["id"] for lesson in course["lessons"][:2])
    student = make_user()
    login(student)
    assert client.get(f"/lessons/{first}/quiz").json() == {"code": "SURVEY_REQUIRED"}
    fill_survey(student, "V")
    response = client.get(f"/lessons/{first}/quiz")
    assert (response.status_code, response.json()) == (403, {"code": "ENROLLMENT_REQUIRED"})
    enroll(student, course["id"])
    response = client.get(f"/lessons/{second}/quiz")
    assert response.status_code == 403
    assert response.json() == {
        "code": "LESSON_LOCKED",
        "required_lesson": {"id": first, "title": "Lekcja 1", "number": 1},
    }
    post = client.post(f"/lessons/{second}/quiz/attempts", json={"draw_id": 1, "answers": {}})
    assert post.json()["code"] == "LESSON_LOCKED"
    assert client.get(f"/lessons/{first}/quiz").status_code == 200


def test_other_roles_cannot_solve(client: TestClient, course, login: Login, teacher, admin):
    lesson_id = course["lessons"][0]["id"]
    for user in (teacher, admin):
        login(user)
        assert client.get(f"/lessons/{lesson_id}/quiz").json() == {"code": "FORBIDDEN"}
        response = client.post(
            f"/lessons/{lesson_id}/quiz/attempts", json={"draw_id": 1, "answers": {}}
        )
        assert response.json() == {"code": "FORBIDDEN"}


def test_lesson_without_pool(client: TestClient, make_course, teacher: User, learner, db: Session):
    course = make_course(teacher, lessons=("Bez quizu",), published=True)
    learner(course["id"])
    response = client.get(f"/lessons/{course['lessons'][0]['id']}/quiz")
    assert (response.status_code, response.json()) == (404, {"code": "QUIZ_NOT_FOUND"})


def test_unpublished_lesson_is_not_found_for_a_student(
    client: TestClient, course, learner, db: Session
):
    lesson_id = course["lessons"][0]["id"]
    db.execute(update(Lesson).where(Lesson.id == lesson_id).values(is_published=False))
    db.commit()
    learner(course["id"])
    assert client.get(f"/lessons/{lesson_id}/quiz").status_code == 404


# --- Student: submitting -------------------------------------------------------------------------


def _answers(quiz: dict[str, Any], answer: str = "a") -> dict[str, str]:
    return {item["id"]: answer for item in quiz["questions"]}


def test_attempt_result_with_explanations(client: TestClient, course, learner):
    learner(course["id"])
    lesson_id = course["lessons"][0]["id"]
    quiz = client.get(f"/lessons/{lesson_id}/quiz").json()
    answers = _answers(quiz)
    answers[quiz["questions"][0]["id"]] = "c"
    response = client.post(
        f"/lessons/{lesson_id}/quiz/attempts", json={"draw_id": quiz["draw_id"], "answers": answers}
    )
    assert response.status_code == 200
    body = response.json()
    assert (body["percent"], body["correct_count"], body["total"], body["passed"]) == (
        80,
        4,
        5,
        True,
    )
    first = body["results"][0]
    assert first["question_id"] == quiz["questions"][0]["id"]
    assert (first["chosen_answer_id"], first["correct_answer_id"], first["correct"]) == (
        "c",
        "a",
        False,
    )
    assert first["explanation"].startswith("Wyjaśnienie")
    assert first["text"].startswith("Pytanie")
    assert len(first["answers"]) == 3
    assert body["feedback"]["unlocked_lesson"] == {
        "id": course["lessons"][1]["id"],
        "title": "Lekcja 2",
        "number": 2,
    }


def test_draw_can_be_submitted_once(client: TestClient, course, learner):
    learner(course["id"])
    lesson_id = course["lessons"][0]["id"]
    quiz = client.get(f"/lessons/{lesson_id}/quiz").json()
    payload = {"draw_id": quiz["draw_id"], "answers": _answers(quiz)}
    assert client.post(f"/lessons/{lesson_id}/quiz/attempts", json=payload).status_code == 200
    again = client.post(f"/lessons/{lesson_id}/quiz/attempts", json=payload)
    assert (again.status_code, again.json()) == (409, {"code": "DRAW_NOT_OPEN"})


def test_draw_of_another_student_or_lesson_is_not_open(client: TestClient, course, learner):
    learner(course["id"])
    lesson_id = course["lessons"][0]["id"]
    quiz = client.get(f"/lessons/{lesson_id}/quiz").json()
    payload = {"draw_id": quiz["draw_id"], "answers": _answers(quiz)}
    learner(course["id"])  # another student logs in
    assert client.post(f"/lessons/{lesson_id}/quiz/attempts", json=payload).json() == {
        "code": "DRAW_NOT_OPEN"
    }
    missing = {"draw_id": 999999, "answers": {}}
    assert client.post(f"/lessons/{lesson_id}/quiz/attempts", json=missing).status_code == 409


def test_answers_must_match_the_drawn_set(client: TestClient, course, learner):
    learner(course["id"])
    lesson_id = course["lessons"][0]["id"]
    quiz = client.get(f"/lessons/{lesson_id}/quiz").json()
    url = f"/lessons/{lesson_id}/quiz/attempts"
    drawn = _answers(quiz)
    outside = next(f"q{i}" for i in range(1, 9) if f"q{i}" not in drawn)
    missing_one = dict(list(drawn.items())[:4])
    with_other = missing_one | {outside: "a"}
    wrong_answer = drawn | {next(iter(drawn)): "zzz"}
    for answers, code in (
        (missing_one, "QUIZ_INCOMPLETE"),
        (with_other, "QUIZ_INCOMPLETE"),
        (wrong_answer, "QUIZ_ANSWER_MISMATCH"),
    ):
        response = client.post(url, json={"draw_id": quiz["draw_id"], "answers": answers})
        assert (response.status_code, response.json()) == (400, {"code": code})
    # the draw stays open after a rejected submission
    assert client.post(url, json={"draw_id": quiz["draw_id"], "answers": drawn}).status_code == 200


def test_pool_edited_after_the_draw(client: TestClient, course, learner, login: Login, teacher):
    student = learner(course["id"])
    lesson_id = course["lessons"][0]["id"]
    quiz = client.get(f"/lessons/{lesson_id}/quiz").json()
    login(teacher)
    renamed = [q | {"id": f"n{index}"} for index, q in enumerate(pool(8))]
    client.put(f"/lessons/{lesson_id}/quiz", json={"questions": renamed})
    login(student)
    payload = {"draw_id": quiz["draw_id"], "answers": _answers(quiz)}
    response = client.post(f"/lessons/{lesson_id}/quiz/attempts", json=payload)
    assert response.json() == {"code": "DRAW_NOT_OPEN"}
    fresh = client.get(f"/lessons/{lesson_id}/quiz").json()
    assert all(item["id"].startswith("n") for item in fresh["questions"])


def test_stale_open_draw_is_replaced(client: TestClient, course, learner, login: Login, teacher):
    student = learner(course["id"])
    lesson_id = course["lessons"][0]["id"]
    old = client.get(f"/lessons/{lesson_id}/quiz").json()
    login(teacher)
    renamed = [q | {"id": f"n{index}"} for index, q in enumerate(pool(8))]
    client.put(f"/lessons/{lesson_id}/quiz", json={"questions": renamed})
    login(student)
    new = client.get(f"/lessons/{lesson_id}/quiz").json()
    assert new["draw_id"] != old["draw_id"]
    assert all(item["id"].startswith("n") for item in new["questions"])
