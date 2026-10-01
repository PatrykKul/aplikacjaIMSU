import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway SQLite file before anything imports app.database
_TMP_DIR = tempfile.mkdtemp(prefix="stylnauki-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR, 'test.db').as_posix()}"
os.environ["GEMINI_API_KEY"] = ""
os.environ["JWT_SECRET"] = "test-secret-only-for-pytest-0123456789abcdef"

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import models  # noqa: E402
from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.security import hash_haslo, utworz_token  # noqa: E402

BACKEND_ROOT = Path(__file__).resolve().parent.parent

# bcrypt is slow on purpose — hash the shared test password once
HASLO = "Haslo123!"
_HASLO_HASH = hash_haslo(HASLO)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    # Schema is built by the real migrations, so they are tested too
    command.upgrade(Config(str(BACKEND_ROOT / "alembic.ini")), "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def _clean_tables(_schema):
    yield
    with SessionLocal() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def utworz_uzytkownika():
    """Factory: creates a user directly in the DB and returns (user_id, auth headers)."""

    def _utworz(rola: str = "uczen", email: str | None = None, **pola):
        with SessionLocal() as session:
            user = models.Uzytkownik(
                email=email or f"{rola}-{os.urandom(4).hex()}@test.pl",
                imie=rola.capitalize(),
                haslo_hash=_HASLO_HASH,
                rola=rola,
                **pola,
            )
            session.add(user)
            session.commit()
            return user.id, {"Authorization": f"Bearer {utworz_token(user.id, user.rola)}"}

    return _utworz


@pytest.fixture
def admin(utworz_uzytkownika):
    return utworz_uzytkownika("admin")[1]


@pytest.fixture
def nauczyciel(utworz_uzytkownika):
    return utworz_uzytkownika("nauczyciel")[1]


@pytest.fixture
def uczen(utworz_uzytkownika):
    # Student who already completed the survey (default for content tests)
    return utworz_uzytkownika("uczen", ankieta_wypelniona=True, styl_uczenia="V", styl_zrodlo="ankieta")[1]
