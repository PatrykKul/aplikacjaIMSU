from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.core.rich_text import RichTextDocument
from app.modules.curriculum.models import TITLE_LENGTH, EnrollmentStatus
from app.modules.curriculum.progress import State
from app.modules.identity.schemas import StudentResponse

Title = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_LENGTH)
]
Description = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]


# --- Requests ------------------------------------------------------------------------------------


class CourseCreateRequest(BaseModel):
    title: Title
    description: Description = ""


class CourseUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    description: Description | None = None
    introduction: RichTextDocument | None = None
    summary: RichTextDocument | None = None
    is_published: bool | None = None


class LessonCreateRequest(BaseModel):
    title: Title


class LessonUpdateRequest(BaseModel):
    """Omitted fields stay; `null` clears the outline or the conclusions."""

    model_config = ConfigDict(extra="forbid")

    title: Title | None = None
    outline: RichTextDocument | None = None
    conclusions: RichTextDocument | None = None


class CourseOwnerRequest(BaseModel):
    owner_id: int


class LessonOrderRequest(BaseModel):
    lesson_ids: list[int] = Field(max_length=500)


# --- Courses -------------------------------------------------------------------------------------


class CourseOwnerResponse(BaseModel):
    id: int
    display_name: str


class CourseProgressResponse(BaseModel):
    passed: int
    total: int


class CourseSummaryResponse(BaseModel):
    """A course in a list. Student-only fields: `enrollment_status`, `progress`;
    author-only: `pending_requests` (null for others)."""

    id: int
    title: str
    description: str
    owner: CourseOwnerResponse
    is_published: bool
    is_archived: bool
    # Published lessons; the author and the admin count every active lesson
    lesson_count: int
    enrollment_status: EnrollmentStatus | None
    progress: CourseProgressResponse | None
    pending_requests: int | None
    updated_at: datetime


class CourseLessonResponse(BaseModel):
    id: int
    title: str
    number: int
    outline: dict[str, Any] | None
    # Author and admin only
    is_published: bool | None
    # Accepted student only (R10)
    state: State | None
    required_lesson_number: int | None


class CourseResponse(CourseSummaryResponse):
    introduction: dict[str, Any] | None
    summary: dict[str, Any] | None
    lessons: list[CourseLessonResponse]


# --- Lessons -------------------------------------------------------------------------------------


class LessonCourseResponse(BaseModel):
    id: int
    title: str
    owner_id: int


class LessonResponse(BaseModel):
    id: int
    title: str
    # Position among published lessons for a student, among all active ones for the author
    number: int
    outline: dict[str, Any] | None
    conclusions: dict[str, Any] | None
    is_published: bool
    course: LessonCourseResponse
    previous_lesson_id: int | None
    next_lesson_id: int | None
    # Student only: whether the next published lesson is open (null for others)
    next_lesson_unlocked: bool | None


# --- Enrollments ---------------------------------------------------------------------------------


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: int
    status: EnrollmentStatus
    requested_at: datetime
    decided_at: datetime | None


class CourseEnrollmentResponse(BaseModel):
    """An enrollment request as the course author sees it."""

    student: StudentResponse
    status: EnrollmentStatus
    requested_at: datetime
    decided_at: datetime | None
