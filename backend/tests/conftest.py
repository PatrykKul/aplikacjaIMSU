import os
import tempfile
from pathlib import Path

import pytest

# Point the app at a throwaway SQLite file before anything imports app.database
_TMP_DIR = tempfile.mkdtemp(prefix="stylnauki-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_TMP_DIR, 'test.db').as_posix()}"
os.environ["GEMINI_API_KEY"] = ""

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402

BACKEND_ROOT = Path(__file__).resolve().parent.parent


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
