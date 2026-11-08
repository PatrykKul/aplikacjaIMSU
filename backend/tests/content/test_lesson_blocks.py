from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User
from tests.content.conftest import attachment, text_block

MakeCourse = Callable[..., dict[str, Any]]
Upload = Callable[..., dict[str, Any]]
Login = Callable[[User], None]

YOUTUBE = "https://youtu.be/dQw4w9WgXcQ"


@pytest.fixture
def lesson_id(make_course: MakeCourse, teacher: User) -> int:
    """A lesson of the teacher's published course; the teacher stays logged in."""
    course = make_course(teacher, lessons=("Procent z liczby",), published=True)
    return course["lessons"][0]["id"]


def _put(client: TestClient, lesson_id: int, blocks: list[dict[str, Any]]) -> Any:
    return client.put(f"/lessons/{lesson_id}/blocks", json={"blocks": blocks})


# --- Saving and reading ------------------------------------------------------------------------


def test_new_lesson_has_no_blocks(client: TestClient, lesson_id: int) -> None:
    response = client.get(f"/lessons/{lesson_id}/blocks")
    assert response.status_code == 200
    assert response.json() == {"blocks": []}


def test_owner_saves_whole_lesson_in_order(
    client: TestClient, lesson_id: int, upload: Upload
) -> None:
    image = upload("wykres.png")
    recording = upload("nagranie.mp3")
    blocks = [
        text_block("t1"),
        attachment("image", "a1", file_id=image["id"], alt="Wykres", forms=["V"]),
        attachment("video", "a2", youtube_url=YOUTUBE, forms=["V", "A"]),
        attachment("audio", "a3", file_id=recording["id"], forms=["A"]),
        attachment("audio", "a4", transcript="Procent to setna część.", forms=["A"]),
        attachment("pdf", "a5", file_id=upload("karta.pdf")["id"], forms=["K"]),
        attachment("link", "a6", url="https://pl.khanacademy.org", forms=["K", "V"]),
        text_block("t2", "Podsumowanie"),
    ]

    response = _put(client, lesson_id, blocks)

    assert response.status_code == 200
    saved = client.get(f"/lessons/{lesson_id}/blocks").json()["blocks"]
    assert saved == response.json()["blocks"]
    assert [block["id"] for block in saved] == ["t1", "a1", "a2", "a3", "a4", "a5", "a6", "t2"]
    assert saved[1]["file_url"] == image["url"]
    assert saved[1]["file_name"] == "wykres.png"
    assert saved[2]["youtube_id"] == "dQw4w9WgXcQ"
    assert saved[3]["file_url"] == recording["url"]
    assert "file_url" not in saved[4]
    assert saved[6]["forms"] == ["K", "V"]


def test_saving_replaces_previous_content(client: TestClient, lesson_id: int) -> None:
    _put(client, lesson_id, [text_block("t1"), text_block("t2")])

    _put(client, lesson_id, [text_block("t2", "Nowy")])

    blocks = client.get(f"/lessons/{lesson_id}/blocks").json()["blocks"]
    assert [block["id"] for block in blocks] == ["t2"]
    assert _put(client, lesson_id, []).json() == {"blocks": []}


def test_blocks_sent_back_with_display_fields_are_accepted(
    client: TestClient, lesson_id: int, upload: Upload
) -> None:
    image = upload()
    first = _put(client, lesson_id, [attachment("image", file_id=image["id"])]).json()["blocks"]

    second = _put(client, lesson_id, first)

    assert second.status_code == 200
    assert second.json()["blocks"] == first


def test_student_reads_blocks_of_published_lesson(
    client: TestClient, login: Login, lesson_id: int, student: User
) -> None:
    _put(client, lesson_id, [text_block()])

    login(student)

    assert client.get(f"/lessons/{lesson_id}/blocks").json()["blocks"][0]["id"] == "t1"
    assert _put(client, lesson_id, []).status_code == 404


@pytest.mark.parametrize("viewer", ["other_teacher", "student"])
def test_blocks_of_private_lesson_are_hidden(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    request: pytest.FixtureRequest,
    viewer: str,
) -> None:
    course = make_course(teacher, lessons=("A",))
    lesson = course["lessons"][0]["id"]

    login(request.getfixturevalue(viewer))

    response = client.get(f"/lessons/{lesson}/blocks")
    assert response.status_code == 404
    assert response.json()["code"] == "LESSON_NOT_FOUND"


@pytest.mark.parametrize("editor", ["other_teacher", "admin"])
def test_only_owner_saves_blocks(
    client: TestClient,
    login: Login,
    lesson_id: int,
    request: pytest.FixtureRequest,
    editor: str,
) -> None:
    login(request.getfixturevalue(editor))
    assert _put(client, lesson_id, [text_block()]).status_code == 404


def test_archived_lesson_has_no_blocks(client: TestClient, lesson_id: int) -> None:
    client.delete(f"/lessons/{lesson_id}")
    assert client.get(f"/lessons/{lesson_id}/blocks").status_code == 404
    assert _put(client, lesson_id, []).status_code == 404


# --- Validation --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "block",
    [
        attachment("link", forms=[], url="https://a.pl"),
        attachment("link", forms=["V", "V"], url="https://a.pl"),
        attachment("link", forms=["X"], url="https://a.pl"),
        attachment("link", title="  ", url="https://a.pl"),
        attachment("link", url="http://a.pl"),
        attachment("link", url="javascript:alert(1)"),
        attachment("video"),
        attachment("video", file_id=1, youtube_url=YOUTUBE),
        attachment("video", youtube_url="https://vimeo.com/1"),
        attachment("audio"),
        attachment("audio", file_id=1, transcript="Tekst"),
        attachment("audio", transcript="   "),
        attachment("diagram", percent=30),
        {"id": "x", "type": "quiz"},
        {"id": "t1", "type": "text", "doc": {"type": "paragraph"}},
        {"id": "z ł", "type": "text", "doc": {"type": "doc", "content": []}},
    ],
)
def test_invalid_block_is_rejected(
    client: TestClient, lesson_id: int, block: dict[str, Any]
) -> None:
    response = _put(client, lesson_id, [block])
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_block_ids_must_be_unique(client: TestClient, lesson_id: int) -> None:
    response = _put(client, lesson_id, [text_block("x"), text_block("x")])
    assert response.status_code == 422


def test_file_of_another_teacher_is_not_found(
    client: TestClient,
    login: Login,
    lesson_id: int,
    teacher: User,
    other_teacher: User,
    upload: Upload,
) -> None:
    login(other_teacher)
    foreign = upload()

    login(teacher)
    response = _put(client, lesson_id, [attachment("image", file_id=foreign["id"])])

    assert response.status_code == 400
    assert response.json()["code"] == "FILE_NOT_FOUND"


def test_missing_file_is_not_found(client: TestClient, lesson_id: int) -> None:
    response = _put(client, lesson_id, [attachment("pdf", file_id=999999)])
    assert response.json()["code"] == "FILE_NOT_FOUND"


@pytest.mark.parametrize(
    ("kind", "file_name"),
    [
        ("image", "karta.pdf"),
        ("pdf", "obraz.png"),
        ("video", "nagranie.mp3"),
        ("audio", "film.mp4"),
    ],
)
def test_file_must_match_attachment_kind(
    client: TestClient, lesson_id: int, upload: Upload, kind: str, file_name: str
) -> None:
    file = upload(file_name)

    response = _put(client, lesson_id, [attachment(kind, file_id=file["id"])])

    assert response.status_code == 400
    assert response.json()["code"] == "FILE_KIND_MISMATCH"
    assert client.get(f"/lessons/{lesson_id}/blocks").json() == {"blocks": []}
