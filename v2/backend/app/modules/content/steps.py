"""Lesson steps and their answers.

The same models validate course package files and the json stored in `lessons.steps`.
"""

from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.content.numbers import parse_number

StepKey = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=64)]
Markdown = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]


class ContentModel(BaseModel):
    # A typo in a course file (e.g. "explenation") must be an error, not silently ignored
    model_config = ConfigDict(extra="forbid", frozen=True)


class NumberFeedback(ContentModel):
    """Message shown when the student gives the particular wrong value (a typical mistake)."""

    when: str
    message: Markdown


class NumberAnswer(ContentModel):
    type: Literal["number"]
    value: str
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    # Data for an independent recalculation in content tests; not used by the application
    check: dict[str, Any] | None = None
    feedback: list[NumberFeedback] = []

    @model_validator(mode="after")
    def _values_are_numbers(self) -> Self:
        correct = parse_number(self.value)
        seen = set()
        for item in self.feedback:
            wrong = parse_number(item.when)
            if wrong == correct:
                raise ValueError(f"feedback 'when' {item.when!r} equals the correct value")
            if wrong in seen:
                raise ValueError(f"duplicate feedback for {item.when!r}")
            seen.add(wrong)
        return self


class ChoiceOption(ContentModel):
    text: Markdown
    # Message shown the the student picks this (wrong) option
    feedback: Markdown | None = None


class ChoiceAnswer(ContentModel):
    type: Literal["choice"]
    options: list[ChoiceOption] = Field(min_length=2, max_length=6)
    correct: int = Field(ge=0)

    @model_validator(mode="after")
    def _correct_option_exists(self) -> Self:
        if self.correct >= len(self.options):
            raise ValueError("'correct' is outside the options list")
        if self.options[self.correct].feedback is not None:
            raise ValueError("the correct option must not have feedback")
        return self


Answer = Annotated[NumberAnswer | ChoiceAnswer, Field(discriminator="type")]


class TextStep(ContentModel):
    type: Literal["text"]
    key: StepKey
    body: Markdown


class QuestionStep(ContentModel):
    type: Literal["question"]
    key: StepKey
    prompt: Markdown
    answer: Answer
    hint: Markdown | None = None
    explanation: Markdown


Step = Annotated[TextStep | QuestionStep, Field(discriminator="type")]


class LessonSteps(ContentModel):
    steps: list[Step] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def _keys_unique_and_has_question(self) -> Self:
        keys = [step.key for step in self.steps]
        duplicates = sorted({key for key in keys if keys.count(key) > 1})
        if duplicates:
            raise ValueError(f"duplicate step keys: {', '.join(duplicates)}")
        if not any(isinstance(step, QuestionStep) for step in self.steps):
            raise ValueError("a lesson needs at least one question step")
        return self

    def find(self, key: str) -> TextStep | QuestionStep | None:
        return next((step for step in self.steps if step.key == key), None)

    def to_json(self) -> list[dict[str, Any]]:
        """Value for the `lessons.steps` JSONB column."""
        return self.model_dump(mode="json")["steps"]
