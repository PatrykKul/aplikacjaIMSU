from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.rich_text import RichTextDocument
from app.modules.curriculum.models import CLASSROOM_NAME_LENGTH, TITLE_LENGTH
from app.modules.identity.schemas import StudentResponse

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_LENGTH)
]
ClassroomName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CLASSROOM_NAME_LENGTH)
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


# --- Classrooms --------------------------------------------------------------------------------


class ClassroomCreateRequest(BaseModel):
    name: ClassroomName


class ClassroomUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: ClassroomName


class ClassroomTeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    email: str


class ClassroomSummaryResponse(BaseModel):
    id: int
    name: str
    teacher: ClassroomTeacherResponse
    course_count: int
    # Only for the classroom teacher; students do not see who else is in the classroom
    student_count: int | None = None


class ClassroomResponse(BaseModel):
    id: int
    name: str
    teacher: ClassroomTeacherResponse
    courses: list[CourseSummaryResponse]
    # Only for the classroom teacher
    students: list[StudentResponse] | None = None
