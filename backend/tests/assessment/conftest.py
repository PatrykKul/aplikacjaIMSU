from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User

# Fixtures of the learning-style tests (survey filling, answer key)
from tests.learning_style.conftest import (  # noqa: F401
    answer_key,
    fill_survey,
    lesson_with_styles,
)


def question(qid: str, form: str | None = None, correct: str = "a") -> dict[str, Any]:
    return {
        "id": qid,
        "text": f"Pytanie {qid}",
        "form": form,
        "answers": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}, {"id": "c", "text": "C"}],
        "correct_answer_id": correct,
    }


@pytest.fixture
def lesson_with_quiz(
    client: TestClient, teacher: User, make_course: Callable[..., dict[str, Any]]
) -> dict[str, Any]:
    """Published lesson whose quiz has 2 common questions and one for each of V, A, K."""
    course = make_course(teacher, title="Funkcja liniowa", lessons=("Wykres",), published=True)
    lesson_id = course["lessons"][0]["id"]
    questions = [
        question("q1"),
        question("q2"),
        question("qv", "V"),
        question("qa", "A"),
        question("qk", "K"),
    ]
    response = client.put(f"/lessons/{lesson_id}/quiz", json={"questions": questions})
    assert response.status_code == 200, response.json()
    return {"course": course, "lesson_id": lesson_id}
