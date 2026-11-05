from collections.abc import Callable, Iterator
from itertools import count
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.main import app
from app.modules.identity import service as identity_service
from app.modules.identity.models import User, UserRole

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = get_settings().test_database_url
    if not url:
        pytest.exit("TEST_DATABASE_URL is not set")
    eng = create_engine(url)
    with eng.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# --- Users shared by API tests of all modules ---------------------------------------------

PASSWORD = "BardzoTajne1"
_user_numbers = count(1)


@pytest.fixture
def make_user(db: Session) -> Callable[..., User]:
    def _make(
        role: UserRole = UserRole.STUDENT, *, email: str | None = None, is_active: bool = True
    ) -> User:
        user = identity_service.create_user(
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
