from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings

PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


@pytest.fixture(autouse=True)
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Uploaded files go to a temporary directory in every content test."""
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path / "uploads")
    return tmp_path / "uploads"


@pytest.fixture
def upload(client: TestClient) -> Callable[..., dict[str, Any]]:
    """Upload a file as the logged-in user and return the response body."""

    def _upload(name: str = "obraz.png", content: bytes = PNG) -> dict[str, Any]:
        response = client.post(
            "/files", files={"file": (name, content, "application/octet-stream")}
        )
        assert response.status_code == 201, response.json()
        return response.json()

    return _upload


def text_block(block_id: str = "t1", text: str = "Procent to setna część") -> dict[str, Any]:
    paragraph = {"type": "paragraph", "content": [{"type": "text", "text": text}]}
    return {"id": block_id, "type": "text", "doc": {"type": "doc", "content": [paragraph]}}


def attachment(kind: str, block_id: str = "a1", **fields: Any) -> dict[str, Any]:
    return {
        "id": block_id,
        "type": "attachment",
        "kind": kind,
        "forms": ["V"],
        "title": "Załącznik",
        **fields,
    }
