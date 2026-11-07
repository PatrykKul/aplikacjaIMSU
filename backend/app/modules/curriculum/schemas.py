from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.rich_text import RichTextDocument
from app.modules.curriculum.models import TITLE_LENGTH

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_LENGTH)
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


class CourseCreateRequest(BaseModel):
    title: Title
    description: Description = ""


class CourseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    description: Description | None = None
    introduction: RichTextDocument | None = None
    is_published: bool | None = None


class LessonCreateRequest(BaseModel):
    title: Title


class LessonUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title


class LessonOrderRequest(BaseModel):
    lesson_ids: list[int] = Field(max_length=500)


class CourseSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    title: str
    description: str
    is_published: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class LessonSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str


class CourseResponse(CourseSummaryResponse):
    introduction: dict[str, Any] | None
    lessons: list[LessonSummaryResponse]


class LessonCourseResponse(BaseModel):
    id: int
    title: str
    owner_id: int


class LessonResponse(BaseModel):
    id: int
    title: str
    course: LessonCourseResponse
    previous_lesson_id: int | None
    next_lesson_id: int | None
