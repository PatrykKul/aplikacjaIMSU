from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.modules.identity.models import User, UserRole

INTRODUCTION = {
    "type": "doc",
    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Witaj w kursie"}]}],
}


@pytest.fixture
def teacher(make_user: Callable[..., User]) -> User:
    return make_user(UserRole.TEACHER)


@pytest.fixture
def other_teacher(make_user: Callable[..., User]) -> User:
    return make_user(UserRole.TEACHER)


@pytest.fixture
def student(make_user: Callable[..., User]) -> User:
    return make_user(UserRole.STUDENT)


@pytest.fixture
def admin(make_user: Callable[..., User]) -> User:
    return make_user(UserRole.ADMIN)


@pytest.fixture
def make_course(client: TestClient, login: Callable[[User], None]) -> Callable[..., dict[str, Any]]:
    """Create a course as `owner` (who stays logged in), optionally with lessons."""

    def _make(
        owner: User,
        *,
        title: str = "Procenty",
        lessons: tuple[str, ...] = (),
        published: bool = False,
    ) -> dict[str, Any]:
        login(owner)
        course = client.post("/courses", json={"title": title, "description": "Opis"}).json()
        for lesson_title in lessons:
            client.post(f"/courses/{course['id']}/lessons", json={"title": lesson_title})
        if published:
            client.patch(f"/courses/{course['id']}", json={"is_published": True})
        return client.get(f"/courses/{course['id']}").json()

    return _make
