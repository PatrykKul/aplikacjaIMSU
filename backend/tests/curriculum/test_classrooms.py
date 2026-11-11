from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User, UserRole

MakeCourse = Callable[..., dict[str, Any]]
MakeUser = Callable[..., User]
Login = Callable[[User], None]


def _create(client: TestClient, name: str = "Klasa 7a") -> dict[str, Any]:
    response = client.post("/classrooms", json={"name": name})
    assert response.status_code == 201
    return response.json()


def _get(client: TestClient, classroom_id: int) -> dict[str, Any]:
    response = client.get(f"/classrooms/{classroom_id}")
    assert response.status_code == 200
    return response.json()


# --- Creating and listing ----------------------------------------------------------------------


def test_teacher_creates_empty_classroom(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)

    classroom = _create(client, "  Klasa 7a ")

    assert classroom == {
        "id": classroom["id"],
        "name": "Klasa 7a",
        "teacher": {"id": teacher.id, "display_name": teacher.display_name, "email": teacher.email},
        "courses": [],
        "students": [],
    }


@pytest.mark.parametrize("body", [{}, {"name": "   "}, {"name": "x" * 81}])
def test_create_validates_name(
    client: TestClient, login: Login, teacher: User, body: dict[str, Any]
) -> None:
    login(teacher)
    response = client.post("/classrooms", json=body)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("role_user", ["student", "admin"])
def test_only_teacher_creates_classrooms(
    client: TestClient, login: Login, request: pytest.FixtureRequest, role_user: str
) -> None:
    login(request.getfixturevalue(role_user))
    response = client.post("/classrooms", json={"name": "Klasa"})
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_admin_has_no_classrooms(client: TestClient, login: Login, admin: User) -> None:
    login(admin)
    response = client.get("/classrooms")
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_classrooms_require_login(client: TestClient) -> None:
    assert client.get("/classrooms").status_code == 401


def test_teacher_lists_own_classrooms_by_name_with_counts(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    other_teacher: User,
    student: User,
) -> None:
    login(other_teacher)
    _create(client, "Cudza klasa")
    course = make_course(teacher)
    seventh = _create(client, "Klasa 7b")
    _create(client, "Klasa 6a")
    client.put(f"/classrooms/{seventh['id']}/students/{student.id}")
    client.put(f"/classrooms/{seventh['id']}/courses/{course['id']}")

    response = client.get("/classrooms")

    assert response.status_code == 200
    assert [(c["name"], c["student_count"], c["course_count"]) for c in response.json()] == [
        ("Klasa 6a", 0, 0),
        ("Klasa 7b", 1, 1),
    ]


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_other_teachers_classroom_is_not_found(
    client: TestClient, login: Login, teacher: User, other_teacher: User, method: str
) -> None:
    login(other_teacher)
    classroom = _create(client)
    login(teacher)

    kwargs = {"json": {"name": "Moja"}} if method == "patch" else {}
    response = getattr(client, method)(f"/classrooms/{classroom['id']}", **kwargs)

    assert response.status_code == 404
    assert response.json()["code"] == "CLASSROOM_NOT_FOUND"


def test_missing_classroom_is_not_found(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)
    assert client.get("/classrooms/999999").json()["code"] == "CLASSROOM_NOT_FOUND"


# --- Renaming and deleting ---------------------------------------------------------------------


def test_teacher_renames_classroom(client: TestClient, login: Login, teacher: User) -> None:
    login(teacher)
    classroom = _create(client)

    response = client.patch(f"/classrooms/{classroom['id']}", json={"name": " Klasa 8a "})

    assert response.status_code == 200
    assert response.json()["name"] == "Klasa 8a"
    assert _get(client, classroom["id"])["name"] == "Klasa 8a"


@pytest.mark.parametrize("body", [{"name": ""}, {"name": "x" * 81}, {"name": "A", "extra": 1}])
def test_rename_validates_body(
    client: TestClient, login: Login, teacher: User, body: dict[str, Any]
) -> None:
    login(teacher)
    classroom = _create(client)
    assert client.patch(f"/classrooms/{classroom['id']}", json=body).status_code == 422


def test_deleting_classroom_keeps_courses_and_students(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, student: User
) -> None:
    course = make_course(teacher)
    classroom = _create(client)
    client.put(f"/classrooms/{classroom['id']}/students/{student.id}")
    client.put(f"/classrooms/{classroom['id']}/courses/{course['id']}")

    response = client.delete(f"/classrooms/{classroom['id']}")

    assert response.status_code == 204
    assert client.get(f"/classrooms/{classroom['id']}").status_code == 404
    assert client.get("/classrooms").json() == []
    assert client.get(f"/courses/{course['id']}").status_code == 200
    login(student)  # the account still works


# --- Students ----------------------------------------------------------------------------------


def test_teacher_adds_and_removes_students(
    client: TestClient, login: Login, make_user: MakeUser, teacher: User
) -> None:
    zosia = make_user(email="zosia@klasa.pl")
    adam = make_user(email="adam@klasa.pl")
    login(teacher)
    classroom = _create(client)
    url = f"/classrooms/{classroom['id']}/students"

    assert client.put(f"{url}/{zosia.id}").status_code == 204
    assert client.put(f"{url}/{adam.id}").status_code == 204
    students = _get(client, classroom["id"])["students"]
    assert {s["email"] for s in students} == {"zosia@klasa.pl", "adam@klasa.pl"}
    assert set(students[0]) == {"id", "display_name", "email"}

    assert client.delete(f"{url}/{zosia.id}").status_code == 204
    assert [s["email"] for s in _get(client, classroom["id"])["students"]] == ["adam@klasa.pl"]


def test_adding_student_again_changes_nothing(
    client: TestClient, login: Login, teacher: User, student: User
) -> None:
    login(teacher)
    classroom = _create(client)
    url = f"/classrooms/{classroom['id']}/students/{student.id}"

    client.put(url)
    assert client.put(url).status_code == 204

    assert len(_get(client, classroom["id"])["students"]) == 1


def test_removing_non_member_changes_nothing(
    client: TestClient, login: Login, teacher: User, student: User
) -> None:
    login(teacher)
    classroom = _create(client)
    assert client.delete(f"/classrooms/{classroom['id']}/students/{student.id}").status_code == 204


@pytest.mark.parametrize("kind", ["teacher", "admin", "blocked_student", "missing"])
def test_only_active_students_can_be_added(
    client: TestClient, login: Login, make_user: MakeUser, teacher: User, kind: str
) -> None:
    users = {
        "teacher": lambda: make_user(UserRole.TEACHER).id,
        "admin": lambda: make_user(UserRole.ADMIN).id,
        "blocked_student": lambda: make_user(is_active=False).id,
        "missing": lambda: 999999,
    }
    user_id = users[kind]()
    login(teacher)
    classroom = _create(client)

    response = client.put(f"/classrooms/{classroom['id']}/students/{user_id}")

    assert response.status_code == 404
    assert response.json()["code"] == "STUDENT_NOT_FOUND"


def test_teacher_cannot_change_students_of_other_teachers_classroom(
    client: TestClient, login: Login, teacher: User, other_teacher: User, student: User
) -> None:
    login(other_teacher)
    classroom = _create(client)
    login(teacher)

    for method in ("put", "delete"):
        response = getattr(client, method)(f"/classrooms/{classroom['id']}/students/{student.id}")
        assert response.status_code == 404
        assert response.json()["code"] == "CLASSROOM_NOT_FOUND"


# --- Courses -----------------------------------------------------------------------------------


def test_teacher_assigns_private_and_published_courses(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    private = make_course(teacher, title="Prywatny")
    published = make_course(teacher, title="Opublikowany", published=True)
    classroom = _create(client)
    url = f"/classrooms/{classroom['id']}/courses"

    assert client.put(f"{url}/{private['id']}").status_code == 204
    assert client.put(f"{url}/{published['id']}").status_code == 204

    courses = _get(client, classroom["id"])["courses"]
    assert [(c["title"], c["is_published"]) for c in courses] == [
        ("Opublikowany", True),
        ("Prywatny", False),
    ]


def test_assigning_course_again_changes_nothing(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher)
    classroom = _create(client)
    url = f"/classrooms/{classroom['id']}/courses/{course['id']}"

    client.put(url)
    assert client.put(url).status_code == 204

    assert len(_get(client, classroom["id"])["courses"]) == 1


def test_teacher_unassigns_course(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher)
    classroom = _create(client)
    url = f"/classrooms/{classroom['id']}/courses/{course['id']}"
    client.put(url)

    assert client.delete(url).status_code == 204
    assert client.delete(url).status_code == 204  # not assigned any more: nothing to do

    assert _get(client, classroom["id"])["courses"] == []
    assert client.get(f"/courses/{course['id']}").status_code == 200


def test_cannot_assign_other_teachers_or_archived_course(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, other_teacher: User
) -> None:
    foreign = make_course(other_teacher, published=True)
    archived = make_course(teacher)
    client.delete(f"/courses/{archived['id']}")
    classroom = _create(client)

    for course_id in (foreign["id"], archived["id"], 999999):
        response = client.put(f"/classrooms/{classroom['id']}/courses/{course_id}")
        assert response.status_code == 404
        assert response.json()["code"] == "COURSE_NOT_FOUND"
    assert _get(client, classroom["id"])["courses"] == []


def test_archived_course_stays_assigned_and_can_be_unassigned(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher)
    classroom = _create(client)
    url = f"/classrooms/{classroom['id']}/courses/{course['id']}"
    client.put(url)
    client.delete(f"/courses/{course['id']}")

    assert [c["is_archived"] for c in _get(client, classroom["id"])["courses"]] == [True]
    assert client.delete(url).status_code == 204
    assert _get(client, classroom["id"])["courses"] == []


def test_teacher_cannot_change_courses_of_other_teachers_classroom(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, other_teacher: User
) -> None:
    login(other_teacher)
    classroom = _create(client)
    course = make_course(teacher)

    for method in ("put", "delete"):
        response = getattr(client, method)(f"/classrooms/{classroom['id']}/courses/{course['id']}")
        assert response.status_code == 404
        assert response.json()["code"] == "CLASSROOM_NOT_FOUND"
