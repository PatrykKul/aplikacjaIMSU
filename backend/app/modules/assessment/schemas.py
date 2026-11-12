from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints, model_validator

from app.modules.learning_style.schemas import Form, QuizFeedback

MAX_QUESTIONS = 50
QUIZ_SIZE = 5  # questions drawn for one attempt

ItemId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,40}$")]
QuestionText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)
]
AnswerText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Explanation = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)
]


class QuizAnswer(BaseModel):
    id: ItemId
    text: AnswerText


class QuizQuestion(BaseModel):
    id: ItemId
    text: QuestionText
    answers: Annotated[list[QuizAnswer], Field(min_length=3, max_length=4)]
    correct_answer_id: ItemId
    # Why the correct answer is correct; shown to the student after the attempt
    explanation: Explanation

    @model_validator(mode="after")
    def _check_answers(self) -> Self:
        ids = [answer.id for answer in self.answers]
        if len(set(ids)) != len(ids):
            raise ValueError("answer ids must be unique in a question")
        if self.correct_answer_id not in ids:
            raise ValueError("correct_answer_id must be one of the answers")
        return self


class QuizContent(BaseModel):
    """Question pool of a lesson, as edited by the teacher (min. 5 to publish the lesson)."""

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


# --- Student -------------------------------------------------------------------------------------


class StudentQuestionResponse(BaseModel):
    """A drawn question without the correct answer and the explanation."""

    id: str
    text: str
    answers: list[QuizAnswer]


class StudentQuizResponse(BaseModel):
    draw_id: int
    questions: list[StudentQuestionResponse]
    pool_size: int
    form: Form  # lesson form the attempt will be recorded in


class AttemptRequest(BaseModel):
    draw_id: int
    # question id -> chosen answer id
    answers: Annotated[dict[str, str], Field(max_length=MAX_QUESTIONS)]


class QuestionResultResponse(BaseModel):
    question_id: str
    text: str
    answers: list[QuizAnswer]
    chosen_answer_id: str
    correct_answer_id: str
    correct: bool
    explanation: str


class AttemptResponse(BaseModel):
    draw_id: int
    percent: int
    correct_count: int
    total: int
    passed: bool
    results: list[QuestionResultResponse]
    feedback: QuizFeedback
