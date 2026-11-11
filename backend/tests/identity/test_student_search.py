from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.identity.models import User, UserRole

MakeUser = Callable[..., User]
Login = Callable[[User], None]


def _emails(client: TestClient, query: str) -> list[str]:
    response = client.get("/students", params={"email": query})
    assert response.status_code == 200
    return [student["email"] for student in response.json()]


def test_teacher_finds_students_by_email_fragment(
    client: TestClient, login: Login, make_user: MakeUser, teacher: User
) -> None:
    ala = make_user(email="ala.nowak@szkola.pl")
    make_user(email="jan.kot@szkola.pl")
    login(teacher)

    response = client.get("/students", params={"email": "NOWAK"})

    assert response.status_code == 200
    assert response.json() == [{"id": ala.id, "display_name": "Test", "email": ala.email}]


def test_results_are_sorted_by_email(
    client: TestClient, login: Login, make_user: MakeUser, teacher: User
) -> None:
    make_user(email="zosia@sortowanie.pl")
    make_user(email="adam@sortowanie.pl")
    login(teacher)

    assert _emails(client, "sortowanie") == ["adam@sortowanie.pl", "zosia@sortowanie.pl"]


def test_only_active_students_are_found(
    client: TestClient, login: Login, make_user: MakeUser, teacher: User
) -> None:
    make_user(email="uczen@filtr.pl")
    make_user(email="zablokowany@filtr.pl", is_active=False)
    make_user(UserRole.TEACHER, email="nauczyciel@filtr.pl")
    make_user(UserRole.ADMIN, email="admin@filtr.pl")
    login(teacher)

    assert _emails(client, "filtr.pl") == ["uczen@filtr.pl"]


def test_wildcards_are_matched_literally(
    client: TestClient, login: Login, make_user: MakeUser, teacher: User
) -> None:
    make_user(email="a_b@wzorce.pl")
    make_user(email="axb@wzorce.pl")
    login(teacher)

    assert _emails(client, "a_b") == ["a_b@wzorce.pl"]
    assert _emails(client, "%@wzorce") == []


def test_results_are_limited(client: TestClient, db: Session, login: Login, teacher: User) -> None:
    # Inserted directly: hashing 21 passwords would slow the test down
    db.add_all(
        User(email=f"u{i:02}@limit.pl", password_hash="-", display_name="U", role=UserRole.STUDENT)
        for i in range(21)
    )
    db.commit()
    login(teacher)

    emails = _emails(client, "@limit.pl")

    assert len(emails) == 20
    assert emails[0] == "u00@limit.pl"


@pytest.mark.parametrize("params", [{}, {"email": "ab"}, {"email": "  ab  "}])
def test_query_needs_three_characters(
    client: TestClient, login: Login, teacher: User, params: dict[str, str]
) -> None:
    login(teacher)
    response = client.get("/students", params=params)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("role_user", ["student", "admin"])
def test_only_teacher_searches_students(
    client: TestClient, login: Login, request: pytest.FixtureRequest, role_user: str
) -> None:
    login(request.getfixturevalue(role_user))
    response = client.get("/students", params={"email": "test.pl"})
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_search_requires_login(client: TestClient) -> None:
    assert client.get("/students", params={"email": "test.pl"}).status_code == 401
