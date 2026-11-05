from typing import Any

import pytest
from pydantic import ValidationError

from app.modules.curriculum.definitions import CourseDefinition


def skill(key: str) -> dict[str, Any]:
    return {"key": key, "title": key.upper()}


def course(*skills: dict[str, Any], **fields: Any) -> dict[str, Any]:
    unit = {"key": "basics", "title": "Podstawy", "skills": list(skills)}
    return {"key": "percentages", "title": "Procenty", "units": [unit], **fields}


def test_valid_course_lists_skills_of_all_units():
    data = course(skill("a"), skill("b"))
    data["units"].append({"key": "applications", "title": "Zastosowania", "skills": [skill("c")]})
    definition = CourseDefinition.model_validate(data)
    assert [s.key for s in definition.skills] == ["a", "b", "c"]
    assert definition.description == ""


def test_two_units_with_the_same_skill_key():
    data = course(skill("a"))
    data["units"].append({"key": "more", "title": "Więcej", "skills": [skill("a")]})
    with pytest.raises(ValidationError, match="duplicate skill keys: a"):
        CourseDefinition.model_validate(data)


@pytest.mark.parametrize(
    ("data", "message"),
    [
        pytest.param(
            course(skill("a"), skill("a")), "duplicate skill keys: a", id="duplicate skill"
        ),
        pytest.param(
            {
                **course(skill("a")),
                "units": [course(skill("a"))["units"][0], course(skill("b"))["units"][0]],
            },
            "duplicate unit keys: basics",
            id="duplicate unit",
        ),
        pytest.param(course(skill("Bad Key")), "should match pattern", id="key format"),
        pytest.param({**course(skill("a")), "titel": "x"}, "Extra inputs", id="unknown field"),
        pytest.param(course(), "at least 1 item", id="unit without skills"),
    ],
)
def test_invalid_course(data, message):
    with pytest.raises(ValidationError, match=message):
        CourseDefinition.model_validate(data)
