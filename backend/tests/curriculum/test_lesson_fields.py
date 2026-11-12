"""Outline and conclusions of a lesson; a published lesson must stay complete (R11)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.identity.models import ApprovalStatus, User
from tests.curriculum.conftest import CONCLUSIONS, EMPTY_DOC, OUTLINE

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]


@pytest.fixture
def lesson_id(make_course: MakeCourse, teacher: User) -> int:
    return make_course(teacher, lessons=("A",))["lessons"][0]["id"]


@pytest.fixture
def published_lesson(
    client: TestClient, make_course: MakeCourse, set_published: Callable[..., None], teacher: User
) -> int:
    """A complete published lesson (outline and conclusions written) of a draft course."""
    lesson_id = make_course(teacher, lessons=("A", "B"))["lessons"][0]["id"]
    client.patch(f"/lessons/{lesson_id}", json={"outline": OUTLINE, "conclusions": CONCLUSIONS})
    set_published(lesson_id)
    return lesson_id


def test_owner_writes_outline_and_conclusions(client: TestClient, lesson_id: int) -> None:
    response = client.patch(
        f"/lessons/{lesson_id}", json={"outline": OUTLINE, "conclusions": CONCLUSIONS}
    )

    assert response.status_code == 200
    lesson = response.json()
    assert (lesson["outline"], lesson["conclusions"]) == (OUTLINE, CONCLUSIONS)
    assert lesson["title"] == "A"
    assert client.get(f"/lessons/{lesson_id}").json()["outline"] == OUTLINE


def test_partial_update_keeps_other_fields(client: TestClient, lesson_id: int) -> None:
    client.patch(f"/lessons/{lesson_id}", json={"outline": OUTLINE, "conclusions": CONCLUSIONS})

    lesson = client.patch(f"/lessons/{lesson_id}", json={"title": "Nowy"}).json()

    assert (lesson["title"], lesson["outline"], lesson["conclusions"]) == (
        "Nowy",
        OUTLINE,
        CONCLUSIONS,
    )


def test_null_clears_a_draft_field(client: TestClient, lesson_id: int) -> None:
    client.patch(f"/lessons/{lesson_id}", json={"outline": OUTLINE, "conclusions": CONCLUSIONS})

    lesson = client.patch(f"/lessons/{lesson_id}", json={"outline": None}).json()

    assert (lesson["outline"], lesson["conclusions"]) == (None, CONCLUSIONS)


def test_outline_is_shown_in_course(client: TestClient, lesson_id: int) -> None:
    lesson = client.patch(f"/lessons/{lesson_id}", json={"outline": OUTLINE}).json()
    course = client.get(f"/courses/{lesson['course']['id']}").json()
    assert course["lessons"][0]["outline"] == OUTLINE


@pytest.mark.parametrize(
    "body",
    [
        {"outline": {"type": "paragraph"}},
        {"conclusions": "tekst"},
        {"title": ""},
        {"title": None},  # null clears only the outline and the conclusions (D61)
        {"title": None, "outline": None},
        {"is_published": True},  # publication goes through /publication (authoring)
    ],
)
def test_update_validates_fields(client: TestClient, lesson_id: int, body: dict) -> None:
    response = client.patch(f"/lessons/{lesson_id}", json=body)
    assert response.status_code == 422


@pytest.mark.parametrize(
    ("body", "issues"),
    [
        ({"outline": EMPTY_DOC}, [{"area": "lesson", "code": "OUTLINE_MISSING"}]),
        ({"conclusions": None}, [{"area": "lesson", "code": "CONCLUSIONS_MISSING"}]),
        (
            {"title": "Nowy", "outline": None, "conclusions": EMPTY_DOC},
            [
                {"area": "lesson", "code": "OUTLINE_MISSING"},
                {"area": "lesson", "code": "CONCLUSIONS_MISSING"},
            ],
        ),
    ],
)
def test_published_lesson_cannot_lose_outline_or_conclusions(
    client: TestClient, published_lesson: int, body: dict, issues: list[dict]
) -> None:
    response = client.patch(f"/lessons/{published_lesson}", json=body)

    assert response.status_code == 409
    assert response.json() == {"code": "PUBLISHED_LESSON_INCOMPLETE", "issues": issues}
    lesson = client.get(f"/lessons/{published_lesson}").json()
    assert (lesson["title"], lesson["outline"], lesson["conclusions"]) == (
        "A",
        OUTLINE,
        CONCLUSIONS,
    )


def test_published_lesson_can_be_edited_while_complete(
    client: TestClient, published_lesson: int
) -> None:
    new_outline = {**OUTLINE, "content": [*OUTLINE["content"], {"type": "paragraph"}]}

    response = client.patch(
        f"/lessons/{published_lesson}", json={"title": "Nowy", "outline": new_outline}
    )

    assert response.status_code == 200
    assert response.json()["outline"] == new_outline


# --- Archiving the last published lesson -------------------------------------------------------


def test_last_published_lesson_of_published_course_cannot_be_archived(
    client: TestClient, make_course: MakeCourse, set_published: Callable[..., None], teacher: User
) -> None:
    course = make_course(teacher, lessons=("A", "B"), published=True)
    first, second = (lesson["id"] for lesson in course["lessons"])
    assert client.delete(f"/lessons/{first}").status_code == 204

    response = client.delete(f"/lessons/{second}")

    assert response.status_code == 409
    assert response.json() == {"code": "LAST_PUBLISHED_LESSON"}
    client.patch(f"/courses/{course['id']}", json={"is_published": False})
    assert client.delete(f"/lessons/{second}").status_code == 204


# --- Teacher approval --------------------------------------------------------------------------


def test_rejected_teacher_loses_access_to_own_course(
    client: TestClient, db: Session, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher, lessons=("A",))
    lesson_id = course["lessons"][0]["id"]
    teacher.approval_status = ApprovalStatus.REJECTED
    db.commit()

    responses = [
        client.get("/courses"),
        client.get(f"/courses/{course['id']}"),
        client.patch(f"/courses/{course['id']}", json={"title": "X"}),
        client.delete(f"/courses/{course['id']}"),
        client.post(f"/courses/{course['id']}/lessons", json={"title": "X"}),
        client.get(f"/courses/{course['id']}/enrollments"),
        client.get(f"/lessons/{lesson_id}"),
        client.patch(f"/lessons/{lesson_id}", json={"title": "X"}),
        client.delete(f"/lessons/{lesson_id}"),
    ]

    for response in responses:
        assert response.status_code == 403
        assert response.json() == {"code": "TEACHER_NOT_APPROVED"}
