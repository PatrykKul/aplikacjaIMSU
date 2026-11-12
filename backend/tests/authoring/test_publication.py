"""Readiness (R11) and publication of a lesson."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.identity.models import ApprovalStatus, User
from tests.authoring.conftest import save_quiz

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]
Complete = Callable[[int], None]

ALL_ISSUES = [
    {"area": "lesson", "code": "OUTLINE_MISSING"},
    {"area": "lesson", "code": "CONCLUSIONS_MISSING"},
    {"area": "V", "code": "VERSION_EMPTY"},
    {"area": "A", "code": "VERSION_EMPTY"},
    {"area": "K", "code": "VERSION_EMPTY"},
    {"area": "quiz", "code": "QUIZ_TOO_FEW_QUESTIONS", "count": 0, "min": 5},
]


@pytest.fixture
def course(make_course: MakeCourse, teacher: User) -> dict[str, Any]:
    """A draft course with two draft lessons; the teacher stays logged in."""
    return make_course(teacher, lessons=("A", "B"))


def _lesson_ids(course: dict[str, Any]) -> list[int]:
    return [lesson["id"] for lesson in course["lessons"]]


def _publish(client: TestClient, lesson_id: int, published: bool = True):
    return client.put(f"/lessons/{lesson_id}/publication", json={"is_published": published})


# --- Readiness ---------------------------------------------------------------------------------


def test_new_lesson_lists_every_missing_part(client: TestClient, course: dict[str, Any]) -> None:
    response = client.get(f"/lessons/{_lesson_ids(course)[0]}/readiness")

    assert response.status_code == 200
    assert response.json() == {"ready": False, "issues": ALL_ISSUES}


def test_complete_lesson_is_ready(
    client: TestClient, course: dict[str, Any], complete_lesson: Complete
) -> None:
    lesson_id = _lesson_ids(course)[0]
    complete_lesson(lesson_id)

    response = client.get(f"/lessons/{lesson_id}/readiness")

    assert response.json() == {"ready": True, "issues": []}


def test_small_quiz_pool_is_reported_with_numbers(
    client: TestClient, course: dict[str, Any], complete_lesson: Complete
) -> None:
    lesson_id = _lesson_ids(course)[0]
    complete_lesson(lesson_id)
    save_quiz(client, lesson_id, 3)

    response = client.get(f"/lessons/{lesson_id}/readiness")

    assert response.json() == {
        "ready": False,
        "issues": [{"area": "quiz", "code": "QUIZ_TOO_FEW_QUESTIONS", "count": 3, "min": 5}],
    }


# --- Publishing --------------------------------------------------------------------------------


def test_incomplete_lesson_cannot_be_published(client: TestClient, course: dict[str, Any]) -> None:
    lesson_id = _lesson_ids(course)[0]

    response = _publish(client, lesson_id)

    assert response.status_code == 409
    assert response.json() == {"code": "LESSON_NOT_READY", "issues": ALL_ISSUES}
    assert client.get(f"/lessons/{lesson_id}").json()["is_published"] is False


def test_ready_lesson_is_published_and_course_can_follow(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    complete_lesson: Complete,
    student: User,
    enroll: Callable[..., None],
) -> None:
    first, second = _lesson_ids(course)
    complete_lesson(second)
    assert client.patch(f"/courses/{course['id']}", json={"is_published": True}).status_code == 409

    response = _publish(client, second)

    assert response.status_code == 200
    lesson = response.json()
    assert lesson["id"] == second
    assert lesson["is_published"] is True
    assert lesson["number"] == 2  # the author numbers every lesson
    assert _publish(client, second).json() == lesson  # repeated: no change
    assert client.patch(f"/courses/{course['id']}", json={"is_published": True}).status_code == 200

    enroll(student, course["id"])
    login(student)
    detail = client.get(f"/courses/{course['id']}").json()
    assert [(item["id"], item["number"], item["state"]) for item in detail["lessons"]] == [
        (second, 1, "available")
    ]
    assert client.get(f"/lessons/{first}").status_code == 404


def test_published_lesson_stays_complete(
    client: TestClient, course: dict[str, Any], complete_lesson: Complete
) -> None:
    lesson_id = _lesson_ids(course)[0]
    complete_lesson(lesson_id)
    _publish(client, lesson_id)

    outline = client.patch(f"/lessons/{lesson_id}", json={"outline": None})
    version = client.put(f"/lessons/{lesson_id}/versions/V", json={"blocks": []})

    assert outline.status_code == 409
    assert outline.json()["issues"] == [{"area": "lesson", "code": "OUTLINE_MISSING"}]
    assert version.status_code == 409
    assert version.json()["issues"] == [{"area": "V", "code": "VERSION_EMPTY"}]
    assert client.get(f"/lessons/{lesson_id}/readiness").json()["ready"] is True


# --- Withdrawing -------------------------------------------------------------------------------


def test_lesson_of_draft_course_is_withdrawn(
    client: TestClient, course: dict[str, Any], complete_lesson: Complete
) -> None:
    lesson_id = _lesson_ids(course)[0]
    complete_lesson(lesson_id)
    _publish(client, lesson_id)

    response = _publish(client, lesson_id, False)

    assert response.status_code == 200
    assert response.json()["is_published"] is False
    assert _publish(client, lesson_id, False).status_code == 200  # repeated: no change


def test_last_published_lesson_of_published_course_stays(
    client: TestClient, course: dict[str, Any], complete_lesson: Complete
) -> None:
    first, second = _lesson_ids(course)
    for lesson_id in (first, second):
        complete_lesson(lesson_id)
        _publish(client, lesson_id)
    client.patch(f"/courses/{course['id']}", json={"is_published": True})

    assert _publish(client, first, False).status_code == 200
    response = _publish(client, second, False)

    assert response.status_code == 409
    assert response.json() == {"code": "LAST_PUBLISHED_LESSON"}
    assert client.get(f"/lessons/{second}").json()["is_published"] is True


# --- Permissions -------------------------------------------------------------------------------


@pytest.mark.parametrize("viewer", ["other_teacher", "student", "admin"])
def test_only_author_checks_and_publishes(
    client: TestClient,
    login: Login,
    request: pytest.FixtureRequest,
    course: dict[str, Any],
    viewer: str,
) -> None:
    lesson_id = _lesson_ids(course)[0]
    login(request.getfixturevalue(viewer))

    for response in (client.get(f"/lessons/{lesson_id}/readiness"), _publish(client, lesson_id)):
        assert response.status_code == 404
        assert response.json() == {"code": "LESSON_NOT_FOUND"}


def test_teacher_not_approved_cannot_publish(
    client: TestClient, db: Session, course: dict[str, Any], teacher: User
) -> None:
    lesson_id = _lesson_ids(course)[0]
    teacher.approval_status = ApprovalStatus.PENDING
    db.commit()

    for response in (client.get(f"/lessons/{lesson_id}/readiness"), _publish(client, lesson_id)):
        assert response.status_code == 403
        assert response.json() == {"code": "TEACHER_NOT_APPROVED"}


def test_missing_lesson_and_login(client: TestClient, course: dict[str, Any]) -> None:
    assert client.get("/lessons/999999/readiness").status_code == 404
    assert _publish(client, 999999).status_code == 404
    client.post("/auth/logout")
    assert client.get(f"/lessons/{_lesson_ids(course)[0]}/readiness").status_code == 401


@pytest.mark.parametrize("body", [{}, {"is_published": "tak"}, {"is_published": True, "x": 1}])
def test_publication_body_is_validated(
    client: TestClient, course: dict[str, Any], body: dict
) -> None:
    response = client.put(f"/lessons/{_lesson_ids(course)[0]}/publication", json=body)
    assert response.status_code == 422
