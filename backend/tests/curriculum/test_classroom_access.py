from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User

MakeCourse = Callable[..., dict[str, Any]]
MakeUser = Callable[..., User]
Login = Callable[[User], None]
FillSurvey = Callable[..., dict[str, Any]]

TEXT_BLOCK = {
    "id": "t1",
    "type": "text",
    "doc": {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Treść"}]}],
    },
}
QUESTION = {
    "id": "q1",
    "text": "Pytanie",
    "form": None,
    "answers": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}, {"id": "c", "text": "C"}],
    "correct_answer_id": "a",
}


def _classroom(
    client: TestClient,
    *,
    name: str = "Klasa 7a",
    students: tuple[User, ...] = (),
    courses: tuple[int, ...] = (),
) -> dict[str, Any]:
    """Create a classroom as the logged-in teacher with the given students and course ids."""
    classroom = client.post("/classrooms", json={"name": name}).json()
    for student in students:
        assert client.put(f"/classrooms/{classroom['id']}/students/{student.id}").status_code == 204
    for course_id in courses:
        assert client.put(f"/classrooms/{classroom['id']}/courses/{course_id}").status_code == 204
    return classroom


@pytest.fixture
def class_course(
    client: TestClient, make_course: MakeCourse, teacher: User, student: User
) -> dict[str, Any]:
    """A private course with a lesson (text block and quiz) assigned to the student's classroom."""
    course = make_course(teacher, title="Kurs klasy", lessons=("Lekcja",))
    lesson_id = course["lessons"][0]["id"]
    assert (
        client.put(f"/lessons/{lesson_id}/blocks", json={"blocks": [TEXT_BLOCK]}).status_code == 200
    )
    assert (
        client.put(f"/lessons/{lesson_id}/quiz", json={"questions": [QUESTION]}).status_code == 200
    )
    classroom = _classroom(client, students=(student,), courses=(course["id"],))
    return {"course_id": course["id"], "lesson_id": lesson_id, "classroom_id": classroom["id"]}


def _course_status(client: TestClient, ids: dict[str, Any]) -> tuple[int, int]:
    return (
        client.get(f"/courses/{ids['course_id']}").status_code,
        client.get(f"/lessons/{ids['lesson_id']}").status_code,
    )


# --- Access to the courses of a classroom ------------------------------------------------------


def test_student_opens_private_course_of_their_classroom(
    client: TestClient, fill_survey: FillSurvey, student: User, class_course: dict[str, Any]
) -> None:
    lesson_url = f"/lessons/{class_course['lesson_id']}"
    fill_survey(student)  # logs the student in

    assert _course_status(client, class_course) == (200, 200)
    assert [b["id"] for b in client.get(f"{lesson_url}/blocks").json()["blocks"]] == ["t1"]
    assert client.get(f"{lesson_url}/personalized-blocks").status_code == 200
    assert [q["id"] for q in client.get(f"{lesson_url}/quiz").json()["questions"]] == ["q1"]
    attempt = client.post(f"{lesson_url}/quiz/attempts", json={"answers": {"q1": "a"}})
    assert attempt.status_code == 200
    assert attempt.json()["percent"] == 100


@pytest.mark.parametrize("change", ["remove_student", "unassign_course", "delete_classroom"])
def test_student_loses_access_with_the_classroom_link(
    client: TestClient,
    login: Login,
    teacher: User,
    student: User,
    class_course: dict[str, Any],
    change: str,
) -> None:
    classroom_url = f"/classrooms/{class_course['classroom_id']}"
    url = {
        "remove_student": f"{classroom_url}/students/{student.id}",
        "unassign_course": f"{classroom_url}/courses/{class_course['course_id']}",
        "delete_classroom": classroom_url,
    }[change]
    login(teacher)
    assert client.delete(url).status_code == 204

    login(student)
    course = client.get(f"/courses/{class_course['course_id']}")
    lesson = client.get(f"/lessons/{class_course['lesson_id']}")
    assert (course.status_code, course.json()["code"]) == (404, "COURSE_NOT_FOUND")
    assert (lesson.status_code, lesson.json()["code"]) == (404, "LESSON_NOT_FOUND")


def test_student_outside_classroom_has_no_access(
    client: TestClient, login: Login, make_user: MakeUser, class_course: dict[str, Any]
) -> None:
    login(make_user())
    assert _course_status(client, class_course) == (404, 404)


def test_other_teacher_still_cannot_open_the_course(
    client: TestClient, login: Login, other_teacher: User, class_course: dict[str, Any]
) -> None:
    login(other_teacher)
    assert _course_status(client, class_course) == (404, 404)


def test_archived_course_disappears_from_classroom(
    client: TestClient, login: Login, teacher: User, student: User, class_course: dict[str, Any]
) -> None:
    login(teacher)
    client.delete(f"/courses/{class_course['course_id']}")

    login(student)
    assert _course_status(client, class_course) == (404, 404)
    assert client.get(f"/classrooms/{class_course['classroom_id']}").json()["courses"] == []
    assert client.get("/classrooms").json()[0]["course_count"] == 0


def test_catalog_lists_only_published_courses(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    student: User,
    class_course: dict[str, Any],
) -> None:
    published = make_course(teacher, title="Opublikowany", published=True)
    client.put(f"/classrooms/{class_course['classroom_id']}/courses/{published['id']}")

    login(student)
    catalog = {course["title"] for course in client.get("/courses").json()}
    classroom = client.get(f"/classrooms/{class_course['classroom_id']}").json()

    assert "Kurs klasy" not in catalog
    assert "Opublikowany" in catalog
    assert [course["title"] for course in classroom["courses"]] == ["Kurs klasy", "Opublikowany"]


# --- Student's classrooms ----------------------------------------------------------------------


def test_student_lists_own_classrooms_without_classmates(
    client: TestClient,
    login: Login,
    make_course: MakeCourse,
    teacher: User,
    other_teacher: User,
    student: User,
) -> None:
    course = make_course(other_teacher)
    _classroom(client, name="Kółko matematyczne", students=(student,), courses=(course["id"],))
    login(teacher)
    _classroom(client, name="Klasa 7a", students=(student,))
    _classroom(client, name="Klasa 7b")

    login(student)
    response = client.get("/classrooms")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": response.json()[0]["id"],
            "name": "Klasa 7a",
            "teacher": {
                "id": teacher.id,
                "display_name": teacher.display_name,
                "email": teacher.email,
            },
            "course_count": 0,
            "student_count": None,
        },
        {
            "id": response.json()[1]["id"],
            "name": "Kółko matematyczne",
            "teacher": {
                "id": other_teacher.id,
                "display_name": other_teacher.display_name,
                "email": other_teacher.email,
            },
            "course_count": 1,
            "student_count": None,
        },
    ]


def test_student_sees_classroom_without_classmates(
    client: TestClient,
    login: Login,
    make_user: MakeUser,
    teacher: User,
    student: User,
    class_course: dict[str, Any],
) -> None:
    login(teacher)
    client.put(f"/classrooms/{class_course['classroom_id']}/students/{make_user().id}")

    login(student)
    classroom = client.get(f"/classrooms/{class_course['classroom_id']}").json()

    assert classroom["name"] == "Klasa 7a"
    assert classroom["teacher"]["email"] == teacher.email
    assert [course["id"] for course in classroom["courses"]] == [class_course["course_id"]]
    assert classroom["students"] is None


def test_student_outside_classroom_cannot_open_it(
    client: TestClient, login: Login, make_user: MakeUser, class_course: dict[str, Any]
) -> None:
    login(make_user())

    response = client.get(f"/classrooms/{class_course['classroom_id']}")

    assert response.status_code == 404
    assert response.json() == {"code": "CLASSROOM_NOT_FOUND"}  # no teacher e-mail either
    assert client.get("/classrooms").json() == []


def test_admin_cannot_open_classroom(
    client: TestClient, login: Login, admin: User, class_course: dict[str, Any]
) -> None:
    login(admin)
    response = client.get(f"/classrooms/{class_course['classroom_id']}")
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("patch", ""),
        ("delete", ""),
        ("put", "/students/{student_id}"),
        ("delete", "/students/{student_id}"),
        ("put", "/courses/{course_id}"),
        ("delete", "/courses/{course_id}"),
    ],
)
def test_student_cannot_change_classroom(
    client: TestClient,
    login: Login,
    student: User,
    class_course: dict[str, Any],
    method: str,
    path: str,
) -> None:
    url = f"/classrooms/{class_course['classroom_id']}" + path.format(
        student_id=student.id, course_id=class_course["course_id"]
    )
    login(student)

    kwargs = {"json": {"name": "Moja klasa"}} if method == "patch" else {}
    response = getattr(client, method)(url, **kwargs)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
