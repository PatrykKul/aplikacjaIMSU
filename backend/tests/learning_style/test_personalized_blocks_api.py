from fastapi.testclient import TestClient


def _ids(response) -> list[str]:
    return [block["id"] for block in response.json()["blocks"]]


def test_student_sees_common_and_own_style(
    client: TestClient, lesson_with_styles, fill_survey, student
):
    fill_survey(student, "V")
    response = client.get(f"/lessons/{lesson_with_styles['lesson_id']}/personalized-blocks")
    assert response.status_code == 200
    assert _ids(response) == ["t1", "v", "va"]
    body = response.json()
    assert body["style"] == "V"
    assert body["hidden_count"] == 2
    assert "wzrokowiec" in body["explanation"]


def test_mixed_style(client: TestClient, lesson_with_styles, fill_survey, student):
    fill_survey(student, "AK")
    response = client.get(f"/lessons/{lesson_with_styles['lesson_id']}/personalized-blocks")
    assert _ids(response) == ["t1", "a", "k", "va"]


def test_new_style_changes_the_lesson(client: TestClient, lesson_with_styles, fill_survey, student):
    fill_survey(student, "V")
    client.put("/profile/learning-style", json={"style": "K"})
    response = client.get(f"/lessons/{lesson_with_styles['lesson_id']}/personalized-blocks")
    assert _ids(response) == ["t1", "k"]


def test_student_without_survey_gets_403(client: TestClient, lesson_with_styles, login, student):
    login(student)
    response = client.get(f"/lessons/{lesson_with_styles['lesson_id']}/personalized-blocks")
    assert response.status_code == 403
    assert response.json() == {"code": "SURVEY_REQUIRED"}


def test_teacher_sees_everything(client: TestClient, lesson_with_styles, login, teacher):
    login(teacher)
    response = client.get(f"/lessons/{lesson_with_styles['lesson_id']}/personalized-blocks")
    assert _ids(response) == ["t1", "v", "a", "k", "va"]
    assert response.json()["style"] is None
    assert response.json()["hidden_count"] == 0


def test_unpublished_lesson_is_404(client: TestClient, make_course, teacher, fill_survey, student):
    course = make_course(teacher, lessons=("Szkic",), published=False)
    fill_survey(student, "V")
    lesson_id = course["lessons"][0]["id"]
    response = client.get(f"/lessons/{lesson_id}/personalized-blocks")
    assert response.status_code == 404


def test_original_blocks_endpoint_is_unchanged(
    client: TestClient, lesson_with_styles, fill_survey, student
):
    fill_survey(student, "V")
    response = client.get(f"/lessons/{lesson_with_styles['lesson_id']}/blocks")
    assert _ids(response) == ["t1", "v", "a", "k", "va"]
