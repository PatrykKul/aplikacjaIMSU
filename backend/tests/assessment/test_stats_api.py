"""Questions to review (student) and question analysis (author) through the API."""

from typing import Any

from fastapi.testclient import TestClient

from app.modules.identity.models import ApprovalStatus


def answer(client: TestClient, lesson_id: int, wrong: dict[str, str] | None = None) -> list[str]:
    """Answer the drawn set: "a" (correct) unless `wrong` names another answer; returns the
    question order of the draw."""
    quiz = client.get(f"/lessons/{lesson_id}/quiz")
    assert quiz.status_code == 200, quiz.json()
    order = [question["id"] for question in quiz.json()["questions"]]
    answers = {qid: (wrong or {}).get(qid, "a") for qid in order}
    response = client.post(
        f"/lessons/{lesson_id}/quiz/attempts",
        json={"draw_id": quiz.json()["draw_id"], "answers": answers},
    )
    assert response.status_code == 200, response.json()
    return order


def review(client: TestClient) -> list[dict[str, Any]]:
    response = client.get("/me/review-questions")
    assert response.status_code == 200, response.json()
    return response.json()


def ids(course: dict[str, Any]) -> list[int]:
    return [lesson["id"] for lesson in course["lessons"]]


# --- Questions to review -------------------------------------------------------------------------


def test_review_questions(client: TestClient, quiz_course, learner, login, teacher):
    course = quiz_course(pool_size=5)  # every draw shows the whole pool
    l1, l2 = ids(course)[:2]
    student = learner(course["id"], "V")
    assert review(client) == []

    order = answer(client, l1, {"q1": "b", "q2": "c"})  # 60%
    items = review(client)
    assert [item["question_id"] for item in items] == [q for q in order if q in ("q1", "q2")]
    q2 = next(item for item in items if item["question_id"] == "q2")
    assert q2["answered_at"] is not None
    assert {key: value for key, value in q2.items() if key != "answered_at"} == {
        "course_id": course["id"],
        "course_title": "Matematyka",
        "lesson_id": l1,
        "lesson_title": "Lekcja 1",
        "number": 1,
        "question_id": "q2",
        "text": "Pytanie 2",
        "chosen_answer": {"id": "c", "text": "C"},
        "correct_answer": {"id": "a", "text": "A"},
        "explanation": "Wyjaśnienie 2",
    }

    # only the last submitted draw of the lesson counts
    answer(client, l1, {"q3": "b"})  # 80%: passed
    assert [(item["lesson_id"], item["question_id"]) for item in review(client)] == [(l1, "q3")]
    # newest first
    answer(client, l2, {"q5": "c"})
    assert [(item["lesson_id"], item["question_id"]) for item in review(client)] == [
        (l2, "q5"),
        (l1, "q3"),
    ]

    # another student sees only their own questions
    learner(course["id"], "V")
    assert review(client) == []

    # a course the student is no longer accepted in drops out
    login(teacher)
    client.post(f"/courses/{course['id']}/enrollments/{student.id}/reject")
    login(student)
    assert review(client) == []


def test_review_questions_only_for_students(client: TestClient, login, teacher, admin):
    for user in (teacher, admin):
        login(user)
        response = client.get("/me/review-questions")
        assert (response.status_code, response.json()) == (403, {"code": "FORBIDDEN"})


# --- Question analysis ---------------------------------------------------------------------------


def stats_row(qid: str, drawn: int, correct: int, **rest: Any) -> dict[str, Any]:
    return {
        "question_id": qid,
        "text": f"Pytanie {qid[1:]}",
        "drawn": drawn,
        "correct": correct,
        "correct_percent": rest.get("correct_percent"),
        "top_wrong": rest.get("top_wrong"),
        "rating": rest.get("rating"),
    }


def test_question_stats(client: TestClient, quiz_course, learner, login, teacher):
    course = quiz_course(pool_size=5)
    l1, l2 = ids(course)[:2]
    for index in range(5):
        learner(course["id"], "V")
        wrong = {"q1": "b"} if index >= 2 else {"q1": "b", "q3": "c"}
        answer(client, l1, wrong)  # 60% or 80%
    answer(client, l2, {"q1": "c"})  # the last student passed lesson 1
    rejected = learner(course["id"], "V")
    answer(client, l1)  # all correct, but the student is rejected later
    login(teacher)
    client.post(f"/courses/{course['id']}/enrollments/{rejected.id}/reject")

    response = client.get(f"/courses/{course['id']}/question-stats")
    assert response.status_code == 200, response.json()
    body = response.json()

    assert [(lesson["lesson_id"], lesson["title"], lesson["number"]) for lesson in body] == [
        (lesson["id"], lesson["title"], number)
        for number, lesson in enumerate(course["lessons"], 1)
    ]
    first = body[0]["questions"]
    assert [row["question_id"] for row in first] == ["q1", "q3", "q2", "q4", "q5"]
    assert first[0] == stats_row(
        "q1",
        5,
        0,
        correct_percent=0,
        top_wrong={"answer_id": "b", "text": "B", "count": 5, "percent": 100},
        rating="hard",
    )
    assert first[1] == stats_row(
        "q3",
        5,
        3,
        correct_percent=60,
        top_wrong={"answer_id": "c", "text": "C", "count": 2, "percent": 40},
        rating="normal",
    )
    assert first[2] == stats_row("q2", 5, 5, correct_percent=100, rating="easy")

    # below 5 draws: counts only, the pool order
    second = body[1]["questions"]
    assert [row["question_id"] for row in second] == ["q1", "q2", "q3", "q4", "q5"]
    assert second[0] == stats_row(
        "q1", 1, 0, top_wrong={"answer_id": "c", "text": "C", "count": 1, "percent": None}
    )
    assert second[1] == stats_row("q2", 1, 1)
    assert {row["drawn"] for row in body[2]["questions"]} == {0}


def test_question_stats_access(
    client: TestClient, quiz_course, login, teacher, other_teacher, student, admin, db
):
    course = quiz_course(pool_size=5)
    url = f"/courses/{course['id']}/question-stats"
    login(other_teacher)
    response = client.get(url)
    assert (response.status_code, response.json()) == (404, {"code": "COURSE_NOT_FOUND"})
    for user in (student, admin):
        login(user)
        response = client.get(url)
        assert (response.status_code, response.json()) == (403, {"code": "FORBIDDEN"})
    login(teacher)
    assert client.get("/courses/999999/question-stats").json() == {"code": "COURSE_NOT_FOUND"}
    teacher.approval_status = ApprovalStatus.PENDING
    db.commit()
    response = client.get(url)
    assert (response.status_code, response.json()) == (403, {"code": "TEACHER_NOT_APPROVED"})
