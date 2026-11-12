from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User, UserRole

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]
Enroll = Callable[..., None]


@pytest.fixture
def course(make_course: MakeCourse, teacher: User) -> dict[str, Any]:
    return make_course(teacher, lessons=("A", "B"), published=True)


def _request(client: TestClient, course_id: int):
    return client.post(f"/courses/{course_id}/enrollment")


def _statuses(client: TestClient, course_id: int, query: str = "") -> list[tuple[int, str]]:
    response = client.get(f"/courses/{course_id}/enrollments{query}")
    assert response.status_code == 200
    return [(item["student"]["id"], item["status"]) for item in response.json()]


# --- Student asks to join ----------------------------------------------------------------------


def test_student_asks_to_join(
    client: TestClient, login: Login, course: dict[str, Any], student: User
) -> None:
    login(student)

    response = _request(client, course["id"])

    assert response.status_code == 201
    body = response.json()
    assert body["course_id"] == course["id"]
    assert body["status"] == "pending"
    assert body["requested_at"]
    assert body["decided_at"] is None
    listed = client.get(f"/courses/{course['id']}").json()
    assert listed["enrollment_status"] == "pending"
    assert listed["progress"] is None


def test_repeated_request_changes_nothing(
    client: TestClient, login: Login, course: dict[str, Any], student: User
) -> None:
    login(student)
    first = _request(client, course["id"]).json()

    again = _request(client, course["id"])

    assert again.status_code == 200
    assert again.json() == first


def test_rejected_student_asks_again(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    teacher: User,
    student: User,
) -> None:
    login(student)
    _request(client, course["id"])
    login(teacher)
    rejected = client.post(f"/courses/{course['id']}/enrollments/{student.id}/reject").json()
    assert rejected["status"] == "rejected"
    assert rejected["decided_at"] is not None

    login(student)
    assert client.get(f"/courses/{course['id']}").json()["enrollment_status"] == "rejected"
    response = _request(client, course["id"])

    assert response.status_code == 201
    assert response.json()["status"] == "pending"
    assert response.json()["decided_at"] is None


def test_accepted_student_cannot_ask_again(
    client: TestClient, login: Login, course: dict[str, Any], student: User, enroll: Enroll
) -> None:
    enroll(student, course["id"])
    login(student)

    response = _request(client, course["id"])

    assert response.status_code == 409
    assert response.json() == {"code": "ALREADY_ENROLLED"}


def test_private_archived_or_missing_course_is_not_found(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    student: User,
) -> None:
    private = make_course(teacher, lessons=("A",))
    archived = make_course(teacher, lessons=("A",), published=True)
    client.delete(f"/courses/{archived['id']}")
    login(student)

    for course_id in (private["id"], archived["id"], 999999):
        response = _request(client, course_id)
        assert response.status_code == 404
        assert response.json() == {"code": "COURSE_NOT_FOUND"}


@pytest.mark.parametrize("role", ["teacher", "admin"])
def test_only_students_ask_to_join(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    request: pytest.FixtureRequest,
    role: str,
) -> None:
    login(request.getfixturevalue(role))
    response = _request(client, course["id"])
    assert response.status_code == 403
    assert response.json() == {"code": "FORBIDDEN"}


def test_anonymous_cannot_ask(client: TestClient, course: dict[str, Any]) -> None:
    client.post("/auth/logout")
    assert _request(client, course["id"]).status_code == 401


# --- Author reviews requests -------------------------------------------------------------------


def test_author_lists_requests_oldest_first(
    client: TestClient,
    login: Login,
    make_user: Callable[..., User],
    course: dict[str, Any],
    teacher: User,
) -> None:
    first = make_user(UserRole.STUDENT, email="pierwszy@test.pl")
    second = make_user(UserRole.STUDENT, email="drugi@test.pl")
    for student in (first, second):
        login(student)
        _request(client, course["id"])

    login(teacher)
    response = client.get(f"/courses/{course['id']}/enrollments")

    assert response.status_code == 200
    items = response.json()
    assert [item["student"]["id"] for item in items] == [first.id, second.id]
    assert items[0]["student"] == {
        "id": first.id,
        "display_name": first.display_name,
        "email": "pierwszy@test.pl",
    }
    assert items[0]["status"] == "pending"
    assert items[0]["requested_at"]
    assert items[0]["decided_at"] is None


def test_author_filters_requests_by_status(
    client: TestClient,
    login: Login,
    make_user: Callable[..., User],
    course: dict[str, Any],
    teacher: User,
    enroll: Enroll,
) -> None:
    pending = make_user(UserRole.STUDENT)
    accepted = make_user(UserRole.STUDENT)
    rejected = make_user(UserRole.STUDENT)
    enroll(pending, course["id"], "pending")
    enroll(accepted, course["id"], "accepted")
    enroll(rejected, course["id"], "rejected")
    login(teacher)

    assert _statuses(client, course["id"], "?status=pending") == [(pending.id, "pending")]
    assert _statuses(client, course["id"], "?status=accepted") == [(accepted.id, "accepted")]
    assert len(_statuses(client, course["id"])) == 3
    assert client.get(f"/courses/{course['id']}/enrollments?status=x").status_code == 422
    assert client.get("/courses").json()[0]["pending_requests"] == 1
    assert client.get(f"/courses/{course['id']}").json()["pending_requests"] == 1


def test_author_accepts_request(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    teacher: User,
    student: User,
) -> None:
    login(student)
    _request(client, course["id"])
    login(teacher)

    url = f"/courses/{course['id']}/enrollments/{student.id}/accept"
    accepted = client.post(url)

    assert accepted.status_code == 200
    body = accepted.json()
    assert body["status"] == "accepted"
    assert body["decided_at"] is not None
    assert client.post(url).json() == body  # repeated decision: no change
    assert _statuses(client, course["id"]) == [(student.id, "accepted")]

    login(student)
    detail = client.get(f"/courses/{course['id']}").json()
    assert detail["enrollment_status"] == "accepted"
    assert detail["progress"] == {"passed": 0, "total": 2}
    assert client.get(f"/lessons/{course['lessons'][0]['id']}").status_code == 200


def test_author_changes_decision(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    teacher: User,
    student: User,
    enroll: Enroll,
) -> None:
    enroll(student, course["id"])
    login(teacher)

    response = client.post(f"/courses/{course['id']}/enrollments/{student.id}/reject")

    assert response.json()["status"] == "rejected"
    login(student)
    assert client.get(f"/lessons/{course['lessons'][0]['id']}").status_code == 403


@pytest.mark.parametrize("action", ["accept", "reject"])
def test_decision_needs_a_request(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    teacher: User,
    student: User,
    action: str,
) -> None:
    login(teacher)
    for student_id in (student.id, 999999):
        response = client.post(f"/courses/{course['id']}/enrollments/{student_id}/{action}")
        assert response.status_code == 404
        assert response.json() == {"code": "ENROLLMENT_NOT_FOUND"}


@pytest.mark.parametrize("viewer", ["other_teacher", "student", "admin"])
def test_only_author_reviews_requests(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    request: pytest.FixtureRequest,
    student: User,
    enroll: Enroll,
    viewer: str,
) -> None:
    enroll(student, course["id"], "pending")
    login(request.getfixturevalue(viewer))
    base = f"/courses/{course['id']}/enrollments"

    for response in (
        client.get(base),
        client.post(f"{base}/{student.id}/accept"),
        client.post(f"{base}/{student.id}/reject"),
    ):
        assert response.status_code == 404
        assert response.json() == {"code": "COURSE_NOT_FOUND"}


def test_requests_of_archived_course_are_hidden(
    client: TestClient, course: dict[str, Any], student: User, enroll: Enroll
) -> None:
    enroll(student, course["id"], "pending")
    client.delete(f"/courses/{course['id']}")
    assert client.get(f"/courses/{course['id']}/enrollments").status_code == 404


# --- Access of an accepted student -------------------------------------------------------------


def test_accepted_student_keeps_access_after_unpublishing(
    client: TestClient,
    login: Login,
    make_user: Callable[..., User],
    course: dict[str, Any],
    teacher: User,
    student: User,
    enroll: Enroll,
) -> None:
    enroll(student, course["id"])
    outsider = make_user(UserRole.STUDENT)
    login(teacher)
    client.patch(f"/courses/{course['id']}", json={"is_published": False})

    login(student)
    assert client.get(f"/courses/{course['id']}").status_code == 200
    assert [c["id"] for c in client.get("/courses").json()] == [course["id"]]
    login(outsider)
    assert client.get(f"/courses/{course['id']}").status_code == 404
    assert _request(client, course["id"]).status_code == 404
