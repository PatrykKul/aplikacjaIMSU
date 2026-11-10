from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.learning_style.hooks import record_quiz_result
from app.modules.learning_style.models import MaterialOpening


def _open(client: TestClient, lesson_id: int, block_id: str):
    return client.post(f"/lessons/{lesson_id}/blocks/{block_id}/open")


def _openings(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(MaterialOpening))


def _blocks(client: TestClient, lesson_id: int) -> dict:
    return client.get(f"/lessons/{lesson_id}/personalized-blocks").json()


def test_opening_a_collapsed_material_is_recorded_once(
    client: TestClient, db: Session, lesson_with_styles, fill_survey, student
):
    lesson_id = lesson_with_styles["lesson_id"]
    fill_survey(student, "V")
    assert _open(client, lesson_id, "a").status_code == 204
    assert _open(client, lesson_id, "a").status_code == 204
    assert _openings(db) == 1
    opening = db.scalar(select(MaterialOpening))
    assert (opening.block_id, opening.forms) == ("a", "A")
    assert _blocks(client, lesson_id)["opened_block_ids"] == ["a"]


def test_text_and_own_style_materials_are_not_recorded(
    client: TestClient, db: Session, lesson_with_styles, fill_survey, student
):
    lesson_id = lesson_with_styles["lesson_id"]
    fill_survey(student, "V")
    for block_id in ("t1", "v", "va"):
        assert _open(client, lesson_id, block_id).status_code == 204
    assert _openings(db) == 0


def test_unknown_block_is_404(client: TestClient, lesson_with_styles, fill_survey, student):
    fill_survey(student, "V")
    response = _open(client, lesson_with_styles["lesson_id"], "missing")
    assert response.status_code == 404
    assert response.json() == {"code": "BLOCK_NOT_FOUND"}


def test_invisible_lesson_is_404(client: TestClient, make_course, teacher, fill_survey, student):
    course = make_course(teacher, lessons=("Szkic",), published=False)
    fill_survey(student, "V")
    assert _open(client, course["lessons"][0]["id"], "a").status_code == 404


def test_only_students_with_a_survey_open_materials(
    client: TestClient, lesson_with_styles, login, student, teacher, admin
):
    lesson_id = lesson_with_styles["lesson_id"]
    login(student)
    assert _open(client, lesson_id, "a").json() == {"code": "SURVEY_REQUIRED"}
    for user in (teacher, admin):
        login(user)
        response = _open(client, lesson_id, "a")
        assert response.status_code == 403
        assert response.json() == {"code": "FORBIDDEN"}


def test_opened_forms_take_part_in_the_adaptation(
    client: TestClient, db: Session, lesson_with_styles, fill_survey, student
):
    lesson_id = lesson_with_styles["lesson_id"]
    fill_survey(student, "VVA")  # V 14 / A 6 / K 0
    _open(client, lesson_id, "a")
    feedback = record_quiz_result(db, user=student, lesson_id=lesson_id, block_id="q", percent=90)
    assert feedback.weights == {"V": 15, "A": 7, "K": 0}

    # The rule "first success per lesson and style" applies to the effective style "VA"
    again = record_quiz_result(db, user=student, lesson_id=lesson_id, block_id="q", percent=90)
    assert again.weights_changed is False


def test_openings_belong_to_one_lesson(
    client: TestClient, db: Session, lesson_with_styles, make_course, teacher, fill_survey, student
):
    lesson_id = lesson_with_styles["lesson_id"]
    fill_survey(student, "VVA")
    _open(client, lesson_id, "a")
    other = make_course(teacher, lessons=("Inna",), published=True)["lessons"][0]["id"]
    feedback = record_quiz_result(db, user=student, lesson_id=other, block_id="q", percent=90)
    assert feedback.weights == {"V": 15, "A": 6, "K": 0}
