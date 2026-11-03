from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.curriculum.definitions import CourseDefinition
from app.modules.curriculum.models import Course
from app.modules.curriculum.service import CourseSync, sync_course
from app.modules.identity.models import User, UserRole

DEFINITION = CourseDefinition.model_validate(
    {
        "key": "percentages",
        "title": "Procenty",
        "description": "Procenty w codziennym życiu.",
        "units": [
            {
                "key": "basics",
                "title": "Podstawy",
                "skills": [
                    {"key": "a", "title": "A", "goal": "Cel A"},
                    {"key": "b", "title": "B", "requires": ["a"]},
                ],
            },
            {
                "key": "applications",
                "title": "Zastosowania",
                "skills": [{"key": "c", "title": "C", "requires": ["a", "b"]}],
            },
        ],
    }
)

Login = Callable[[UserRole], User]


@pytest.fixture
def as_role(make_user: Callable[..., User], login: Callable[[User], None]) -> Login:
    def _as(role: UserRole) -> User:
        user = make_user(role)
        login(user)
        return user

    return _as


@pytest.fixture
def draft(db: Session) -> CourseSync:
    return sync_course(db, DEFINITION)


@pytest.fixture
def published(db: Session, draft: CourseSync) -> CourseSync:
    db.get(Course, draft.course_id).is_published = True
    db.flush()
    return draft


def test_anonymous_gets_401(client: TestClient, published: CourseSync):
    assert client.get("/courses").status_code == 401
    assert client.get(f"/courses/{published.course_id}").status_code == 401


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER])
def test_student_and_teacher_see_only_published_courses(
    client: TestClient, as_role: Login, db: Session, published: CourseSync, role: UserRole
):
    hidden = sync_course(db, DEFINITION.model_copy(update={"key": "draft-course"}))
    as_role(role)

    keys = [course["key"] for course in client.get("/courses").json()]

    assert keys == ["percentages"]
    response = client.get(f"/courses/{hidden.course_id}")
    assert (response.status_code, response.json()) == (404, {"code": "COURSE_NOT_FOUND"})


def test_admin_sees_drafts_and_archived_courses(
    client: TestClient, as_role: Login, db: Session, draft: CourseSync
):
    archived = sync_course(db, DEFINITION.model_copy(update={"key": "old-course"}))
    db.get(Course, archived.course_id).is_archived = True
    db.flush()
    as_role(UserRole.ADMIN)

    courses = {course["key"]: course for course in client.get("/courses").json()}

    assert courses["percentages"]["is_published"] is False
    assert courses["old-course"]["is_archived"] is True
    assert client.get(f"/courses/{draft.course_id}").status_code == 200


def test_course_detail(client: TestClient, as_role: Login, published: CourseSync):
    as_role(UserRole.STUDENT)
    ids = published.skill_ids

    course = client.get(f"/courses/{published.course_id}").json()

    assert course["title"] == "Procenty"
    assert course["description"] == "Procenty w codziennym życiu."
    assert [unit["key"] for unit in course["units"]] == ["basics", "applications"]
    basics, applications = course["units"]
    assert basics["skills"] == [
        {"id": ids["a"], "key": "a", "title": "A", "goal": "Cel A", "requires": []},
        {"id": ids["b"], "key": "b", "title": "B", "goal": "", "requires": [ids["a"]]},
    ]
    assert applications["skills"][0]["requires"] == sorted([ids["a"], ids["b"]])


def test_archived_skill_is_hidden(
    client: TestClient, as_role: Login, db: Session, published: CourseSync
):
    without_c = DEFINITION.model_copy(update={"units": DEFINITION.units[:1]})
    sync_course(db, without_c)
    as_role(UserRole.STUDENT)

    course = client.get(f"/courses/{published.course_id}").json()

    assert [unit["key"] for unit in course["units"]] == ["basics"]
    response = client.get(f"/skills/{published.skill_ids['c']}")
    assert (response.status_code, response.json()) == (404, {"code": "SKILL_NOT_FOUND"})


def test_skill_detail(client: TestClient, as_role: Login, published: CourseSync):
    as_role(UserRole.STUDENT)
    ids = published.skill_ids

    skill = client.get(f"/skills/{ids['b']}").json()

    assert skill["key"] == "b"
    assert skill["course_id"] == published.course_id
    assert skill["requires"] == [ids["a"]]


def test_skill_of_draft_course_is_hidden(client: TestClient, as_role: Login, draft: CourseSync):
    as_role(UserRole.STUDENT)
    assert client.get(f"/skills/{draft.skill_ids['a']}").status_code == 404
    assert client.get("/skills/999999").status_code == 404


def test_admin_publishes_course(client: TestClient, as_role: Login, draft: CourseSync):
    as_role(UserRole.ADMIN)

    response = client.patch(f"/courses/{draft.course_id}", json={"is_published": True})

    assert response.status_code == 200
    assert response.json()["is_published"] is True


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER])
def test_only_admin_publishes(
    client: TestClient, as_role: Login, draft: CourseSync, role: UserRole
):
    as_role(role)
    response = client.patch(f"/courses/{draft.course_id}", json={"is_published": True})
    assert (response.status_code, response.json()) == (403, {"code": "FORBIDDEN"})


def test_publish_errors(client: TestClient, as_role: Login, draft: CourseSync):
    assert (
        client.patch(f"/courses/{draft.course_id}", json={"is_published": True}).status_code == 401
    )
    as_role(UserRole.ADMIN)
    response = client.patch("/courses/999999", json={"is_published": True})
    assert (response.status_code, response.json()) == (404, {"code": "COURSE_NOT_FOUND"})
    assert client.patch(f"/courses/{draft.course_id}", json={}).status_code == 422
