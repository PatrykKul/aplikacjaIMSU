from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User, UserRole
from tests.conftest import PASSWORD

NEW_ACCOUNT = {
    "email": " Nowy@Test.pl ",
    "password": "NoweHaslo12",
    "display_name": "Nowy",
    "role": "teacher",
}


@pytest.fixture
def admin(make_user: Callable[..., User], login: Callable[[User], None]) -> User:
    user = make_user(UserRole.ADMIN)
    login(user)
    return user


def _can_login(client: TestClient, email: str, password: str) -> bool:
    response = client.post("/auth/login", json={"email": email, "password": password})
    return response.status_code == 200


# --- GET /users ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER])
def test_admin_lists_users_of_one_role_sorted_by_email(
    client: TestClient, make_user: Callable[..., User], admin: User, role: UserRole
) -> None:
    other = UserRole.TEACHER if role == UserRole.STUDENT else UserRole.STUDENT
    second = make_user(role, email="b-lista@test.pl")
    first = make_user(role, email="a-lista@test.pl")
    make_user(other, email="c-lista@test.pl")

    response = client.get(f"/users?role={role}")

    assert response.status_code == 200
    users = response.json()
    assert {user["role"] for user in users} == {role}
    emails = [user["email"] for user in users]
    assert emails == sorted(emails)
    assert {first.email, second.email} <= set(emails)


@pytest.mark.parametrize("query", ["", "?role=admin", "?role=nobody"])
def test_list_requires_student_or_teacher_role(client: TestClient, admin: User, query: str) -> None:
    response = client.get(f"/users{query}")
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER])
def test_non_admin_cannot_list_users(
    client: TestClient,
    make_user: Callable[..., User],
    login: Callable[[User], None],
    role: UserRole,
) -> None:
    login(make_user(role))
    response = client.get("/users?role=student")
    assert response.status_code == 403
    assert response.json() == {"code": "FORBIDDEN"}


def test_anonymous_cannot_list_users(client: TestClient) -> None:
    assert client.get("/users?role=student").status_code == 401


# --- POST /users --------------------------------------------------------------------------


@pytest.mark.parametrize("role", ["student", "teacher"])
def test_admin_creates_account(client: TestClient, admin: User, role: str) -> None:
    response = client.post("/users", json={**NEW_ACCOUNT, "role": role})

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nowy@test.pl"
    assert body["role"] == role
    assert body["is_active"] is True
    assert "password_hash" not in body
    assert "set-cookie" not in response.headers
    assert client.get("/auth/me").json()["id"] == admin.id
    assert _can_login(client, "nowy@test.pl", NEW_ACCOUNT["password"])


def test_admin_cannot_create_admin(client: TestClient, admin: User) -> None:
    response = client.post("/users", json={**NEW_ACCOUNT, "role": "admin"})
    assert response.status_code == 422


def test_create_rejects_taken_email(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    make_user(email="nowy@test.pl")
    response = client.post("/users", json=NEW_ACCOUNT)
    assert response.status_code == 409
    assert response.json() == {"code": "EMAIL_TAKEN"}


@pytest.mark.parametrize(
    "change",
    [{"email": "zly-adres"}, {"password": "krotkie"}, {"display_name": "   "}],
)
def test_create_validates_fields(client: TestClient, admin: User, change: dict) -> None:
    response = client.post("/users", json={**NEW_ACCOUNT, **change})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_non_admin_cannot_create_account(
    client: TestClient, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    login(make_user(UserRole.TEACHER))
    assert client.post("/users", json=NEW_ACCOUNT).status_code == 403


# --- PATCH /users/{id} --------------------------------------------------------------------


def test_admin_edits_name_and_email(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    student = make_user(UserRole.STUDENT)

    response = client.patch(
        f"/users/{student.id}", json={"display_name": " Ola ", "email": " OLA@test.pl "}
    )

    assert response.status_code == 200
    assert response.json()["display_name"] == "Ola"
    assert response.json()["email"] == "ola@test.pl"
    assert response.json()["role"] == "student"


def test_admin_sets_new_password(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    teacher = make_user(UserRole.TEACHER)

    response = client.patch(f"/users/{teacher.id}", json={"password": "InneHaslo99"})

    assert response.status_code == 200
    assert not _can_login(client, teacher.email, PASSWORD)
    assert _can_login(client, teacher.email, "InneHaslo99")


def test_edit_keeps_own_email(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    student = make_user(UserRole.STUDENT)
    response = client.patch(f"/users/{student.id}", json={"email": student.email.upper()})
    assert response.status_code == 200


def test_edit_rejects_email_of_another_account(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    student = make_user(UserRole.STUDENT)
    other = make_user(UserRole.TEACHER)
    response = client.patch(f"/users/{student.id}", json={"email": other.email})
    assert response.status_code == 409
    assert response.json() == {"code": "EMAIL_TAKEN"}


def test_role_cannot_be_changed(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    student = make_user(UserRole.STUDENT)
    response = client.patch(f"/users/{student.id}", json={"role": "teacher"})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_block_and_unblock_take_effect_immediately(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    student = make_user(UserRole.STUDENT)

    blocked = client.patch(f"/users/{student.id}", json={"is_active": False})
    assert blocked.status_code == 200
    assert blocked.json()["is_active"] is False
    assert not _can_login(client, student.email, PASSWORD)  # failed login keeps admin session

    unblocked = client.patch(f"/users/{student.id}", json={"is_active": True})
    assert unblocked.json()["is_active"] is True
    assert _can_login(client, student.email, PASSWORD)


def test_admin_accounts_are_not_managed(
    client: TestClient, make_user: Callable[..., User], admin: User
) -> None:
    other_admin = make_user(UserRole.ADMIN)
    for user_id in (admin.id, other_admin.id):
        response = client.patch(f"/users/{user_id}", json={"is_active": False})
        assert response.status_code == 404
        assert response.json() == {"code": "USER_NOT_FOUND"}


def test_update_unknown_user(client: TestClient, admin: User) -> None:
    response = client.patch("/users/999999", json={"is_active": False})
    assert response.status_code == 404
    assert response.json() == {"code": "USER_NOT_FOUND"}
