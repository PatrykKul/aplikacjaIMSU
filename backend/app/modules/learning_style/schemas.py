from datetime import datetime
from typing import Annotated, Any

from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from app.modules.learning_style.scoring import is_valid_style

MAX_SURVEY_ANSWERS = 200


def _check_style(value: str) -> str:
    if not is_valid_style(value):
        raise ValueError("style must be V, A, K or their combination in V-A-K order")
    return value


Style = Annotated[str, AfterValidator(_check_style)]


# --- Survey --------------------------------------------------------------------------------------


class SurveyAnswerResponse(BaseModel):
    """An answer without its style: the key never reaches the browser."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str


class SurveyQuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    answers: list[SurveyAnswerResponse]


class SurveyChoice(BaseModel):
    question_id: int
    answer_id: int


class SurveySubmitRequest(BaseModel):
    answers: Annotated[list[SurveyChoice], Field(max_length=MAX_SURVEY_ANSWERS)]


class SurveyResultResponse(BaseModel):
    points: dict[str, int]
    dominant_style: str
    created_at: datetime


# --- Profile -------------------------------------------------------------------------------------


class StyleProposalResponse(BaseModel):
    style: str
    message: str
    why: str


class LearningProfileResponse(BaseModel):
    survey_completed: bool
    style: str | None = None
    style_source: str | None = None
    weights: dict[str, int] | None = None
    last_result: SurveyResultResponse | None = None
    explanation: str | None = None
    proposal: StyleProposalResponse | None = None


class StyleChangeRequest(BaseModel):
    style: Style


# --- Lessons and quizzes -------------------------------------------------------------------------


class PersonalizedBlocksResponse(BaseModel):
    """All `blocks` of `GET /lessons/{id}/blocks` plus what to collapse for the student."""

    blocks: list[dict[str, Any]]
    style: str | None
    # Attachments without a form of the student's style (empty for teachers and admins)
    collapsed_block_ids: list[str]
    # Collapsed attachments the student has already opened in this lesson
    opened_block_ids: list[str]
    explanation: str


class QuizFeedback(BaseModel):
    """What the quiz module gets back from `hooks.record_quiz_result` (can be sent as JSON)."""

    passed: bool
    percent: int
    weights: dict[str, int]
    weights_changed: bool
    why: str
    proposal: StyleProposalResponse | None = None
