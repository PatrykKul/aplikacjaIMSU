"""The admin moves a course to another approved teacher (D56)."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.curriculum import service
from app.modules.curriculum.models import CourseOwnerChange
from app.modules.identity.models import ApprovalStatus, User, UserRole

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]


def _changes(db: Session, course_id: int) -> list[CourseOwnerChange]:
    query = select(CourseOwnerChange).where(CourseOwnerChange.course_id == course_id)
    return list(db.scalars(query.order_by(CourseOwnerChange.id)))


def _put_owner(client: TestClient, course_id: int, owner_id: Any):
    return client.put(f"/courses/{course_id}/owner", json={"owner_id": owner_id})


def test_admin_moves_course_to_another_teacher(
    client: TestClient,
    db: Session,
    login: Login,
    make_course: MakeCourse,
    enroll: Callable[..., None],
    teacher: User,
    other_teacher: User,
    student: User,
    admin: User,
) -> None:
    course = make_course(teacher, lessons=("L1", "L2"), published=True)
    enroll(student, course["id"])
    login(admin)

    response = _put_owner(client, course["id"], other_teacher.id)

    assert response.status_code == 200
    body = response.json()
    assert body["owner"] == {"id": other_teacher.id, "display_name": other_teacher.display_name}
    assert [lesson["is_published"] for lesson in body["lessons"]] == [True, True]  # admin view
    [change] = _changes(db, course["id"])
    assert (change.from_owner_id, change.to_owner_id, change.changed_by_id) == (
        teacher.id,
        other_teacher.id,
        admin.id,
    )
    assert change.changed_at is not None

    # The new author manages the course at once, the previous one no longer sees it
    login(other_teacher)
    assert [c["id"] for c in client.get("/courses").json()] == [course["id"]]
    assert client.get(f"/courses/{course['id']}/enrollments").status_code == 200
    login(teacher)
    assert client.get("/courses").json() == []
    assert client.get(f"/courses/{course['id']}").status_code == 404

    # The student keeps the enrollment and sees the new author in the catalog
    login(student)
    listed = client.get("/courses").json()[0]
    assert listed["owner"]["id"] == other_teacher.id
    assert listed["enrollment_status"] == "accepted"
    assert client.get(f"/courses/{course['id']}").json()["lessons"][0]["state"] == "available"


def test_same_owner_changes_nothing(
    client: TestClient,
    db: Session,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    admin: User,
) -> None:
    course = make_course(teacher)
    login(admin)

    response = _put_owner(client, course["id"], teacher.id)

    assert response.status_code == 200
    assert response.json()["owner"]["id"] == teacher.id
    assert _changes(db, course["id"]) == []


def test_each_change_is_logged(
    client: TestClient,
    db: Session,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    other_teacher: User,
    admin: User,
) -> None:
    course = make_course(teacher)
    client.delete(f"/courses/{course['id']}")  # an archived course can be moved too
    login(admin)

    _put_owner(client, course["id"], other_teacher.id)
    _put_owner(client, course["id"], teacher.id)

    pairs = [(c.from_owner_id, c.to_owner_id) for c in _changes(db, course["id"])]
    assert pairs == [(teacher.id, other_teacher.id), (other_teacher.id, teacher.id)]


@pytest.mark.parametrize("role_user", ["teacher", "other_teacher", "student"])
def test_only_admin_changes_owner(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    request: pytest.FixtureRequest,
    teacher: User,
    other_teacher: User,
    role_user: str,
) -> None:
    course = make_course(teacher, lessons=("L1",), published=True)
    login(request.getfixturevalue(role_user))

    response = _put_owner(client, course["id"], other_teacher.id)

    assert response.status_code == 403
    assert response.json() == {"code": "FORBIDDEN"}


def test_owner_change_requires_login(
    client: TestClient, make_course: MakeCourse, teacher: User, other_teacher: User
) -> None:
    course = make_course(teacher)
    client.post("/auth/logout")
    assert _put_owner(client, course["id"], other_teacher.id).status_code == 401


def test_missing_course(client: TestClient, login: Login, admin: User, teacher: User) -> None:
    login(admin)
    response = _put_owner(client, 999999, teacher.id)
    assert response.status_code == 404
    assert response.json() == {"code": "COURSE_NOT_FOUND"}


@pytest.mark.parametrize("target", ["student", "admin", "missing"])
def test_new_owner_must_be_a_teacher(
    client: TestClient,
    db: Session,
    login: Login,
    make_course: MakeCourse,
    request: pytest.FixtureRequest,
    teacher: User,
    admin: User,
    target: str,
) -> None:
    course = make_course(teacher)
    owner_id = 999999 if target == "missing" else request.getfixturevalue(target).id
    login(admin)

    response = _put_owner(client, course["id"], owner_id)

    assert response.status_code == 404
    assert response.json() == {"code": "USER_NOT_FOUND"}
    assert _changes(db, course["id"]) == []


@pytest.mark.parametrize("approval", [ApprovalStatus.PENDING, ApprovalStatus.REJECTED])
def test_new_owner_must_be_approved(
    client: TestClient,
    db: Session,
    login: Login,
    make_course: MakeCourse,
    make_user: Callable[..., User],
    teacher: User,
    admin: User,
    approval: ApprovalStatus,
) -> None:
    course = make_course(teacher)
    waiting = make_user(UserRole.TEACHER)
    waiting.approval_status = approval
    db.commit()
    login(admin)

    response = _put_owner(client, course["id"], waiting.id)

    assert response.status_code == 409
    assert response.json() == {"code": "TEACHER_NOT_APPROVED"}
    assert client.get(f"/courses/{course['id']}").json()["owner"]["id"] == teacher.id


@pytest.mark.parametrize("body", [{}, {"owner_id": "x"}, {"owner_id": None}])
def test_owner_change_validates_body(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    admin: User,
    body: dict[str, Any],
) -> None:
    course = make_course(teacher)
    login(admin)
    response = client.put(f"/courses/{course['id']}/owner", json=body)
    assert response.status_code == 422


def test_service_checks_the_admin_role(
    db: Session, make_course: MakeCourse, teacher: User, other_teacher: User
) -> None:
    course = make_course(teacher)
    with pytest.raises(AppError) as error:
        service.change_owner(db, course["id"], teacher, other_teacher.id)
    assert error.value.code == "FORBIDDEN"
