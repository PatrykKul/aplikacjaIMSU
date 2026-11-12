"""What a student sees of a course and its lessons: published lessons, enrollment, R10 lock."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]
Enroll = Callable[..., None]


@pytest.fixture
def course(
    make_course: MakeCourse, set_published: Callable[..., None], teacher: User
) -> dict[str, Any]:
    """Lessons A, B (draft), C, D; A, C, D published."""
    course = make_course(teacher, lessons=("A", "B", "C", "D"), published=True)
    set_published(course["lessons"][1]["id"], False)
    return course


def _ids(course: dict[str, Any]) -> dict[str, int]:
    return {lesson["title"]: lesson["id"] for lesson in course["lessons"]}


def _lessons(client: TestClient, course_id: int) -> list[tuple[str, int, str | None, int | None]]:
    lessons = client.get(f"/courses/{course_id}").json()["lessons"]
    return [
        (item["title"], item["number"], item["state"], item["required_lesson_number"])
        for item in lessons
    ]


# --- Course page -------------------------------------------------------------------------------


def test_student_sees_only_published_lessons_numbered_among_them(
    client: TestClient, login: Login, course: dict[str, Any], student: User
) -> None:
    login(student)

    detail = client.get(f"/courses/{course['id']}").json()

    assert [(item["title"], item["number"]) for item in detail["lessons"]] == [
        ("A", 1),
        ("C", 2),
        ("D", 3),
    ]
    assert {item["is_published"] for item in detail["lessons"]} == {None}
    assert {item["state"] for item in detail["lessons"]} == {None}  # not enrolled
    assert detail["lesson_count"] == 3
    assert detail["enrollment_status"] is None
    assert detail["pending_requests"] is None
    assert client.get("/courses").json()[0]["lesson_count"] == 3


@pytest.mark.parametrize("viewer", ["teacher", "admin"])
def test_author_and_admin_see_every_lesson(
    client: TestClient,
    login: Login,
    request: pytest.FixtureRequest,
    course: dict[str, Any],
    viewer: str,
) -> None:
    login(request.getfixturevalue(viewer))

    detail = client.get(f"/courses/{course['id']}").json()

    assert [
        (item["title"], item["number"], item["is_published"]) for item in detail["lessons"]
    ] == [
        ("A", 1, True),
        ("B", 2, False),
        ("C", 3, True),
        ("D", 4, True),
    ]
    assert detail["lesson_count"] == 4


def test_accepted_student_sees_lesson_states(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    student: User,
    enroll: Enroll,
    pass_lesson: Callable[[int, int], None],
) -> None:
    enroll(student, course["id"])
    login(student)
    assert _lessons(client, course["id"]) == [
        ("A", 1, "available", None),
        ("C", 2, "locked", 1),
        ("D", 3, "locked", 2),
    ]

    pass_lesson(student.id, _ids(course)["A"])

    assert _lessons(client, course["id"]) == [
        ("A", 1, "passed", None),
        ("C", 2, "available", None),
        ("D", 3, "locked", 2),
    ]
    listed = client.get("/courses").json()[0]
    assert listed["enrollment_status"] == "accepted"
    assert listed["progress"] == {"passed": 1, "total": 3}


# --- Lesson access (R10) -----------------------------------------------------------------------


@pytest.mark.parametrize("status", [None, "pending", "rejected"])
def test_lesson_needs_accepted_enrollment(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    student: User,
    enroll: Enroll,
    status: str | None,
) -> None:
    if status:
        enroll(student, course["id"], status)
    login(student)

    response = client.get(f"/lessons/{_ids(course)['A']}")

    assert response.status_code == 403
    assert response.json() == {"code": "ENROLLMENT_REQUIRED"}


def test_locked_lesson_names_the_lesson_to_pass(
    client: TestClient, login: Login, course: dict[str, Any], student: User, enroll: Enroll
) -> None:
    enroll(student, course["id"])
    login(student)
    ids = _ids(course)

    assert client.get(f"/lessons/{ids['A']}").status_code == 200
    response = client.get(f"/lessons/{ids['D']}")

    assert response.status_code == 403
    assert response.json() == {
        "code": "LESSON_LOCKED",
        "required_lesson": {"id": ids["C"], "title": "C", "number": 2},
    }


def test_passing_unlocks_next_published_lesson(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    student: User,
    enroll: Enroll,
    pass_lesson: Callable[[int, int], None],
) -> None:
    enroll(student, course["id"])
    login(student)
    ids = _ids(course)
    first = client.get(f"/lessons/{ids['A']}").json()
    assert first["next_lesson_id"] == ids["C"]  # draft B is skipped
    assert first["next_lesson_unlocked"] is False
    assert client.get(f"/lessons/{ids['C']}").json()["code"] == "LESSON_LOCKED"

    pass_lesson(student.id, ids["A"])

    assert client.get(f"/lessons/{ids['A']}").json()["next_lesson_unlocked"] is True
    second = client.get(f"/lessons/{ids['C']}")
    assert second.status_code == 200
    assert second.json()["number"] == 2
    assert second.json()["previous_lesson_id"] == ids["A"]


def test_unpublished_lesson_is_hidden_from_student(
    client: TestClient, login: Login, course: dict[str, Any], student: User, enroll: Enroll
) -> None:
    enroll(student, course["id"])
    login(student)

    response = client.get(f"/lessons/{_ids(course)['B']}")

    assert response.status_code == 404
    assert response.json() == {"code": "LESSON_NOT_FOUND"}


def test_last_lesson_has_nothing_to_unlock(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    student: User,
    enroll: Enroll,
    pass_lesson: Callable[[int, int], None],
) -> None:
    enroll(student, course["id"])
    ids = _ids(course)
    for title in ("A", "C"):
        pass_lesson(student.id, ids[title])
    login(student)

    last = client.get(f"/lessons/{ids['D']}").json()

    assert last["number"] == 3
    assert last["next_lesson_id"] is None
    assert last["next_lesson_unlocked"] is False


def test_passed_lesson_stays_open_after_reordering(
    client: TestClient,
    login: Login,
    course: dict[str, Any],
    teacher: User,
    student: User,
    enroll: Enroll,
    pass_lesson: Callable[[int, int], None],
) -> None:
    enroll(student, course["id"])
    ids = _ids(course)
    pass_lesson(student.id, ids["A"])
    pass_lesson(student.id, ids["C"])
    login(teacher)
    order = [ids["D"], ids["B"], ids["A"], ids["C"]]
    client.put(f"/courses/{course['id']}/lessons/order", json={"lesson_ids": order})

    login(student)

    assert _lessons(client, course["id"]) == [
        ("D", 1, "available", None),
        ("A", 2, "passed", None),
        ("C", 3, "passed", None),
    ]
    assert client.get(f"/lessons/{ids['C']}").status_code == 200


@pytest.mark.parametrize("viewer", ["teacher", "admin"])
def test_author_and_admin_preview_any_lesson(
    client: TestClient,
    login: Login,
    request: pytest.FixtureRequest,
    course: dict[str, Any],
    viewer: str,
) -> None:
    login(request.getfixturevalue(viewer))
    ids = _ids(course)

    draft = client.get(f"/lessons/{ids['B']}")
    last = client.get(f"/lessons/{ids['D']}").json()

    assert draft.status_code == 200
    assert draft.json()["number"] == 2
    assert draft.json()["is_published"] is False
    assert draft.json()["next_lesson_unlocked"] is None
    assert (last["number"], last["previous_lesson_id"]) == (4, ids["C"])
