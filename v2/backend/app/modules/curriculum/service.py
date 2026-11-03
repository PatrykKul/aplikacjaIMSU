from collections.abc import Iterable
from dataclasses import dataclass, field

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.sync import Changes, assign_changed
from app.modules.curriculum.definitions import CourseDefinition
from app.modules.curriculum.models import Course, Skill, SkillPrerequisite, Unit
from app.modules.curriculum.schemas import (
    CourseResponse,
    CourseSummaryResponse,
    SkillResponse,
    SkillSummaryResponse,
    UnitResponse,
)
from app.modules.identity.models import User, UserRole


@dataclass
class CourseSync:
    """Result of `sync_course`: ids needed by other modules and a change report."""

    course_id: int
    # Active skills of the course by key
    skill_ids: dict[str, int]
    # Every skill of the course, archived ones included
    all_skill_ids: set[int]
    changes: dict[str, Changes] = field(default_factory=dict)


def sync_course(db: Session, definition: CourseDefinition) -> CourseSync:
    """Create or update a course from its definition, matching rows by key.

    Elements missing from the definition are archived (never deleted), archived ones that
    come back are restored, and the prerequisite graph is replaced. `is_published` is not
    touched. Flushes but does not commit: the caller owns the transaction.
    """
    changes = {kind: Changes() for kind in ("course", "units", "skills", "prerequisites")}
    course = _sync_course_row(db, definition, changes["course"])
    units = _sync_units(db, course, definition, changes["units"])
    skills = _sync_skills(db, course, definition, units, changes["skills"])
    _sync_prerequisites(db, course, definition, skills, changes["prerequisites"])
    return CourseSync(
        course_id=course.id,
        skill_ids={key: skill.id for key, skill in skills.items() if not skill.is_archived},
        all_skill_ids={skill.id for skill in skills.values()},
        changes=changes,
    )


def _sync_course_row(db: Session, definition: CourseDefinition, changes: Changes) -> Course:
    course = db.scalar(select(Course).where(Course.key == definition.key))
    if course is None:
        last_position = db.scalar(select(func.max(Course.position)))
        course = Course(
            key=definition.key,
            title=definition.title,
            description=definition.description,
            position=0 if last_position is None else last_position + 1,
        )
        db.add(course)
        db.flush()
        changes.created += 1
    elif assign_changed(
        course, title=definition.title, description=definition.description, is_archived=False
    ):
        changes.updated += 1
    return course


def _sync_units(
    db: Session, course: Course, definition: CourseDefinition, changes: Changes
) -> dict[str, Unit]:
    existing = {
        unit.key: unit for unit in db.scalars(select(Unit).where(Unit.course_id == course.id))
    }
    synced: dict[str, Unit] = {}
    for position, unit_definition in enumerate(definition.units):
        unit = existing.pop(unit_definition.key, None)
        if unit is None:
            unit = Unit(
                course_id=course.id,
                key=unit_definition.key,
                title=unit_definition.title,
                position=position,
            )
            db.add(unit)
            changes.created += 1
        elif assign_changed(
            unit, title=unit_definition.title, position=position, is_archived=False
        ):
            changes.updated += 1
        synced[unit.key] = unit
    _archive(existing.values(), changes)
    db.flush()
    return synced


def _sync_skills(
    db: Session,
    course: Course,
    definition: CourseDefinition,
    units: dict[str, Unit],
    changes: Changes,
) -> dict[str, Skill]:
    """Returns every skill of the course by key, archived ones included."""
    existing = {
        skill.key: skill for skill in db.scalars(select(Skill).where(Skill.course_id == course.id))
    }
    synced: dict[str, Skill] = {}
    for unit_definition in definition.units:
        unit = units[unit_definition.key]
        for position, skill_definition in enumerate(unit_definition.skills):
            values = {
                "unit_id": unit.id,
                "title": skill_definition.title,
                "goal": skill_definition.goal,
                "position": position,
            }
            skill = existing.pop(skill_definition.key, None)
            if skill is None:
                skill = Skill(course_id=course.id, key=skill_definition.key, **values)
                db.add(skill)
                changes.created += 1
            elif assign_changed(skill, **values, is_archived=False):
                changes.updated += 1
            synced[skill.key] = skill
    _archive(existing.values(), changes)
    db.flush()
    return synced | existing


def _sync_prerequisites(
    db: Session,
    course: Course,
    definition: CourseDefinition,
    skills: dict[str, Skill],
    changes: Changes,
) -> None:
    wanted = {
        (skills[skill.key].id, skills[required].id)
        for skill in definition.skills
        for required in skill.requires
    }
    current = {
        (row.skill_id, row.prerequisite_id)
        for row in db.execute(
            select(SkillPrerequisite.skill_id, SkillPrerequisite.prerequisite_id)
            .join(Skill, Skill.id == SkillPrerequisite.skill_id)
            .where(Skill.course_id == course.id)
        )
    }
    # Edges carry no history, so they are replaced instead of archived
    for skill_id, prerequisite_id in current - wanted:
        db.execute(
            delete(SkillPrerequisite).where(
                SkillPrerequisite.skill_id == skill_id,
                SkillPrerequisite.prerequisite_id == prerequisite_id,
            )
        )
        changes.removed += 1
    for skill_id, prerequisite_id in wanted - current:
        db.add(SkillPrerequisite(skill_id=skill_id, prerequisite_id=prerequisite_id))
        changes.created += 1
    db.flush()


def _archive(rows: Iterable[Unit | Skill], changes: Changes) -> None:
    for row in rows:
        if not row.is_archived:
            row.is_archived = True
            changes.archived += 1


# --- Reading and publishing --------------------------------------------------------------------
# Students and teachers see only published, non-archived courses; an admin sees everything.
# Archived units and skills are hidden from everyone. Hidden elements give 404, not 403,
# so the API does not reveal that they exist.


def can_view_course(course: Course, user: User) -> bool:
    if user.role == UserRole.ADMIN:
        return True
    return course.is_published and not course.is_archived


def list_courses(db: Session, user: User) -> list[Course]:
    query = select(Course).order_by(Course.position, Course.id)
    if user.role != UserRole.ADMIN:
        query = query.where(Course.is_published, Course.is_archived.is_(False))
    return list(db.scalars(query))


def get_course(db: Session, course_id: int, user: User) -> Course:
    course = db.get(Course, course_id)
    if course is None or not can_view_course(course, user):
        raise AppError(404, "COURSE_NOT_FOUND")
    return course


def get_course_detail(db: Session, course_id: int, user: User) -> CourseResponse:
    course = get_course(db, course_id, user)
    units = [unit for unit in course.units if not unit.is_archived]
    skills = {unit.id: [s for s in unit.skills if not s.is_archived] for unit in units}
    requires = _requirements(
        db, [skill.id for unit_skills in skills.values() for skill in unit_skills]
    )
    return CourseResponse(
        **CourseSummaryResponse.model_validate(course).model_dump(),
        units=[
            UnitResponse(
                id=unit.id,
                key=unit.key,
                title=unit.title,
                skills=[_skill_summary(skill, requires) for skill in skills[unit.id]],
            )
            for unit in units
        ],
    )


def get_skill(db: Session, skill_id: int, user: User) -> Skill:
    skill = _visible_skill(db, skill_id, user)
    if skill is None:
        raise AppError(404, "SKILL_NOT_FOUND")
    return skill


def get_skill_detail(db: Session, skill_id: int, user: User) -> SkillResponse:
    skill = get_skill(db, skill_id, user)
    requires = _requirements(db, [skill.id])
    return SkillResponse(
        **_skill_summary(skill, requires).model_dump(),
        course_id=skill.course_id,
        unit_id=skill.unit_id,
    )


def is_skill_visible(db: Session, skill_id: int, user: User) -> bool:
    """For other modules: may this user see content attached to the skill?"""
    return _visible_skill(db, skill_id, user) is not None


def set_published(db: Session, course_id: int, is_published: bool) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise AppError(404, "COURSE_NOT_FOUND")
    course.is_published = is_published
    db.commit()
    return course


def _visible_skill(db: Session, skill_id: int, user: User) -> Skill | None:
    skill = db.get(Skill, skill_id)
    if skill is None or skill.is_archived:
        return None
    course = db.get(Course, skill.course_id)
    if course is None or not can_view_course(course, user):
        return None
    return skill


def _requirements(db: Session, skill_ids: list[int]) -> dict[int, list[int]]:
    requires: dict[int, list[int]] = {skill_id: [] for skill_id in skill_ids}
    rows = db.execute(
        select(SkillPrerequisite.skill_id, SkillPrerequisite.prerequisite_id)
        .where(SkillPrerequisite.skill_id.in_(skill_ids))
        .order_by(SkillPrerequisite.skill_id, SkillPrerequisite.prerequisite_id)
    )
    for row in rows:
        requires[row.skill_id].append(row.prerequisite_id)
    return requires


def _skill_summary(skill: Skill, requires: dict[int, list[int]]) -> SkillSummaryResponse:
    return SkillSummaryResponse(
        id=skill.id,
        key=skill.key,
        title=skill.title,
        goal=skill.goal,
        requires=requires.get(skill.id, []),
    )
