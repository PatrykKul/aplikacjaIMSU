from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.content.importer import format_report, import_package
from app.modules.content.models import Lesson, LessonMethod
from app.modules.content.package import CoursePackage, load_package
from app.modules.curriculum.models import Course
from tests.content.builders import COURSE, lesson, write_package


def package(path: Path, **kwargs) -> CoursePackage:
    return load_package(write_package(path, **kwargs))


def lessons_by_method(db: Session) -> dict[tuple[int, LessonMethod], Lesson]:
    return {(item.skill_id, item.method): item for item in db.scalars(select(Lesson))}


def test_import_creates_course_and_lessons(db: Session, tmp_path: Path):
    report = import_package(db, package(tmp_path))

    assert report.changes["course"].created == 1
    assert report.changes["skills"].created == 2
    assert report.changes["prerequisites"].created == 1
    assert report.changes["lessons"].created == 2
    assert db.get(Course, report.course_id).is_published is False
    assert len(lessons_by_method(db)) == 2


def test_second_import_reports_no_changes(db: Session, tmp_path: Path):
    import_package(db, package(tmp_path / "v1"))
    report = import_package(db, package(tmp_path / "v2"))
    assert report.has_changes is False


def test_changed_lesson_is_updated(db: Session, tmp_path: Path):
    import_package(db, package(tmp_path / "v1"))
    changed = [lesson("base", title="Nowy tytuł"), lesson("advanced")]
    report = import_package(db, package(tmp_path / "v2", lessons=changed))
    assert report.changes["lessons"].updated == 1
    assert "Nowy tytuł" in {item.title for item in lessons_by_method(db).values()}


def test_lesson_missing_from_package_is_archived_and_restored(db: Session, tmp_path: Path):
    with_beta = [lesson("base"), lesson("base", "beta"), lesson("advanced")]
    import_package(db, package(tmp_path / "v1", lessons=with_beta))

    report = import_package(db, package(tmp_path / "v2"))
    assert report.changes["lessons"].archived == 1
    beta = [item for item in lessons_by_method(db).values() if item.method == LessonMethod.BETA]
    assert [item.is_archived for item in beta] == [True]

    report = import_package(db, package(tmp_path / "v3", lessons=with_beta))
    assert report.changes["lessons"].updated == 1
    assert beta[0].is_archived is False


def test_lessons_of_archived_skill_are_archived(db: Session, tmp_path: Path):
    import_package(db, package(tmp_path / "v1"))
    course = {
        **COURSE,
        "units": [{**COURSE["units"][0], "skills": COURSE["units"][0]["skills"][:1]}],
    }
    report = import_package(db, package(tmp_path / "v2", course=course, lessons=[lesson("base")]))
    assert report.changes["skills"].archived == 1
    assert report.changes["lessons"].archived == 1


def test_dry_run_saves_nothing(db: Session, tmp_path: Path):
    report = import_package(db, package(tmp_path), dry_run=True)
    assert report.changes["lessons"].created == 2
    assert db.scalar(select(func.count()).select_from(Course)) == 0
    assert db.scalar(select(func.count()).select_from(Lesson)) == 0


def test_format_report(db: Session, tmp_path: Path):
    text = format_report(import_package(db, package(tmp_path), dry_run=True))
    assert text.splitlines()[0] == "Dry run: nothing was saved."
    assert "lessons:       2 created" in text
