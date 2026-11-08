from pathlib import Path

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.demo import seed
from app.demo.courses import COURSES
from app.modules.content.models import File
from app.modules.curriculum.models import Course
from app.modules.learning_style import service as learning_style
from app.modules.learning_style.models import LearningProfile, QuizAttempt


@pytest.fixture(autouse=True)
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path / "uploads")
    return tmp_path / "uploads"


def _run(db: Session) -> tuple:
    teacher = seed.ensure_user(db, seed.TEACHER)
    new_student = seed.ensure_user(db, seed.NEW_STUDENT)
    student = seed.ensure_user(db, seed.VISUAL_STUDENT)
    for course in COURSES:
        seed.ensure_course(db, teacher, course)
    seed.ensure_visual_student(db, student, teacher)
    return teacher, new_student, student


def _count(db: Session, model, *where) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*where))


def test_seed_creates_published_courses_with_files(db: Session, upload_dir: Path):
    teacher, _, _ = _run(db)
    courses = db.scalars(select(Course).where(Course.owner_id == teacher.id)).all()
    assert {c.title for c in courses} == {c.title for c in COURSES}
    assert all(c.is_published for c in courses)
    files = _count(db, File, File.owner_id == teacher.id)
    assert files > 0
    assert len(list(upload_dir.iterdir())) == files


def test_seed_student_has_proposal_and_new_student_has_no_survey(db: Session):
    _, new_student, student = _run(db)
    assert db.get(LearningProfile, new_student.id) is None
    profile = learning_style.profile_response(db, student)
    assert profile.style == "V"
    assert profile.weights == {"V": 7, "A": 8, "K": 3}
    assert profile.proposal is not None and profile.proposal.style == "A"


def test_seed_is_idempotent(db: Session):
    teacher, _, student = _run(db)
    files = _count(db, File, File.owner_id == teacher.id)
    _run(db)
    assert _count(db, Course, Course.owner_id == teacher.id) == len(COURSES)
    assert _count(db, File, File.owner_id == teacher.id) == files
    assert _count(db, QuizAttempt, QuizAttempt.user_id == student.id) == len(seed.VISUAL_QUIZZES)


def test_reset_clears_only_learning_data(db: Session):
    _, _, student = _run(db)
    seed.reset_student(db, student)
    assert db.get(LearningProfile, student.id) is None
    assert _count(db, QuizAttempt, QuizAttempt.user_id == student.id) == 0
    assert seed.ensure_user(db, seed.VISUAL_STUDENT).id == student.id
