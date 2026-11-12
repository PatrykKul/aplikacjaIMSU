from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_SURVEY_ANSWERS = 200

Form = Literal["V", "A", "K"]
Percentages = dict[str, int]  # {"V": int, "A": int, "K": int}

# Fields named "from" in JSON (a Python keyword): `from_` in code
_FROM = ConfigDict(validate_by_name=True, validate_by_alias=True)


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


class SurveySummaryResponse(BaseModel):
    points: Percentages
    percentages: Percentages
    created_at: datetime


# --- Profile, proposals, trial -------------------------------------------------------------------


class StyleRequest(BaseModel):
    """Manual style change and the choice after a survey tie."""

    style: Form


class FormStatsResponse(BaseModel):
    confirmed: bool  # passed at least once in this form
    lessons: int  # counted results
    average: int | None


class Proposal(BaseModel):
    model_config = _FROM

    id: int
    kind: str
    from_: str = Field(alias="from")
    to: str
    evidence: dict[str, Any]
    created_at: datetime


class Trial(BaseModel):
    model_config = _FROM

    id: int
    from_: str = Field(alias="from")
    to: str
    source: str
    before_average: int | None
    after_average: int | None
    result: str | None
    done: int  # counted results in the new style so far
    needed: int
    started_at: datetime
    finished_at: datetime | None


class LearningProfileResponse(BaseModel):
    survey_completed: bool
    style: Form | None
    style_source: str | None
    tie_styles: list[str]  # not empty only for an unresolved survey tie
    percentages: Percentages | None
    forms: dict[str, FormStatsResponse] | None
    survey: SurveySummaryResponse | None
    open_proposal: Proposal | None
    trial: Trial | None  # running or the last finished one


# --- Quiz feedback -------------------------------------------------------------------------------


class LessonScoreResponse(BaseModel):
    lesson_id: int
    lesson_title: str
    percent: int


class FailedFormResponse(BaseModel):
    form: Form
    percent: int
    previous: LessonScoreResponse | None


class SuggestedFormResponse(BaseModel):
    form: Form
    reason: Literal["confirmed", "survey"]
    percent: int
    survey_percent: int
    best: LessonScoreResponse | None


class RetrySuggestion(BaseModel):
    failed: FailedFormResponse
    suggested: SuggestedFormResponse


class PraiseResponse(BaseModel):
    form: Form
    streak: int
    average: int


class LessonRefResponse(BaseModel):
    id: int
    title: str
    number: int | None


class QuizFeedback(BaseModel):
    form: Form
    counted: bool
    percentages_before: Percentages
    percentages_after: Percentages
    passed: bool
    unlocked_lesson: LessonRefResponse | None
    course_completed: bool
    praise: PraiseResponse | None
    suggestion: RetrySuggestion | None
    proposal: Proposal | None  # open after this attempt
    trial: Trial | None  # running, or finished by this attempt


# --- Studying a lesson ---------------------------------------------------------------------------


class LessonFormRequest(BaseModel):
    form: Form
    source: Literal["manual", "suggestion"] = "manual"


class LastResultResponse(BaseModel):
    percent: int
    passed: bool
    form: Form


class StudyResponse(BaseModel):
    lesson_id: int
    form: Form
    form_source: Literal["style", "choice"]
    style: Form
    blocks: list[dict[str, Any]]
    other_forms: list[Form]
    suggestion: RetrySuggestion | None
    last_result: LastResultResponse | None


class CourseHint(BaseModel):
    form: Form
    average: int
    students: int
    results: int


# --- Progress, journal, statistics ---------------------------------------------------------------


class HistoryPointResponse(BaseModel):
    at: datetime
    percentages: Percentages
    style: Form | None


class CourseProgressResponse(BaseModel):
    id: int
    title: str
    passed: int
    total: int
    next_lesson: LessonRefResponse | None


class AttemptItemResponse(BaseModel):
    at: datetime
    form: Form
    percent: int
    passed: bool
    counted: bool


class LessonResultResponse(BaseModel):
    course_id: int
    course_title: str
    lesson_id: int
    lesson_title: str
    number: int | None
    passed: bool
    attempts: list[AttemptItemResponse]


class ProgressResponse(BaseModel):
    history: list[HistoryPointResponse]
    courses: list[CourseProgressResponse]
    lessons: list[LessonResultResponse]


class RefResponse(BaseModel):
    id: int
    title: str


class JournalEntry(BaseModel):
    id: int
    type: str
    at: datetime
    course: RefResponse | None
    lesson: RefResponse | None
    data: dict[str, Any]


class FormEffectResponse(BaseModel):
    average: int | None
    counted_results: int
    attempts: int
    students: int


class OpenProposalBrief(BaseModel):
    to: Form
    kind: str


class CourseStudentResponse(BaseModel):
    id: int
    display_name: str
    email: str
    style: Form | None
    percentages: Percentages | None
    passed: int
    total: int
    average: int | None  # counted results in this course
    last_activity: datetime | None  # last result in this course
    open_proposal: OpenProposalBrief | None


class CourseStatsResponse(BaseModel):
    forms: dict[str, FormEffectResponse]
    styles: dict[str, int]  # V, A, K, none
    students: list[CourseStudentResponse]
    pending_requests: int


class StudentRefResponse(BaseModel):
    id: int
    display_name: str
    email: str


class StudentDetailResponse(BaseModel):
    student: StudentRefResponse
    profile: LearningProfileResponse
    history: list[HistoryPointResponse]
    lessons: list[LessonResultResponse]
    journal: list[JournalEntry]
