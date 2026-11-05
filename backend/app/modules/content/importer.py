"""Importing a course package into the database (used by the `import-course` command)."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.sync import Changes, assign_changed
from app.modules.content.models import Lesson
from app.modules.content.package import CoursePackage, LessonDefinition
from app.modules.curriculum import service as curriculum_service
from app.modules.curriculum.service import CourseSync


@dataclass(frozen=True)
class ImportReport:
    course_id: int
    # Keys in report order: course, units, skills, prerequisites, lessons
    changes: dict[str, Changes]
    dry_run: bool

    @property
    def has_changes(self) -> bool:
        return any(changes.total for changes in self.changes.values())


def import_package(db: Session, package: CoursePackage, *, dry_run: bool = False) -> ImportReport:
    """Synchronise the database with the package in one transaction (all or nothing).

    With `dry_run` every change is computed and reported, then rolled back.
    """
    try:
        sync = curriculum_service.sync_course(db, package.course)
        lessons = _sync_lessons(db, package.lessons, sync)
    except Exception:
        db.rollback()
        raise
    if dry_run:
        db.rollback()
    else:
        db.commit()
    return ImportReport(
        course_id=sync.course_id, changes={**sync.changes, "lessons": lessons}, dry_run=dry_run
    )


def _sync_lessons(db: Session, lessons: list[LessonDefinition], sync: CourseSync) -> Changes:
    changes = Changes()
    existing = {
        (lesson.skill_id, lesson.method): lesson
        for lesson in db.scalars(select(Lesson).where(Lesson.skill_id.in_(sync.all_skill_ids)))
    }
    for definition in lessons:
        skill_id = sync.skill_ids[definition.skill]
        values = {"title": definition.title, "steps": definition.to_json()}
        lesson = existing.pop((skill_id, definition.method), None)
        if lesson is None:
            db.add(Lesson(skill_id=skill_id, method=definition.method, **values))
            changes.created += 1
        elif assign_changed(lesson, **values, is_archived=False):
            changes.updated += 1
    # Lessons missing from the package (also those of archived skills)
    for lesson in existing.values():
        if not lesson.is_archived:
            lesson.is_archived = True
            changes.archived += 1
    db.flush()
    return changes


def format_report(report: ImportReport) -> str:
    lines = ["Dry run: nothing was saved."] if report.dry_run else []
    for kind, changes in report.changes.items():
        counts = [
            f"{count} {label}"
            for label, count in (
                ("created", changes.created),
                ("updated", changes.updated),
                ("archived", changes.archived),
                ("removed", changes.removed),
            )
            if count
        ]
        lines.append(f"{kind + ':':<15}{', '.join(counts) or 'no changes'}")
    return "\n".join(lines)
