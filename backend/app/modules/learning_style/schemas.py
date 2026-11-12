from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

MAX_SURVEY_ANSWERS = 200


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
