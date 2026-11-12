"""Course hint (R8), "My progress", the journal, course statistics and student details."""

from typing import Any

from fastapi.testclient import TestClient

from tests.learning_style.conftest import set_form, survey_styles, take_quiz


def first_lessons(course: dict[str, Any], count: int = 2) -> list[int]:
    return [lesson["id"] for lesson in course["lessons"][:count]]


# --- Course hint (R8) ----------------------------------------------------------------------------


def test_hint_for_a_student_without_results(client: TestClient, course, learner):
    l1 = first_lessons(course)[0]
    for percent in (80, 100, 60):
        learner(course["id"], "A")
        take_quiz(client, l1, percent)  # A: 3 students, average 80
    for percent in (100, 100):
        learner(course["id"], "K")
        take_quiz(client, l1, percent)  # K: 2 students, average 100
    learner(course["id"], "V")
    take_quiz(client, l1, 100)  # V: 1 student only
    learner(course["id"], "V")
    hint = client.get(f"/courses/{course['id']}/hint")
    assert hint.status_code == 200
    assert hint.json() == {"form": "K", "average": 100, "students": 2, "results": 2}
    take_quiz(client, l1, 40)
    assert client.get(f"/courses/{course['id']}/hint").json() is None


def test_no_hint_without_data(client: TestClient, course, learner):
    learner(course["id"], "V")
    assert client.get(f"/courses/{course['id']}/hint").json() is None


def test_hint_access(client: TestClient, course, learner, login, teacher, enroll, make_user):
    learner(None, "V")  # not enrolled
    response = client.get(f"/courses/{course['id']}/hint")
    assert (response.status_code, response.json()) == (403, {"code": "ENROLLMENT_REQUIRED"})
    assert client.get("/courses/999999/hint").status_code == 404
    login(teacher)
    assert client.get(f"/courses/{course['id']}/hint").json() == {"code": "FORBIDDEN"}


# --- Progress and journal ------------------------------------------------------------------------


def test_progress(client: TestClient, course, quiz_course, learner, enroll):
    other = quiz_course(title="Angielski", lessons=("Unit 1",))
    student = learner(course["id"], survey_styles(9, 8, 3))
    enroll(student, other["id"], "pending")
    l1, l2 = first_lessons(course)
    take_quiz(client, l1, 40)
    take_quiz(client, l1, 80)
    set_form(client, l1, "A")
    take_quiz(client, l1, 100)
    progress = client.get("/me/progress").json()
    assert [point["percentages"] for point in progress["history"]] == [
        {"V": 45, "A": 40, "K": 15},
        {"V": 35, "A": 47, "K": 18},
        {"V": 28, "A": 57, "K": 15},
    ]
    assert progress["history"][0]["style"] == "V"
    assert progress["courses"] == [
        {
            "id": course["id"],
            "title": "Matematyka",
            "passed": 1,
            "total": 4,
            "next_lesson": {"id": l2, "title": "Lekcja 2", "number": 2},
        }
    ]
    (lesson,) = progress["lessons"]
    assert (lesson["course_id"], lesson["course_title"]) == (course["id"], "Matematyka")
    assert (lesson["lesson_id"], lesson["lesson_title"], lesson["number"]) == (l1, "Lekcja 1", 1)
    assert lesson["passed"] is True
    assert [(a["form"], a["percent"], a["passed"], a["counted"]) for a in lesson["attempts"]] == [
        ("V", 40, False, True),
        ("V", 80, True, False),
        ("A", 100, True, True),
    ]


def test_journal_newest_first_with_course_and_lesson(client: TestClient, course, learner):
    learner(course["id"], "V")
    l1 = first_lessons(course)[0]
    take_quiz(client, l1, 80)
    journal = client.get("/me/journal").json()
    assert [entry["type"] for entry in journal] == ["quiz_attempt", "survey_completed"]
    assert journal[0]["course"] == {"id": course["id"], "title": "Matematyka"}
    assert journal[0]["lesson"] == {"id": l1, "title": "Lekcja 1"}
    assert journal[1]["course"] is None and journal[1]["lesson"] is None
    assert set(journal[0]) == {"id", "type", "at", "course", "lesson", "data"}


def test_progress_and_journal_only_for_students(client: TestClient, login, teacher, admin):
    for user in (teacher, admin):
        login(user)
        assert client.get("/me/progress").json() == {"code": "FORBIDDEN"}
        assert client.get("/me/journal").json() == {"code": "FORBIDDEN"}


# --- Course statistics (teacher) -----------------------------------------------------------------


def test_course_stats(client: TestClient, course, learner, make_user, enroll, login, teacher):
    l1 = first_lessons(course)[0]
    anna = learner(course["id"], "A")
    take_quiz(client, l1, 80)
    take_quiz(client, l1, 100)  # retry: an attempt, not a counted result
    bartek = learner(course["id"], "A")
    take_quiz(client, l1, 60)
    learner(course["id"], "V")
    take_quiz(client, l1, 40)
    take_quiz(client, l1, 40)
    without_survey = make_user()
    enroll(without_survey, course["id"])
    enroll(make_user(), course["id"], "pending")
    login(teacher)
    stats = client.get(f"/courses/{course['id']}/stats")
    assert stats.status_code == 200
    body = stats.json()
    assert body["forms"] == {
        "V": {"average": 40, "counted_results": 1, "attempts": 2, "students": 1},
        "A": {"average": 70, "counted_results": 2, "attempts": 3, "students": 2},
        "K": {"average": None, "counted_results": 0, "attempts": 0, "students": 0},
    }
    assert body["styles"] == {"V": 1, "A": 2, "K": 0, "none": 1}
    assert body["pending_requests"] == 1
    rows = {row["id"]: row for row in body["students"]}
    assert len(rows) == 4
    assert rows[anna.id]["style"] == "A"
    assert rows[anna.id]["percentages"] == {"V": 5, "A": 90, "K": 5}
    assert (rows[anna.id]["passed"], rows[anna.id]["total"]) == (1, 4)
    assert rows[anna.id]["average"] == 80
    assert rows[anna.id]["last_activity"] is not None
    assert rows[anna.id]["open_proposal"] is None
    assert rows[bartek.id]["average"] == 60
    empty = rows[without_survey.id]
    assert (empty["style"], empty["percentages"], empty["average"]) == (None, None, None)
    assert empty["last_activity"] is None


def test_stats_and_hint_skip_a_student_rejected_later(
    client: TestClient, course, learner, login, teacher
):
    l1 = first_lessons(course)[0]
    for percent in (80, 100):
        learner(course["id"], "A")
        take_quiz(client, l1, percent)
    rejected = learner(course["id"], "A")
    take_quiz(client, l1, 0)
    login(teacher)
    decision = client.post(f"/courses/{course['id']}/enrollments/{rejected.id}/reject")
    assert decision.status_code == 200
    forms = client.get(f"/courses/{course['id']}/stats").json()["forms"]
    assert forms["A"] == {"average": 90, "counted_results": 2, "attempts": 2, "students": 2}
    learner(course["id"], "V")
    hint = client.get(f"/courses/{course['id']}/hint").json()
    assert (hint["form"], hint["average"], hint["students"]) == ("A", 90, 2)


def test_stats_show_the_open_proposal(client: TestClient, course, learner, login, teacher):
    student = learner(course["id"], survey_styles(9, 8, 3))
    l1 = first_lessons(course)[0]
    take_quiz(client, l1, 40)
    set_form(client, l1, "A")
    take_quiz(client, l1, 80)  # A confirmed and higher than V -> proposal
    login(teacher)
    rows = {
        row["id"]: row for row in client.get(f"/courses/{course['id']}/stats").json()["students"]
    }
    assert rows[student.id]["open_proposal"] == {"to": "A", "kind": "switch"}


def test_stats_only_for_the_author(client: TestClient, course, login, other_teacher, learner):
    login(other_teacher)
    response = client.get(f"/courses/{course['id']}/stats")
    assert (response.status_code, response.json()) == (404, {"code": "COURSE_NOT_FOUND"})
    learner(course["id"], "V")
    assert client.get(f"/courses/{course['id']}/stats").status_code == 403


# --- Student details (teacher) -------------------------------------------------------------------


def test_student_detail(client: TestClient, course, quiz_course, learner, enroll, login, teacher):
    other = quiz_course(title="Angielski", lessons=("Unit 1",))
    student = learner(course["id"], "V")
    enroll(student, other["id"])
    take_quiz(client, first_lessons(course)[0], 80)
    take_quiz(client, other["lessons"][0]["id"], 100)
    client.put("/profile/learning-style", json={"style": "K"})
    login(teacher)
    detail = client.get(f"/courses/{course['id']}/students/{student.id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["student"] == {
        "id": student.id,
        "display_name": student.display_name,
        "email": student.email,
    }
    assert body["profile"]["style"] == "K"
    assert body["profile"]["trial"]["source"] == "manual"
    assert len(body["history"]) == 4  # survey, two counted results, style change
    assert [lesson["course_id"] for lesson in body["lessons"]] == [course["id"]]
    types = [entry["type"] for entry in body["journal"]]
    assert types == ["trial_started", "manual_style_change", "quiz_attempt", "survey_completed"]
    assert all(
        entry["course"] in (None, {"id": course["id"], "title": "Matematyka"})
        for entry in body["journal"]
    )


def test_student_detail_only_for_accepted_students(
    client: TestClient, course, learner, enroll, make_user, login, teacher, other_teacher
):
    accepted = learner(course["id"], "V")
    pending = make_user()
    enroll(pending, course["id"], "pending")
    stranger = make_user()
    login(teacher)
    for user_id in (pending.id, stranger.id, 999999):
        response = client.get(f"/courses/{course['id']}/students/{user_id}")
        assert (response.status_code, response.json()) == (404, {"code": "STUDENT_NOT_FOUND"})
    login(other_teacher)
    response = client.get(f"/courses/{course['id']}/students/{accepted.id}")
    assert response.json() == {"code": "COURSE_NOT_FOUND"}
