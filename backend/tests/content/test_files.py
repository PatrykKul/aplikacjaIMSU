from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.modules.identity.models import User
from tests.content.conftest import PNG

Upload = Callable[..., dict[str, Any]]
Login = Callable[[User], None]


@pytest.mark.parametrize(
    ("name", "content_type", "kind"),
    [
        ("Wykres.PNG", "image/png", "image"),
        ("zdjecie.jpg", "image/jpeg", "image"),
        ("nagranie.mp3", "audio/mpeg", "audio"),
        ("film.mp4", "video/mp4", "video"),
        ("karta pracy.pdf", "application/pdf", "pdf"),
    ],
)
def test_teacher_uploads_allowed_file(
    login: Login,
    teacher: User,
    upload: Upload,
    upload_dir: Path,
    name: str,
    content_type: str,
    kind: str,
) -> None:
    login(teacher)

    file = upload(name, b"abc")

    assert file["original_name"] == name
    assert file["content_type"] == content_type
    assert file["kind"] == kind
    assert file["size"] == 3
    assert file["url"] == f"/files/{file['id']}"
    stored = list(upload_dir.iterdir())
    assert len(stored) == 1
    assert stored[0].name != name  # random name on disk
    assert stored[0].suffix == Path(name).suffix.lower()


@pytest.mark.parametrize("name", ["rysunek.svg", "strona.html", "program.exe", "bez_rozszerzenia"])
def test_other_file_types_are_rejected(
    client: TestClient, login: Login, teacher: User, upload_dir: Path, name: str
) -> None:
    login(teacher)

    response = client.post("/files", files={"file": (name, b"abc", "image/png")})

    assert response.status_code == 400
    assert response.json()["code"] == "FILE_TYPE_NOT_ALLOWED"
    assert not upload_dir.exists() or not any(upload_dir.iterdir())


def test_too_large_file_is_rejected_and_not_kept(
    client: TestClient,
    login: Login,
    teacher: User,
    upload_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 10)
    login(teacher)

    response = client.post("/files", files={"file": ("film.mp4", b"x" * 11, "video/mp4")})

    assert response.status_code == 413
    assert response.json()["code"] == "FILE_TOO_LARGE"
    assert not any(upload_dir.iterdir())


def test_empty_file_is_rejected(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)
    response = client.post("/files", files={"file": ("pusty.png", b"", "image/png")})
    assert response.status_code == 400
    assert response.json()["code"] == "FILE_EMPTY"


def test_upload_requires_file_field(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)
    assert client.post("/files").status_code == 422


@pytest.mark.parametrize("role_user", ["student", "admin"])
def test_only_teacher_uploads(
    client: TestClient, login: Login, request: pytest.FixtureRequest, role_user: str
) -> None:
    login(request.getfixturevalue(role_user))
    response = client.post("/files", files={"file": ("a.png", PNG, "image/png")})
    assert response.status_code == 403


def test_logged_in_user_downloads_file_inline(
    client: TestClient, login: Login, teacher: User, student: User, upload: Upload
) -> None:
    login(teacher)
    file = upload("Procenty — wykres.png")

    login(student)
    response = client.get(file["url"])

    assert response.status_code == 200
    assert response.content == PNG
    assert response.headers["content-type"] == "image/png"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["content-disposition"].startswith("inline;")


def test_video_supports_range_requests(
    client: TestClient, login: Login, teacher: User, upload: Upload
) -> None:
    login(teacher)
    file = upload("film.mp4", b"0123456789")

    response = client.get(file["url"], headers={"Range": "bytes=2-5"})

    assert response.status_code == 206
    assert response.content == b"2345"


def test_download_requires_login(
    client: TestClient, login: Login, teacher: User, upload: Upload
) -> None:
    login(teacher)
    file = upload()
    client.post("/auth/logout")
    assert client.get(file["url"]).status_code == 401


def test_missing_file_is_not_found(
    client: TestClient, login: Login, teacher: User, upload: Upload, upload_dir: Path
) -> None:
    login(teacher)
    assert client.get("/files/999999").json()["code"] == "FILE_NOT_FOUND"

    file = upload()
    for stored in upload_dir.iterdir():
        stored.unlink()
    assert client.get(file["url"]).status_code == 404
