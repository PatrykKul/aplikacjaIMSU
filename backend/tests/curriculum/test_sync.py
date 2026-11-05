import copy
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.curriculum.definitions import CourseDefinition
from app.modules.curriculum.models import Course, Skill
from app.modules.curriculum.service import sync_course

BASE: dict[str, Any] = {
    "key": "percentages",
    "title": "Procenty",
    "units": [
        {
            "key": "basics",
            "title": "Podstawy",
            "skills": [
                {"key": "a", "title": "A"},
                {"key": "b", "title": "B"},
            ],
        },
        {
            "key": "applications",
            "title": "Zastosowania",
            "skills": [{"key": "c", "title": "C"}],
        },
    ],
}


def definition(change=None) -> CourseDefinition:
    data = copy.deepcopy(BASE)
    if change:
        change(data)
    return CourseDefinition.model_validate(data)


def without_applications(data: dict[str, Any]) -> None:
    del data["units"][1]


def skill(db: Session, course_id: int, key: str) -> Skill:
    return db.scalars(select(Skill).where(Skill.course_id == course_id, Skill.key == key)).one()


def test_creates_course_structure(db: Session):
    result = sync_course(db, definition())
    course = db.get(Course, result.course_id)

    assert course.title == "Procenty"
    assert course.is_published is False
    assert [unit.key for unit in course.units] == ["basics", "applications"]
    assert [s.key for s in course.units[0].skills] == ["a", "b"]
    assert set(result.skill_ids) == {"a", "b", "c"}
    assert result.changes["course"].created == 1
    assert result.changes["units"].created == 2
    assert result.changes["skills"].created == 3


def test_second_sync_changes_nothing(db: Session):
    sync_course(db, definition())
    result = sync_course(db, definition())
    assert all(changes.total == 0 for changes in result.changes.values())


def test_changed_title_is_updated(db: Session):
    sync_course(db, definition())

    def rename(data):
        data["units"][0]["skills"][0]["title"] = "Nowe A"

    result = sync_course(db, definition(rename))
    assert result.changes["skills"].updated == 1
    assert skill(db, result.course_id, "a").title == "Nowe A"


def test_missing_skill_is_archived_and_restored(db: Session):
    first = sync_course(db, definition())

    second = sync_course(db, definition(without_applications))
    assert skill(db, second.course_id, "c").is_archived is True
    assert "c" not in second.skill_ids
    assert first.skill_ids["c"] in second.all_skill_ids
    assert second.changes["units"].archived == 1
    assert second.changes["skills"].archived == 1

    third = sync_course(db, definition())
    assert skill(db, third.course_id, "c").is_archived is False
    assert third.skill_ids["c"] == first.skill_ids["c"]
    assert third.changes["skills"].updated == 1


def test_skill_moved_to_another_unit(db: Session):
    first = sync_course(db, definition())

    def move_b(data):
        moved = data["units"][0]["skills"].pop()
        data["units"][1]["skills"].insert(0, moved)

    result = sync_course(db, definition(move_b))
    course = db.get(Course, result.course_id)
    assert [s.key for s in course.units[1].skills] == ["b", "c"]
    assert result.skill_ids["b"] == first.skill_ids["b"]


def test_publication_is_not_changed(db: Session):
    result = sync_course(db, definition())
    db.get(Course, result.course_id).is_published = True
    db.flush()

    def rename(data):
        data["title"] = "Procenty w praktyce"

    sync_course(db, definition(rename))
    assert db.get(Course, result.course_id).is_published is True


def test_new_course_is_placed_after_existing(db: Session):
    first = sync_course(db, definition())

    def other_key(data):
        data["key"] = "fractions"

    second = sync_course(db, definition(other_key))
    assert db.get(Course, second.course_id).position > db.get(Course, first.course_id).position
