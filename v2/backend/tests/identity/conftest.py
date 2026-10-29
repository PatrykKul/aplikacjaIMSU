from collections.abc import Callable
from itertools import count

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.modules.identity import service
from app.modules.identity.models import User, UserRole

PASSWORD = "BardzoTajne1"
_user_numbers = count(1)


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    def _make(
        role: UserRole = UserRole.STUDENT, *, email: str | None = None, is_active: bool = True
    ) -> User:
        user = service.create_user(
            db,
            email=email or f"user{next(_user_numbers)}@test.pl",
            password=PASSWORD,
            display_name="Test",
            role=role,
        )
        if not is_active:
            user.is_active = False
            db.commit()
        return user

    return _make


@pytest.fixture
def login(client: TestClient) -> Callable[[User], None]:
    def _login(user: User) -> None:
        response = client.post("/auth/login", json={"email": user.email, "password": PASSWORD})
        assert response.status_code == 200

    return _login
