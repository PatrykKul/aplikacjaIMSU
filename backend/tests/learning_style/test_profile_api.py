from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.learning_style.models import LearningProfile


def test_profile_before_survey(client: TestClient, login, student):
    login(student)
    assert client.get("/profile/learning-style").json() == {
        "survey_completed": False,
        "style": None,
        "style_source": None,
        "weights": None,
        "last_result": None,
        "explanation": None,
        "proposal": None,
    }


def test_teacher_profile_is_empty(client: TestClient, login, teacher):
    login(teacher)
    assert client.get("/profile/learning-style").json()["survey_completed"] is False


def test_change_style_needs_survey(client: TestClient, login, student):
    login(student)
    response = client.put("/profile/learning-style", json={"style": "A"})
    assert response.status_code == 403
    assert response.json() == {"code": "SURVEY_REQUIRED"}


def test_manual_style_and_restore(client: TestClient, fill_survey, student):
    fill_survey(student, "V")
    manual = client.put("/profile/learning-style", json={"style": "AK"}).json()
    assert manual["style"] == "AK"
    assert manual["style_source"] == "manual"
    assert "ręcznie" in manual["explanation"]
    restored = client.delete("/profile/learning-style").json()
    assert restored["style"] == "V"
    assert restored["style_source"] == "survey"


def test_invalid_style(client: TestClient, fill_survey, student):
    fill_survey(student, "V")
    response = client.put("/profile/learning-style", json={"style": "AV"})
    assert response.status_code == 422


def test_no_proposal(client: TestClient, fill_survey, student):
    fill_survey(student, "V")
    response = client.post("/profile/learning-style/proposal/accept")
    assert response.status_code == 409
    assert response.json() == {"code": "NO_PROPOSAL"}


def _make_auditory_leader(db: Session, user_id: int) -> None:
    profile = db.get(LearningProfile, user_id)
    profile.weights = {"V": 10, "A": 12, "K": 0}
    db.commit()


def test_accept_proposal(client: TestClient, db: Session, fill_survey, student):
    fill_survey(student, "V")
    _make_auditory_leader(db, student.id)
    proposal = client.get("/profile/learning-style").json()["proposal"]
    assert proposal["style"] == "A"
    assert proposal["message"] == "Wagi wskazują na materiały słuchowe – przełączyć?"
    assert "V 10 / A 12 / K 0" in proposal["why"]
    accepted = client.post("/profile/learning-style/proposal/accept").json()
    assert accepted["style"] == "A"
    assert accepted["style_source"] == "adaptation"
    assert accepted["proposal"] is None


def test_reject_proposal_is_not_repeated(client: TestClient, db: Session, fill_survey, student):
    fill_survey(student, "V")
    _make_auditory_leader(db, student.id)
    rejected = client.post("/profile/learning-style/proposal/reject").json()
    assert rejected["style"] == "V"
    assert rejected["proposal"] is None


def test_manual_style_turns_proposals_off(client: TestClient, db: Session, fill_survey, student):
    fill_survey(student, "V")
    _make_auditory_leader(db, student.id)
    profile = client.put("/profile/learning-style", json={"style": "K"}).json()
    assert profile["proposal"] is None
