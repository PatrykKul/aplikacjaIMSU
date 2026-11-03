from contextlib import nullcontext
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.content import cli
from app.modules.content.models import Lesson
from app.modules.curriculum.models import Course
from tests.content.builders import write_package


def test_invalid_package_prints_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    code = cli.main(["import-course", str(write_package(tmp_path, course=None))])
    assert code == 1
    assert "  - course.yaml: file not found" in capsys.readouterr().err


def test_import_course(
    db: Session, tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
):
    # Use the test session instead of the development database
    monkeypatch.setattr(cli, "SessionLocal", lambda: nullcontext(db))
    assert cli.main(["import-course", str(write_package(tmp_path))]) == 0
    assert "lessons:       2 created" in capsys.readouterr().out
    assert db.scalar(select(Course).where(Course.key == "test-course")) is not None
    assert len(db.scalars(select(Lesson)).all()) == 2
