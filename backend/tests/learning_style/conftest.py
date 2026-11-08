from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.identity.models import User
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


def text_block(block_id: str) -> dict[str, Any]:
    paragraph = {"type": "paragraph", "content": [{"type": "text", "text": "Treść"}]}
    return {"id": block_id, "type": "text", "doc": {"type": "doc", "content": [paragraph]}}


def link(block_id: str, forms: list[str]) -> dict[str, Any]:
    return {
        "id": block_id,
        "type": "attachment",
        "kind": "link",
        "forms": forms,
        "title": f"Materiał {block_id}",
        "url": "https://example.com/material",
    }


@pytest.fixture
def lesson_with_styles(
    client: TestClient, teacher: User, make_course: Callable[..., dict[str, Any]]
) -> dict[str, Any]:
    """Published lesson with a common text and attachments for V, A, K and V+A."""
    course = make_course(teacher, title="Funkcja liniowa", lessons=("Wykres",), published=True)
    lesson_id = course["lessons"][0]["id"]
    blocks = [
        text_block("t1"),
        link("v", ["V"]),
        link("a", ["A"]),
        link("k", ["K"]),
        link("va", ["V", "A"]),
    ]
    response = client.put(f"/lessons/{lesson_id}/blocks", json={"blocks": blocks})
    assert response.status_code == 200, response.json()
    return {"course": course, "lesson_id": lesson_id}
