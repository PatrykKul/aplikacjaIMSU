"""Three versions (V / A / K) of a lesson: saving, reading, file checks, published lessons."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.modules.content import service
from app.modules.curriculum.models import Lesson
from app.modules.identity.models import ApprovalStatus, User
from tests.content.conftest import attachment, text_block

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]
Upload = Callable[..., dict[str, Any]]

YOUTUBE = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def lesson_id(make_course: MakeCourse, teacher: User) -> int:
    """A draft lesson; the teacher stays logged in."""
    return make_course(teacher, lessons=("A",))["lessons"][0]["id"]


def _put(client: TestClient, lesson_id: int, form: str, blocks: list[dict[str, Any]]):
    return client.put(f"/lessons/{lesson_id}/versions/{form}", json={"blocks": blocks})


# --- Saving and reading ------------------------------------------------------------------------


def test_new_lesson_has_three_empty_versions(client: TestClient, lesson_id: int) -> None:
    response = client.get(f"/lessons/{lesson_id}/versions")
    assert response.status_code == 200
    assert response.json() == {"V": {"blocks": []}, "A": {"blocks": []}, "K": {"blocks": []}}


def test_owner_saves_each_version_separately(
    client: TestClient, lesson_id: int, upload: Upload
) -> None:
    image = upload("wykres.png")
    visual = [text_block("t1", "Wykres"), attachment("image", "a1", file_id=image["id"])]
    audio = [attachment("audio", "a1", transcript="Posłuchaj"), text_block("t1", "Opis")]

    saved = _put(client, lesson_id, "V", visual)
    _put(client, lesson_id, "A", audio)

    assert saved.status_code == 200
    blocks = saved.json()["blocks"]
    assert blocks[1]["file_url"] == f"/files/{image['id']}"
    assert blocks[1]["file_name"] == "wykres.png"
    versions = client.get(f"/lessons/{lesson_id}/versions").json()
    assert [block["id"] for block in versions["V"]["blocks"]] == ["t1", "a1"]
    assert versions["A"]["blocks"][0]["transcript"] == "Posłuchaj"
    assert versions["K"]["blocks"] == []


def test_saving_replaces_the_version(client: TestClient, lesson_id: int) -> None:
    _put(client, lesson_id, "K", [text_block("t1"), text_block("t2")])
    _put(client, lesson_id, "K", [text_block("t3")])

    blocks = client.get(f"/lessons/{lesson_id}/versions").json()["K"]["blocks"]
    assert [block["id"] for block in blocks] == ["t3"]


def test_attachment_has_no_forms(client: TestClient, lesson_id: int) -> None:
    video = attachment("video", "v1", youtube_url=YOUTUBE, forms=["V", "A"])

    blocks = _put(client, lesson_id, "V", [video]).json()["blocks"]

    assert "forms" not in blocks[0]
    assert blocks[0]["youtube_id"] == "dQw4w9WgXcQ"
    stored = client.get(f"/lessons/{lesson_id}/versions").json()["V"]["blocks"][0]
    assert "forms" not in stored


def test_service_reads_one_version_and_issues(
    client: TestClient, db: Session, lesson_id: int
) -> None:
    _put(client, lesson_id, "A", [attachment("audio", "a1", transcript="Tekst")])

    assert [block["id"] for block in service.get_version(db, lesson_id, "A")] == ["a1"]
    assert service.get_version(db, lesson_id, "V") == []
    assert service.version_issues(db, lesson_id) == [
        {"area": "V", "code": "VERSION_EMPTY"},
        {"area": "A", "code": "A_DESCRIPTION_MISSING"},
        {"area": "K", "code": "VERSION_EMPTY"},
    ]


# --- Validation --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "blocks",
    [
        [text_block("t1"), text_block("t1")],  # duplicate ids
        [{"id": "x", "type": "quote"}],
        [attachment("video", "v1")],  # no source
        [attachment("audio", "a1", transcript="x", file_id=1)],  # two sources
        [attachment("link", "l1", url="http://example.com")],  # not https
        [{"id": "t1", "type": "text", "doc": {"type": "paragraph"}}],
    ],
)
def test_invalid_blocks_are_rejected(
    client: TestClient, lesson_id: int, blocks: list[dict[str, Any]]
) -> None:
    response = _put(client, lesson_id, "V", blocks)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_unknown_form_is_rejected(client: TestClient, lesson_id: int) -> None:
    assert _put(client, lesson_id, "X", []).status_code == 422


def test_file_must_belong_to_course_owner(
    client: TestClient, login: Login, lesson_id: int, other_teacher: User, teacher: User, upload
) -> None:
    login(other_teacher)
    foreign = upload("obcy.png")
    login(teacher)

    for file_id in (foreign["id"], 999999):
        response = _put(client, lesson_id, "V", [attachment("image", "a1", file_id=file_id)])
        assert response.status_code == 400
        assert response.json() == {"code": "FILE_NOT_FOUND"}


def test_file_must_match_attachment_kind(
    client: TestClient, lesson_id: int, upload: Upload
) -> None:
    pdf = upload("karta.pdf", b"%PDF-1.4")

    response = _put(client, lesson_id, "V", [attachment("image", "a1", file_id=pdf["id"])])

    assert response.status_code == 400
    assert response.json() == {"code": "FILE_KIND_MISMATCH"}


# --- Published lesson --------------------------------------------------------------------------


@pytest.fixture
def published_lesson(
    client: TestClient, db: Session, lesson_id: int, upload: Upload
) -> dict[str, Any]:
    """A published lesson with a complete K version: instruction and a worksheet."""
    pdf = upload("karta.pdf", b"%PDF-1.4")
    blocks = [text_block("t1", "Wykonaj zadanie"), attachment("pdf", "p1", file_id=pdf["id"])]
    _put(client, lesson_id, "K", blocks)
    db.execute(update(Lesson).where(Lesson.id == lesson_id).values(is_published=True))
    db.commit()
    return {"id": lesson_id, "K": blocks}


@pytest.mark.parametrize(
    ("change", "codes"),
    [
        (lambda blocks: [], ["VERSION_EMPTY"]),
        (lambda blocks: blocks[:1], ["K_WORKSHEET_MISSING"]),
        (lambda blocks: blocks[1:], ["K_INSTRUCTION_MISSING"]),
    ],
)
def test_published_lesson_version_cannot_become_incomplete(
    client: TestClient,
    published_lesson: dict[str, Any],
    change: Callable[[list[dict[str, Any]]], list[dict[str, Any]]],
    codes: list[str],
) -> None:
    lesson_id = published_lesson["id"]

    response = _put(client, lesson_id, "K", change(published_lesson["K"]))

    assert response.status_code == 409
    assert response.json() == {
        "code": "PUBLISHED_LESSON_INCOMPLETE",
        "issues": [{"area": "K", "code": code} for code in codes],
    }
    stored = client.get(f"/lessons/{lesson_id}/versions").json()["K"]["blocks"]
    assert [block["id"] for block in stored] == ["t1", "p1"]


def test_published_lesson_version_can_change_while_complete(
    client: TestClient, published_lesson: dict[str, Any]
) -> None:
    blocks = [*published_lesson["K"], text_block("t2", "Dodatkowa wskazówka")]
    assert _put(client, published_lesson["id"], "K", blocks).status_code == 200


# --- Permissions -------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("viewer", "read", "write"),
    [("admin", 200, 404), ("other_teacher", 404, 404), ("student", 404, 404)],
)
def test_versions_belong_to_the_author(
    client: TestClient,
    login: Login,
    request: pytest.FixtureRequest,
    make_course: MakeCourse,
    teacher: User,
    viewer: str,
    read: int,
    write: int,
) -> None:
    lesson_id = make_course(teacher, lessons=("A",), published=True)["lessons"][0]["id"]
    login(request.getfixturevalue(viewer))

    assert client.get(f"/lessons/{lesson_id}/versions").status_code == read
    response = _put(client, lesson_id, "V", [text_block()])
    assert response.status_code == write
    assert response.json()["code"] == "LESSON_NOT_FOUND"


def test_rejected_teacher_cannot_edit_versions(
    client: TestClient, db: Session, lesson_id: int, teacher: User
) -> None:
    teacher.approval_status = ApprovalStatus.REJECTED
    db.commit()

    for response in (
        client.get(f"/lessons/{lesson_id}/versions"),
        _put(client, lesson_id, "V", [text_block()]),
    ):
        assert response.status_code == 403
        assert response.json() == {"code": "TEACHER_NOT_APPROVED"}


def test_versions_require_login(client: TestClient, lesson_id: int) -> None:
    client.post("/auth/logout")
    assert client.get(f"/lessons/{lesson_id}/versions").status_code == 401
