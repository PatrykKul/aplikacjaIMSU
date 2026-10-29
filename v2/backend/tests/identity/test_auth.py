from collections.abc import Callable
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.modules.identity.models import User, UserRole

from .conftest import PASSWORD

REGISTER = {
    "email": " Nowy@Test.pl ",
    "password": "BardzoTajne1",
    "display_name": " Nowy ",
    "role": "student",
}


def _error_fields(response) -> list[str]:
    return [field["field"] for field in response.json()["fields"]]


# --- registration ---


def test_register_student_sets_http_only_cookie(client: TestClient) -> None:
    response = client.post("/auth/register", json=REGISTER)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "nowy@test.pl"
    assert body["display_name"] == "Nowy"
    assert body["role"] == "student"
    assert body["is_active"] is True
    assert "password_hash" not in body

    cookie = response.headers["set-cookie"].lower()
    assert cookie.startswith(f"{get_settings().auth_cookie_name}=")
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_register_teacher(client: TestClient) -> None:
    response = client.post("/auth/register", json={**REGISTER, "role": "teacher"})
    assert response.status_code == 201
    assert response.json()["role"] == "teacher"


def test_register_cannot_create_admin(client: TestClient) -> None:
    response = client.post("/auth/register", json={**REGISTER, "role": "admin"})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "role" in _error_fields(response)


def test_register_duplicate_email_ignores_case(client: TestClient) -> None:
    assert client.post("/auth/register", json=REGISTER).status_code == 201
    response = client.post("/auth/register", json={**REGISTER, "email": "NOWY@test.pl"})
    assert response.status_code == 409
    assert response.json() == {"code": "EMAIL_TAKEN"}


@pytest.mark.parametrize(
    ("change", "field"),
    [
        ({"email": "bez-malpy"}, "email"),
        ({"password": "krotkie"}, "password"),
        ({"password": "ą" * 37}, "password"),  # 37 chars, 74 bytes > bcrypt limit
        ({"display_name": "   "}, "display_name"),
    ],
)
def test_register_validation(client: TestClient, change: dict, field: str) -> None:
    response = client.post("/auth/register", json={**REGISTER, **change})
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert field in _error_fields(response)


def test_registered_user_is_logged_in(client: TestClient) -> None:
    client.post("/auth/register", json=REGISTER)
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "nowy@test.pl"


# --- login ---


def test_login_normalizes_email_and_sets_cookie(
    client: TestClient, make_user: Callable[..., User]
) -> None:
    make_user(email="jan@test.pl")
    response = client.post("/auth/login", json={"email": " JAN@test.pl ", "password": PASSWORD})
    assert response.status_code == 200
    assert "set-cookie" in response.headers
    assert client.get("/auth/me").json()["email"] == "jan@test.pl"


@pytest.mark.parametrize(
    ("email", "password", "is_active"),
    [
        ("jan@test.pl", "ZleHaslo123", True),
        ("nikt@test.pl", PASSWORD, True),
        ("jan@test.pl", PASSWORD, False),
    ],
    ids=["wrong-password", "unknown-email", "blocked-account"],
)
def test_login_failures_share_one_code(
    client: TestClient,
    make_user: Callable[..., User],
    email: str,
    password: str,
    is_active: bool,
) -> None:
    make_user(email="jan@test.pl", is_active=is_active)
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.json() == {"code": "INVALID_CREDENTIALS"}


# --- session ---


def test_me_without_cookie(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json() == {"code": "NOT_AUTHENTICATED"}


def test_me_rejects_forged_token(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user()
    future = datetime.now(UTC) + timedelta(hours=1)
    forged = jwt.encode({"sub": str(user.id), "exp": future}, "x" * 40, algorithm="HS256")
    client.cookies.set(get_settings().auth_cookie_name, forged)
    assert client.get("/auth/me").status_code == 401


def test_me_rejects_expired_token(client: TestClient, make_user: Callable[..., User]) -> None:
    user = make_user()
    settings = get_settings()
    past = datetime.now(UTC) - timedelta(minutes=1)
    expired = jwt.encode(
        {"sub": str(user.id), "exp": past}, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    client.cookies.set(settings.auth_cookie_name, expired)
    assert client.get("/auth/me").status_code == 401


def test_blocking_takes_effect_immediately(
    client: TestClient, db: Session, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    user = make_user()
    login(user)
    assert client.get("/auth/me").status_code == 200

    user.is_active = False
    db.commit()
    assert client.get("/auth/me").status_code == 401


def test_role_change_takes_effect_immediately(
    client: TestClient, db: Session, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    user = make_user(UserRole.STUDENT)
    login(user)
    assert client.get("/users").status_code == 403

    user.role = UserRole.ADMIN
    db.commit()
    assert client.get("/users").status_code == 200


def test_logout_clears_session(
    client: TestClient, make_user: Callable[..., User], login: Callable[[User], None]
) -> None:
    login(make_user())
    response = client.post("/auth/logout")
    assert response.status_code == 204
    assert client.get("/auth/me").status_code == 401
