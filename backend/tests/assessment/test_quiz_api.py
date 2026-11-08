from fastapi.testclient import TestClient

from tests.assessment.conftest import question


def _url(lesson: dict, suffix: str = "") -> str:
    return f"/lessons/{lesson['lesson_id']}/quiz{suffix}"


# --- Teacher editor ------------------------------------------------------------------------------


def test_editor_returns_answer_key(client: TestClient, lesson_with_quiz):
    quiz = client.get(_url(lesson_with_quiz, "/edit")).json()
    assert len(quiz["questions"]) == 5
    assert quiz["questions"][0]["correct_answer_id"] == "a"


def test_editor_of_lesson_without_quiz_is_empty(client: TestClient, make_course, teacher):
    course = make_course(teacher, lessons=("Pusta",))
    response = client.get(f"/lessons/{course['lessons'][0]['id']}/quiz/edit")
    assert response.json() == {"questions": []}


def test_only_the_author_edits(client: TestClient, lesson_with_quiz, login, other_teacher, student):
    login(other_teacher)
    assert client.get(_url(lesson_with_quiz, "/edit")).status_code == 404
    assert (
        client.put(_url(lesson_with_quiz), json={"questions": [question("x")]}).status_code == 404
    )
    login(student)
    assert (
        client.put(_url(lesson_with_quiz), json={"questions": [question("x")]}).status_code == 403
    )


def test_validation(client: TestClient, lesson_with_quiz):
    bad_correct = question("q1", correct="zzz")
    two_answers = question("q2") | {"answers": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}]}
    for questions in ([], [bad_correct], [two_answers], [question("q"), question("q")]):
        response = client.put(_url(lesson_with_quiz), json={"questions": questions})
        assert response.status_code == 422, questions


def test_save_replaces_and_delete_removes(client: TestClient, lesson_with_quiz):
    client.put(_url(lesson_with_quiz), json={"questions": [question("only")]})
    assert [q["id"] for q in client.get(_url(lesson_with_quiz, "/edit")).json()["questions"]] == [
        "only"
    ]
    assert client.delete(_url(lesson_with_quiz)).status_code == 204
    assert client.get(_url(lesson_with_quiz)).status_code == 404


# --- Student -------------------------------------------------------------------------------------


def test_student_gets_questions_for_own_style_without_key(
    client: TestClient, lesson_with_quiz, fill_survey, student
):
    fill_survey(student, "V")
    quiz = client.get(_url(lesson_with_quiz)).json()
    assert [q["id"] for q in quiz["questions"]] == ["q1", "q2", "qv"]
    assert quiz["hidden_count"] == 2
    assert all("correct_answer_id" not in q for q in quiz["questions"])


def test_student_without_survey(client: TestClient, lesson_with_quiz, login, student):
    login(student)
    response = client.get(_url(lesson_with_quiz))
    assert response.status_code == 403
    assert response.json() == {"code": "SURVEY_REQUIRED"}


def test_lesson_without_quiz_is_404(client: TestClient, make_course, teacher, fill_survey, student):
    course = make_course(teacher, lessons=("Bez quizu",), published=True)
    fill_survey(student, "V")
    response = client.get(f"/lessons/{course['lessons'][0]['id']}/quiz")
    assert response.json() == {"code": "QUIZ_NOT_FOUND"}


def test_unpublished_course_quiz_is_hidden(
    client: TestClient, make_course, teacher, fill_survey, student
):
    course = make_course(teacher, lessons=("Szkic",), published=False)
    lesson_id = course["lessons"][0]["id"]
    client.put(f"/lessons/{lesson_id}/quiz", json={"questions": [question("q1")]})
    fill_survey(student, "V")
    assert client.get(f"/lessons/{lesson_id}/quiz").status_code == 404


def test_server_scores_and_updates_adaptation(
    client: TestClient, lesson_with_quiz, fill_survey, student
):
    profile = fill_survey(student, "VVA")  # V 14 / A 6 / K 0
    assert profile["weights"] == {"V": 14, "A": 6, "K": 0}
    response = client.post(
        _url(lesson_with_quiz, "/attempts"), json={"answers": {"q1": "a", "q2": "a", "qv": "b"}}
    )
    assert response.status_code == 200, response.json()
    body = response.json()
    assert (body["correct_count"], body["total"], body["percent"]) == (2, 3, 67)
    assert [r["correct"] for r in body["results"]] == [True, True, False]
    adaptation = body["adaptation"]
    assert adaptation["passed"] is False  # 67% < 70%
    assert adaptation["weights"] == {"V": 13, "A": 6, "K": 0}
    assert "„Wykres”: 67%" in adaptation["why"]
    assert client.get("/profile/learning-style").json()["weights"] == {"V": 13, "A": 6, "K": 0}


def test_question_of_another_style_cannot_be_answered(
    client: TestClient, lesson_with_quiz, fill_survey, student
):
    fill_survey(student, "V")
    answers = {"q1": "a", "q2": "a", "qv": "a", "qa": "a"}
    response = client.post(_url(lesson_with_quiz, "/attempts"), json={"answers": answers})
    assert response.status_code == 400
    assert response.json() == {"code": "QUIZ_INCOMPLETE"}


def test_wrong_answer_id(client: TestClient, lesson_with_quiz, fill_survey, student):
    fill_survey(student, "V")
    answers = {"q1": "a", "q2": "a", "qv": "nope"}
    response = client.post(_url(lesson_with_quiz, "/attempts"), json={"answers": answers})
    assert response.json() == {"code": "QUIZ_ANSWER_MISMATCH"}


def test_repeated_attempts_do_not_farm_weights(
    client: TestClient, lesson_with_quiz, fill_survey, student
):
    fill_survey(student, "V")  # V 20
    perfect = {"answers": {"q1": "a", "q2": "a", "qv": "a"}}
    first = client.post(_url(lesson_with_quiz, "/attempts"), json=perfect).json()
    second = client.post(_url(lesson_with_quiz, "/attempts"), json=perfect).json()
    assert first["adaptation"]["weights"]["V"] == 21
    assert first["adaptation"]["weights_changed"] is True
    assert second["adaptation"]["weights"]["V"] == 21
    assert second["adaptation"]["weights_changed"] is False


def test_teacher_preview_attempt_has_no_adaptation(client: TestClient, lesson_with_quiz):
    answers = {"q1": "a", "q2": "a", "qv": "a", "qa": "a", "qk": "a"}
    body = client.post(_url(lesson_with_quiz, "/attempts"), json={"answers": answers}).json()
    assert body["percent"] == 100
    assert body["adaptation"] is None
