"""Course package: a directory with `course.yaml` and `lessons/<skill>.yaml`.

`load_package` reads and validates the whole package and reports every problem it
finds, with file names, before anything is written to the database.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from app.modules.content.steps import LessonSteps
from app.modules.curriculum.definitions import CourseDefinition, Key, Title

COURSE_FILE = "course.yaml"
LESSONS_DIR = "lessons"


class LessonDefinition(LessonSteps):
    """One lesson file: the skill it teaches and its steps."""

    skill: Key
    title: Title

    @property
    def file_name(self) -> str:
        return f"{self.skill}.yaml"


@dataclass(frozen=True)
class CoursePackage:
    course: CourseDefinition
    lessons: list[LessonDefinition]


class PackageError(Exception):
    """The package is invalid; `errors` lists every problem as 'file: location: message'."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__(f"{len(errors)} error(s) in the course package")
        self.errors = errors


def load_package(path: Path) -> CoursePackage:
    errors: list[str] = []
    course = _load(path, COURSE_FILE, CourseDefinition, errors)
    lessons: list[LessonDefinition] = []
    for file in sorted((path / LESSONS_DIR).glob("*.yaml")):
        label = f"{LESSONS_DIR}/{file.name}"
        lesson = _load(path, label, LessonDefinition, errors)
        if lesson is None:
            continue
        if file.name != lesson.file_name:
            errors.append(f"{label}: file name must match its content: {lesson.file_name}")
        lessons.append(lesson)

    # Cross-file rules only for files that are valid on their own, to avoid follow-up errors
    if course is not None and not errors:
        errors += _check_lessons_against_course(course, lessons)
    if course is None or errors:
        raise PackageError(errors)
    return CoursePackage(course=course, lessons=lessons)


def _load[M: BaseModel](root: Path, label: str, model: type[M], errors: list[str]) -> M | None:
    file = root / label
    if not file.is_file():
        errors.append(f"{label}: file not found")
        return None
    try:
        data: Any = yaml.safe_load(file.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        errors.append(f"{label}: invalid YAML: {' '.join(str(error).split())}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{label}: expected key: value pairs at the top level")
        return None
    try:
        return model.model_validate(data)
    except ValidationError as error:
        for problem in error.errors():
            location = ".".join(str(part) for part in problem["loc"])
            prefix = f"{label}: {location}: " if location else f"{label}: "
            errors.append(prefix + problem["msg"])
        return None


def _check_lessons_against_course(
    course: CourseDefinition, lessons: list[LessonDefinition]
) -> list[str]:
    errors = []
    skill_keys = [skill.key for skill in course.skills]
    with_lesson = {lesson.skill for lesson in lessons}
    for lesson in lessons:
        if lesson.skill not in skill_keys:
            errors.append(f"{LESSONS_DIR}/{lesson.file_name}: unknown skill {lesson.skill}")
    # One lesson per skill is guaranteed by the file names
    for key in skill_keys:
        if key not in with_lesson:
            errors.append(f"{COURSE_FILE}: skill {key} has no lesson {LESSONS_DIR}/{key}.yaml")
    return errors
