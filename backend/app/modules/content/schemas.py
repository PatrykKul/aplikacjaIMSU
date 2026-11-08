from typing import Any

from pydantic import BaseModel

from app.modules.content.files import FileKind


class UploadedFileResponse(BaseModel):
    id: int
    url: str
    original_name: str
    content_type: str
    size: int
    kind: FileKind


class LessonBlocksResponse(BaseModel):
    """Blocks as saved, plus read-only fields for display: `file_url`, `file_name`
    (attachments with a file) and `youtube_id` (YouTube videos)."""

    blocks: list[dict[str, Any]]
