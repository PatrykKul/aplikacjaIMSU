from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User
from tests.curriculum.conftest import INTRODUCTION

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]


# --- Creating ----------------------------------------------------------------------------------


def test_teacher_creates_private_course(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)

    response = client.post("/courses", json={"title": "  Procenty ", "description": "Opis"})

    assert response.status_code == 201
    course = response.json()
    assert course["title"] == "Procenty"
    assert course["description"] == "Opis"
    assert course["owner_id"] == teacher.id
    assert course["is_published"] is False
    assert course["is_archived"] is False
    assert course["introduction"] is None
    assert course["lessons"] == []


def test_description_is_optional(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)
    response = client.post("/courses", json={"title": "Procenty"})
    assert response.status_code == 201
    assert response.json()["description"] == ""


@pytest.mark.parametrize(
    "body", [{}, {"title": "   "}, {"title": "x" * 121}, {"title": "T", "description": "x" * 501}]
)
def test_create_validates_fields(
    client: TestClient, login: Login, teacher: User, body: dict[str, Any]
) -> None:
    login(teacher)
    response = client.post("/courses", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("role_user", ["student", "admin"])
def test_only_teacher_creates_courses(
    client: TestClient, login: Login, request: pytest.FixtureRequest, role_user: str
) -> None:
    login(request.getfixturevalue(role_user))
    response = client.post("/courses", json={"title": "Procenty"})
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_courses_require_login(client: TestClient) -> None:
    assert client.get("/courses").status_code == 401


# --- Listing and visibility --------------------------------------------------------------------


def _titles(client: TestClient) -> set[str]:
    return {course["title"] for course in client.get("/courses").json()}


def test_teacher_lists_only_own_courses(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, other_teacher: User
) -> None:
    make_course(other_teacher, title="Cudzy opublikowany", published=True)
    make_course(teacher, title="Mój prywatny")
    make_course(teacher, title="Mój opublikowany", published=True)

    login(teacher)
    assert _titles(client) == {"Mój prywatny", "Mój opublikowany"}


def test_student_lists_only_published_courses(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, student: User
) -> None:
    make_course(teacher, title="Prywatny")
    make_course(teacher, title="Opublikowany", published=True)

    login(student)
    assert _titles(client) == {"Opublikowany"}


def test_admin_lists_every_course_with_archived(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, admin: User
) -> None:
    make_course(teacher, title="Prywatny")
    archived = make_course(teacher, title="Zarchiwizowany", published=True)
    client.delete(f"/courses/{archived['id']}")

    login(admin)
    titles = _titles(client)
    assert {"Prywatny", "Zarchiwizowany"} <= titles


def test_newest_course_is_listed_first(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User
) -> None:
    make_course(teacher, title="Pierwszy")
    make_course(teacher, title="Drugi")

    login(teacher)
    assert [c["title"] for c in client.get("/courses").json()] == ["Drugi", "Pierwszy"]


@pytest.mark.parametrize(
    ("viewer", "published", "visible"),
    [
        ("teacher", False, True),
        ("other_teacher", False, False),
        ("other_teacher", True, False),
        ("student", False, False),
        ("student", True, True),
        ("admin", False, True),
    ],
)
def test_course_page_visibility(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    request: pytest.FixtureRequest,
    teacher: User,
    viewer: str,
    published: bool,
    visible: bool,
) -> None:
    course = make_course(teacher, lessons=("Lekcja",), published=published)

    login(request.getfixturevalue(viewer))
    response = client.get(f"/courses/{course['id']}")

    if visible:
        assert response.status_code == 200
        assert [lesson["title"] for lesson in response.json()["lessons"]] == ["Lekcja"]
    else:
        assert response.status_code == 404
        assert response.json()["code"] == "COURSE_NOT_FOUND"


def test_missing_course_is_not_found(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)
    assert client.get("/courses/999999").json()["code"] == "COURSE_NOT_FOUND"


# --- Editing -----------------------------------------------------------------------------------


def test_owner_edits_course(client: TestClient, make_course: MakeCourse, teacher: User) -> None:
    course = make_course(teacher)

    response = client.patch(
        f"/courses/{course['id']}",
        json={"title": "Nowy tytuł", "description": "Nowy opis", "introduction": INTRODUCTION},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Nowy tytuł"
    assert updated["description"] == "Nowy opis"
    assert updated["introduction"] == INTRODUCTION
    assert updated["is_published"] is False


def test_partial_edit_keeps_other_fields(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher)
    client.patch(f"/courses/{course['id']}", json={"introduction": INTRODUCTION})

    updated = client.patch(f"/courses/{course['id']}", json={"title": "Inny"}).json()

    assert updated["description"] == "Opis"
    assert updated["introduction"] == INTRODUCTION


def test_owner_publishes_and_unpublishes(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    student: User,
) -> None:
    course = make_course(teacher)
    url = f"/courses/{course['id']}"

    assert client.patch(url, json={"is_published": True}).json()["is_published"] is True
    login(student)
    assert client.get(url).status_code == 200

    login(teacher)
    assert client.patch(url, json={"is_published": False}).json()["is_published"] is False
    login(student)
    assert client.get(url).status_code == 404


@pytest.mark.parametrize(
    "body",
    [
        {"introduction": {"type": "paragraph"}},
        {"introduction": "tekst"},
        {"introduction": {"type": "doc", "content": "x"}},
        {"title": ""},
        {"owner_id": 1},
    ],
)
def test_edit_validates_fields(
    client: TestClient, make_course: MakeCourse, teacher: User, body: dict[str, Any]
) -> None:
    course = make_course(teacher)
    response = client.patch(f"/courses/{course['id']}", json=body)
    assert response.status_code == 422


@pytest.mark.parametrize("editor", ["other_teacher", "student", "admin"])
def test_only_owner_edits_course(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    request: pytest.FixtureRequest,
    teacher: User,
    editor: str,
) -> None:
    course = make_course(teacher, published=True)

    login(request.getfixturevalue(editor))
    url = f"/courses/{course['id']}"

    assert client.patch(url, json={"title": "Przejęty"}).status_code == 404
    assert client.delete(url).status_code == 404
    login(teacher)
    assert client.get(url).json()["title"] == "Procenty"


# --- Archiving ---------------------------------------------------------------------------------


def test_archived_course_disappears_for_owner_and_students(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    student: User,
) -> None:
    course = make_course(teacher, published=True)
    url = f"/courses/{course['id']}"

    assert client.delete(url).status_code == 204

    assert client.get(url).status_code == 404
    assert client.patch(url, json={"title": "X"}).status_code == 404
    assert client.get("/courses").json() == []
    login(student)
    assert client.get(url).status_code == 404
    assert client.get("/courses").json() == []


def test_admin_still_sees_archived_course(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, admin: User
) -> None:
    course = make_course(teacher)
    client.delete(f"/courses/{course['id']}")

    login(admin)
    response = client.get(f"/courses/{course['id']}")

    assert response.status_code == 200
    assert response.json()["is_archived"] is True
