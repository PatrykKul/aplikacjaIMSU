"""API views of lessons. Built field by field from the stored steps, so answer keys,
feedback, explanations and test data never reach the client before a check."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StringConstraints


class TextStepResponse(BaseModel):
    type: Literal["text"] = "text"
    key: str
    body: str


class NumberAnswerResponse(BaseModel):
    type: Literal["number"] = "number"
    unit: str | None


class ChoiceAnswerResponse(BaseModel):
    type: Literal["choice"] = "choice"
    options: list[str]


class QuestionStepResponse(BaseModel):
    type: Literal["question"] = "question"
    key: str
    prompt: str
    hint: str | None
    answer: Annotated[NumberAnswerResponse | ChoiceAnswerResponse, Field(discriminator="type")]


StepResponse = Annotated[TextStepResponse | QuestionStepResponse, Field(discriminator="type")]


class LessonResponse(BaseModel):
    id: int
    skill_id: int
    title: str
    steps: list[StepResponse]


class CheckRequest(BaseModel):
    # Text for number questions, option index for choice questions (StrictInt: true is not 1)
    answer: Annotated[str, StringConstraints(max_length=100)] | StrictInt
    # The student asks for the solution after a wrong answer
    reveal: bool = False


class CheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    correct: bool
    feedback: str | None
    explanation: str | None
    correct_answer: str | None
