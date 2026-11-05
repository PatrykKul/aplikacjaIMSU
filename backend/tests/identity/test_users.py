from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User, UserRole


def test_admin_lists_users(
    client: TestClient, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    admin = make_user(UserRole.ADMIN)
    student = make_user(UserRole.STUDENT)
    login(admin)

    response = client.get("/users")

    assert response.status_code == 200
    ids = [user["id"] for user in response.json()]
    assert ids == sorted(ids)
    assert {admin.id, student.id} <= set(ids)


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER])
def test_non_admin_cannot_list_users(
    client: TestClient,
    make_user: Callable[..., User],
    login: Callable[[User], None],
    role: UserRole,
) -> None:
    login(make_user(role))
    response = client.get("/users")
    assert response.status_code == 403
    assert response.json() == {"code": "FORBIDDEN"}


def test_anonymous_cannot_list_users(client: TestClient) -> None:
    assert client.get("/users").status_code == 401


def test_admin_changes_role_and_blocks_user(
    client: TestClient, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    login(make_user(UserRole.ADMIN))
    student = make_user(UserRole.STUDENT)

    response = client.patch(f"/users/{student.id}", json={"role": "teacher", "is_active": False})

    assert response.status_code == 200
    assert response.json()["role"] == "teacher"
    assert response.json()["is_active"] is False


def test_admin_cannot_modify_self(
    client: TestClient, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    admin = make_user(UserRole.ADMIN)
    login(admin)
    response = client.patch(f"/users/{admin.id}", json={"is_active": False})
    assert response.status_code == 400
    assert response.json() == {"code": "CANNOT_MODIFY_SELF"}


def test_update_unknown_user(
    client: TestClient, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    login(make_user(UserRole.ADMIN))
    response = client.patch("/users/999999", json={"is_active": False})
    assert response.status_code == 404
    assert response.json() == {"code": "USER_NOT_FOUND"}
