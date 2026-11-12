from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from tests.content.conftest import attachment, text_block
from tests.curriculum.conftest import CONCLUSIONS, OUTLINE

YOUTUBE = "https://youtu.be/dQw4w9WgXcQ"


@pytest.fixture(autouse=True)
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path / "uploads")
    return tmp_path / "uploads"


def question(number: int) -> dict[str, Any]:
    return {
        "id": f"q{number}",
        "text": f"Pytanie {number}",
        "answers": [
            {"id": "a", "text": "Tak"},
            {"id": "b", "text": "Nie"},
            {"id": "c", "text": "?"},
        ],
        "correct_answer_id": "a",
        "explanation": "Bo tak",
    }


def save_quiz(client: TestClient, lesson_id: int, size: int) -> None:
    questions = [question(number) for number in range(1, size + 1)]
    response = client.put(f"/lessons/{lesson_id}/quiz", json={"questions": questions})
    assert response.status_code == 200, response.json()


@pytest.fixture
def complete_lesson(client: TestClient) -> Callable[[int], None]:
    """Fill a lesson of the logged-in author so that it is ready to publish."""

    def _complete(lesson_id: int) -> None:
        pdf = client.post(
            "/files", files={"file": ("karta.pdf", b"%PDF-1.4", "application/pdf")}
        ).json()
        client.patch(f"/lessons/{lesson_id}", json={"outline": OUTLINE, "conclusions": CONCLUSIONS})
        versions = {
            "V": [text_block(), attachment("video", "v1", youtube_url=YOUTUBE)],
            "A": [attachment("audio", "a1", transcript="Posłuchaj"), text_block()],
            "K": [text_block(), attachment("pdf", "p1", file_id=pdf["id"])],
        }
        for form, blocks in versions.items():
            response = client.put(f"/lessons/{lesson_id}/versions/{form}", json={"blocks": blocks})
            assert response.status_code == 200, response.json()
        save_quiz(client, lesson_id, 5)

    return _complete
