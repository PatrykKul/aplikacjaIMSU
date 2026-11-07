from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User

MakeCourse = Callable[..., dict[str, Any]]
Login = Callable[[User], None]


def _lesson_titles(client: TestClient, course_id: int) -> list[str]:
    return [lesson["title"] for lesson in client.get(f"/courses/{course_id}").json()["lessons"]]


def _lesson_ids(course: dict[str, Any]) -> list[int]:
    return [lesson["id"] for lesson in course["lessons"]]


# --- Creating and ordering ---------------------------------------------------------------------


def test_owner_adds_lessons_at_the_end(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher, lessons=("Pierwsza",))

    response = client.post(f"/courses/{course['id']}/lessons", json={"title": " Druga "})

    assert response.status_code == 201
    lesson = response.json()
    assert lesson["title"] == "Druga"
    assert lesson["course"] == {"id": course["id"], "title": "Procenty", "owner_id": teacher.id}
    assert _lesson_titles(client, course["id"]) == ["Pierwsza", "Druga"]


def test_lesson_title_is_validated(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher)
    response = client.post(f"/courses/{course['id']}/lessons", json={"title": ""})
    assert response.status_code == 422


def test_owner_reorders_lessons(client: TestClient, make_course: MakeCourse, teacher: User) -> None:
    course = make_course(teacher, lessons=("A", "B", "C"))
    a, b, c = _lesson_ids(course)

    response = client.put(f"/courses/{course['id']}/lessons/order", json={"lesson_ids": [c, a, b]})

    assert response.status_code == 200
    assert [lesson["title"] for lesson in response.json()["lessons"]] == ["C", "A", "B"]
    assert _lesson_titles(client, course["id"]) == ["C", "A", "B"]


def test_lesson_added_after_reorder_goes_last(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher, lessons=("A", "B"))
    a, b = _lesson_ids(course)
    client.put(f"/courses/{course['id']}/lessons/order", json={"lesson_ids": [b, a]})

    client.post(f"/courses/{course['id']}/lessons", json={"title": "C"})

    assert _lesson_titles(client, course["id"]) == ["B", "A", "C"]


@pytest.mark.parametrize(
    "order",
    [
        lambda a, b, c: [a, b],  # missing lesson
        lambda a, b, c: [a, b, c, c],  # duplicate
        lambda a, b, c: [a, b, 999999],  # foreign id
        lambda a, b, c: [a, a, b],  # duplicate instead of one
    ],
)
def test_order_must_list_every_lesson_once(
    client: TestClient,
    make_course: MakeCourse,
    teacher: User,
    order: Callable[[int, int, int], list[int]],
) -> None:
    course = make_course(teacher, lessons=("A", "B", "C"))

    response = client.put(
        f"/courses/{course['id']}/lessons/order",
        json={"lesson_ids": order(*_lesson_ids(course))},
    )

    assert response.status_code == 400
    assert response.json()["code"] == "LESSON_ORDER_MISMATCH"
    assert _lesson_titles(client, course["id"]) == ["A", "B", "C"]


def test_order_ignores_archived_lessons(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher, lessons=("A", "B", "C"))
    a, b, c = _lesson_ids(course)
    client.delete(f"/lessons/{b}")

    url = f"/courses/{course['id']}/lessons/order"
    assert client.put(url, json={"lesson_ids": [c, a, b]}).status_code == 400
    assert client.put(url, json={"lesson_ids": [c, a]}).status_code == 200
    assert _lesson_titles(client, course["id"]) == ["C", "A"]


# --- Reading a lesson --------------------------------------------------------------------------


def test_lesson_has_course_and_neighbours(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher, lessons=("A", "B", "C"))
    a, b, c = _lesson_ids(course)

    first = client.get(f"/lessons/{a}").json()
    middle = client.get(f"/lessons/{b}").json()
    last = client.get(f"/lessons/{c}").json()

    assert middle["title"] == "B"
    assert middle["course"]["title"] == "Procenty"
    assert (first["previous_lesson_id"], first["next_lesson_id"]) == (None, b)
    assert (middle["previous_lesson_id"], middle["next_lesson_id"]) == (a, c)
    assert (last["previous_lesson_id"], last["next_lesson_id"]) == (b, None)


def test_neighbours_skip_archived_lesson(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher, lessons=("A", "B", "C"))
    a, b, c = _lesson_ids(course)
    client.delete(f"/lessons/{b}")

    assert client.get(f"/lessons/{a}").json()["next_lesson_id"] == c


@pytest.mark.parametrize(
    ("viewer", "published", "visible"),
    [
        ("teacher", False, True),
        ("other_teacher", True, False),
        ("student", False, False),
        ("student", True, True),
        ("admin", False, True),
    ],
)
def test_lesson_visibility_follows_course(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    request: pytest.FixtureRequest,
    teacher: User,
    viewer: str,
    published: bool,
    visible: bool,
) -> None:
    course = make_course(teacher, lessons=("A",), published=published)

    login(request.getfixturevalue(viewer))
    response = client.get(f"/lessons/{_lesson_ids(course)[0]}")

    assert response.status_code == (200 if visible else 404)
    if not visible:
        assert response.json()["code"] == "LESSON_NOT_FOUND"


def test_lessons_of_archived_course_are_hidden(
    client: TestClient, login: Login, make_course: MakeCourse, teacher: User, student: User
) -> None:
    course = make_course(teacher, lessons=("A",), published=True)
    lesson_id = _lesson_ids(course)[0]
    client.delete(f"/courses/{course['id']}")

    assert client.get(f"/lessons/{lesson_id}").status_code == 404
    assert client.patch(f"/lessons/{lesson_id}", json={"title": "X"}).status_code == 404
    login(student)
    assert client.get(f"/lessons/{lesson_id}").status_code == 404


# --- Editing and archiving ---------------------------------------------------------------------


def test_owner_renames_lesson(client: TestClient, make_course: MakeCourse, teacher: User) -> None:
    course = make_course(teacher, lessons=("A",))
    lesson_id = _lesson_ids(course)[0]

    response = client.patch(f"/lessons/{lesson_id}", json={"title": "Nowa nazwa"})

    assert response.status_code == 200
    assert response.json()["title"] == "Nowa nazwa"


def test_archived_lesson_disappears(
    client: TestClient, make_course: MakeCourse, teacher: User
) -> None:
    course = make_course(teacher, lessons=("A", "B"))
    a, _ = _lesson_ids(course)

    assert client.delete(f"/lessons/{a}").status_code == 204

    assert client.get(f"/lessons/{a}").status_code == 404
    assert client.delete(f"/lessons/{a}").status_code == 404
    assert _lesson_titles(client, course["id"]) == ["B"]


@pytest.mark.parametrize("editor", ["other_teacher", "student", "admin"])
def test_only_owner_changes_lessons(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    request: pytest.FixtureRequest,
    teacher: User,
    editor: str,
) -> None:
    course = make_course(teacher, lessons=("A",), published=True)
    lesson_id = _lesson_ids(course)[0]

    login(request.getfixturevalue(editor))

    assert client.post(f"/courses/{course['id']}/lessons", json={"title": "X"}).status_code == 404
    order_url = f"/courses/{course['id']}/lessons/order"
    assert client.put(order_url, json={"lesson_ids": [lesson_id]}).status_code == 404
    assert client.patch(f"/lessons/{lesson_id}", json={"title": "X"}).status_code == 404
    assert client.delete(f"/lessons/{lesson_id}").status_code == 404
    login(teacher)
    assert _lesson_titles(client, course["id"]) == ["A"]
