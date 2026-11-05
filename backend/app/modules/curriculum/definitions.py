"""Course structure as written in a course package (`course.yaml`).

These models are the input of `service.sync_course`; they validate the whole
structure before anything touches the database.
"""

from collections.abc import Iterator
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.curriculum.models import KEY_LENGTH, TITLE_LENGTH

Key = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=KEY_LENGTH)]
Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_LENGTH)
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2000)]


class DefinitionModel(BaseModel):
    # A typo in a field name must be an error, not silently ignored
    model_config = ConfigDict(extra="forbid", frozen=True)


class SkillDefinition(DefinitionModel):
    key: Key
    title: Title
    goal: Description = ""


class UnitDefinition(DefinitionModel):
    key: Key
    title: Title
    skills: list[SkillDefinition] = Field(min_length=1)


class CourseDefinition(DefinitionModel):
    key: Key
    title: Title
    description: Description = ""
    units: list[UnitDefinition] = Field(min_length=1)

    @property
    def skills(self) -> Iterator[SkillDefinition]:
        for unit in self.units:
            yield from unit.skills

    @model_validator(mode="after")
    def _structure_is_consistent(self) -> Self:
        _reject_duplicates("unit keys", [unit.key for unit in self.units])
        _reject_duplicates("skill keys", [skill.key for skill in self.skills])
        return self


def _reject_duplicates(kind: str, keys: list[str]) -> None:
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    if duplicates:
        raise ValueError(f"duplicate {kind}: {', '.join(duplicates)}")
