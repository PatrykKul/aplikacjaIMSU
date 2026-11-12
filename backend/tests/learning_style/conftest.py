from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.models import User, UserRole
from app.modules.learning_style.models import SurveyAnswer, SurveyQuestion


@pytest.fixture
def answer_key(db: Session) -> dict[int, dict[str, int]]:
    """question id -> {style: answer id} for the active survey (read straight from the database)."""
    key: dict[int, dict[str, int]] = {}
    rows = db.execute(
        select(SurveyAnswer.question_id, SurveyAnswer.style, SurveyAnswer.id)
        .join(SurveyQuestion)
        .where(SurveyQuestion.is_active)
    )
    for question_id, style, answer_id in rows:
        key.setdefault(question_id, {})[style] = answer_id
    return key


def choices(answer_key: dict[int, dict[str, int]], styles: str) -> list[dict[str, int]]:
    """Answers for every question; `styles` is repeated, e.g. "V" or "VVA"."""
    return [
        {"question_id": question_id, "answer_id": by_style[styles[index % len(styles)]]}
        for index, (question_id, by_style) in enumerate(sorted(answer_key.items()))
    ]


@pytest.fixture
def fill_survey(
    client: TestClient, login: Callable[[User], None], answer_key: dict[int, dict[str, int]]
) -> Callable[..., dict[str, Any]]:
    """Log `user` in and fill in the survey with answers following `styles`."""

    def _fill(user: User, styles: str = "V") -> dict[str, Any]:
        login(user)
        response = client.post("/survey/answers", json={"answers": choices(answer_key, styles)})
        assert response.status_code == 200, response.json()
        return response.json()

    return _fill


# --- Courses with question pools and students taking quizzes (v3 engine) ------------------------

LESSONS = ("Lekcja 1", "Lekcja 2", "Lekcja 3", "Lekcja 4")


def survey_styles(v: int, a: int, k: int) -> str:
    """Answers giving exactly V/A/K points (the survey has 20 questions)."""
    assert v + a + k == 20
    return "V" * v + "A" * a + "K" * k


def pool(size: int = 8) -> list[dict[str, Any]]:
    """Questions q1..qN, the correct answer is always "a"."""
    return [
        {
            "id": f"q{number}",
            "text": f"Pytanie {number}",
            "answers": [
                {"id": "a", "text": "A"},
                {"id": "b", "text": "B"},
                {"id": "c", "text": "C"},
            ],
            "correct_answer_id": "a",
            "explanation": f"Wyjaśnienie {number}",
        }
        for number in range(1, size + 1)
    ]


def take_quiz(client: TestClient, lesson_id: int, percent: int) -> dict[str, Any]:
    """Draw (or reuse the open draw) and answer so that the score is `percent`."""
    quiz = client.get(f"/lessons/{lesson_id}/quiz")
    assert quiz.status_code == 200, quiz.json()
    questions = quiz.json()["questions"]
    correct = percent * len(questions) // 100
    answers = {q["id"]: "a" if index < correct else "b" for index, q in enumerate(questions)}
    response = client.post(
        f"/lessons/{lesson_id}/quiz/attempts",
        json={"draw_id": quiz.json()["draw_id"], "answers": answers},
    )
    assert response.status_code == 200, response.json()
    assert response.json()["percent"] == percent
    return response.json()


def set_form(
    client: TestClient, lesson_id: int, form: str, source: str = "suggestion"
) -> dict[str, Any]:
    response = client.put(f"/lessons/{lesson_id}/study/form", json={"form": form, "source": source})
    assert response.status_code == 200, response.json()
    return response.json()


def journal_types(client: TestClient) -> list[str]:
    """Event types of the logged-in student, oldest first."""
    return [entry["type"] for entry in reversed(client.get("/me/journal").json())]


def last_event(client: TestClient, type_: str) -> dict[str, Any]:
    return next(entry for entry in client.get("/me/journal").json() if entry["type"] == type_)


@pytest.fixture
def quiz_course(
    client: TestClient, make_course: Callable[..., dict[str, Any]], teacher: User
) -> Callable[..., dict[str, Any]]:
    """A published course of the `teacher` with a pool of questions in every lesson."""

    def _make(
        *, title: str = "Matematyka", lessons: tuple[str, ...] = LESSONS, pool_size: int = 8
    ) -> dict[str, Any]:
        course = make_course(teacher, title=title, lessons=lessons, published=True)
        for lesson in course["lessons"]:
            response = client.put(
                f"/lessons/{lesson['id']}/quiz", json={"questions": pool(pool_size)}
            )
            assert response.status_code == 200, response.json()
        return course

    return _make


@pytest.fixture
def learner(
    make_user: Callable[..., User],
    enroll: Callable[..., None],
    fill_survey: Callable[..., dict[str, Any]],
) -> Callable[..., User]:
    """A student accepted in the course who filled in the survey (stays logged in)."""

    def _make(course_id: int | None = None, styles: str = "V") -> User:
        user = make_user(UserRole.STUDENT)
        if course_id is not None:
            enroll(user, course_id)
        fill_survey(user, styles)
        return user

    return _make


@pytest.fixture
def course(quiz_course: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    """Default course: 4 published lessons with 8 questions each."""
    return quiz_course()
