from typing import Annotated, Literal, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.modules.learning_style.schemas import QuizFeedback

MAX_QUESTIONS = 20

ItemId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,40}$")]
QuestionText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]
AnswerText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Form = Literal["V", "A", "K"]


class QuizAnswer(BaseModel):
    id: ItemId
    text: AnswerText


class QuizQuestion(BaseModel):
    id: ItemId
    text: QuestionText
    # Material the question is about; None = about the common part of the lesson
    form: Form | None = None
    answers: Annotated[list[QuizAnswer], Field(min_length=3, max_length=4)]
    correct_answer_id: ItemId

    @model_validator(mode="after")
    def _check_answers(self) -> Self:
        ids = [answer.id for answer in self.answers]
        if len(set(ids)) != len(ids):
            raise ValueError("answer ids must be unique in a question")
        if self.correct_answer_id not in ids:
            raise ValueError("correct_answer_id must be one of the answers")
        return self


class QuizContent(BaseModel):
    """Whole quiz of a lesson, as edited by the teacher."""

    questions: Annotated[list[QuizQuestion], Field(min_length=1, max_length=MAX_QUESTIONS)]

    @model_validator(mode="after")
    def _unique_ids(self) -> Self:
        ids = [question.id for question in self.questions]
        if len(set(ids)) != len(ids):
            raise ValueError("question ids must be unique in a quiz")
        return self


class QuizEditResponse(BaseModel):
    """For the author: with correct answers; empty list when the lesson has no quiz yet."""

    questions: list[QuizQuestion]


class StudentQuestion(BaseModel):
    id: str
    text: str
    form: Form | None
    answers: list[QuizAnswer]


class StudentQuizResponse(BaseModel):
    """Questions without the answer key, chosen for the student's learning style."""

    questions: list[StudentQuestion]
    hidden_count: int


class AttemptRequest(BaseModel):
    # question id -> chosen answer id
    answers: Annotated[dict[str, str], Field(max_length=MAX_QUESTIONS)]


class QuestionResult(BaseModel):
    question_id: str
    correct: bool
    chosen_answer_id: str
    correct_answer_id: str


class AttemptResponse(BaseModel):
    percent: int
    correct_count: int
    total: int
    results: list[QuestionResult]
    # Present for students (see learning_style.hooks.record_quiz_result)
    adaptation: QuizFeedback | None = None
