from typing import Literal

from pydantic import BaseModel, ConfigDict


class IssueResponse(BaseModel):
    """One missing part of a lesson (R11); `count` and `min` only for the quiz pool."""

    area: Literal["lesson", "V", "A", "K", "quiz"]
    code: str
    count: int | None = None
    min: int | None = None


class ReadinessResponse(BaseModel):
    ready: bool
    issues: list[IssueResponse]


class PublicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    is_published: bool
