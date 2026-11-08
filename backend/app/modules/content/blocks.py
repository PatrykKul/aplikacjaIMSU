"""Lesson blocks: text (TipTap document) and attachments marked with V / A / K forms."""

import re
from typing import Annotated, Any, Literal, Self
from urllib.parse import parse_qs, urlparse

from pydantic import (
    AfterValidator,
    BaseModel,
    Discriminator,
    Field,
    StringConstraints,
    Tag,
    model_validator,
)

from app.core.rich_text import RichTextDocument
from app.modules.content.files import FileKind

MAX_BLOCKS = 200

BlockId = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,40}$")]
Form = Literal["V", "A", "K"]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)]

_YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_YOUTUBE_HOSTS = {"youtube.com", "m.youtube.com", "youtube-nocookie.com"}


def youtube_id(url: str) -> str | None:
    """Video id from youtube.com/watch?v=, youtu.be/, /embed/ or /shorts/ addresses."""
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https"):
        return None
    host = (parsed.hostname or "").removeprefix("www.")
    candidate: str | None = None
    if host == "youtu.be":
        candidate = parsed.path.lstrip("/").split("/")[0]
    elif host in _YOUTUBE_HOSTS:
        parts = parsed.path.strip("/").split("/")
        if parts == ["watch"]:
            candidate = parse_qs(parsed.query).get("v", [None])[0]
        elif len(parts) >= 2 and parts[0] in ("embed", "shorts"):
            candidate = parts[1]
    return candidate if candidate and _YOUTUBE_ID.match(candidate) else None


def _check_youtube_url(value: str) -> str:
    if youtube_id(value) is None:
        raise ValueError("not a YouTube video address")
    return value.strip()


def _check_https_url(value: str) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("only https addresses are allowed")
    return value


def _check_forms(value: list[str]) -> list[str]:
    if len(set(value)) != len(value):
        raise ValueError("forms must not repeat")
    return value


YoutubeUrl = Annotated[str, StringConstraints(max_length=300), AfterValidator(_check_youtube_url)]
HttpsUrl = Annotated[
    str, StringConstraints(strip_whitespace=True, max_length=2000), AfterValidator(_check_https_url)
]
Forms = Annotated[list[Form], Field(min_length=1, max_length=3), AfterValidator(_check_forms)]


class TextBlock(BaseModel):
    id: BlockId
    type: Literal["text"]
    doc: RichTextDocument


class _Attachment(BaseModel):
    id: BlockId
    type: Literal["attachment"]
    forms: Forms
    title: Title
    description: ShortText = ""

    def file_ids(self) -> list[tuple[int, FileKind]]:
        """Files used by the attachment, with the kind each one must have."""
        return []


class ImageAttachment(_Attachment):
    kind: Literal["image"]
    file_id: int
    alt: ShortText = ""

    def file_ids(self) -> list[tuple[int, FileKind]]:
        return [(self.file_id, FileKind.IMAGE)]


class VideoAttachment(_Attachment):
    kind: Literal["video"]
    file_id: int | None = None
    youtube_url: YoutubeUrl | None = None

    @model_validator(mode="after")
    def _one_source(self) -> Self:
        if (self.file_id is None) == (self.youtube_url is None):
            raise ValueError("a video needs either file_id or youtube_url")
        return self

    def file_ids(self) -> list[tuple[int, FileKind]]:
        return [] if self.file_id is None else [(self.file_id, FileKind.VIDEO)]


class AudioAttachment(_Attachment):
    kind: Literal["audio"]
    file_id: int | None = None
    # Read aloud by the browser's speech synthesis and shown as a transcript
    transcript: (
        Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
        | None
    ) = None

    @model_validator(mode="after")
    def _one_source(self) -> Self:
        if (self.file_id is None) == (self.transcript is None):
            raise ValueError("a recording needs either file_id or transcript")
        return self

    def file_ids(self) -> list[tuple[int, FileKind]]:
        return [] if self.file_id is None else [(self.file_id, FileKind.AUDIO)]


class PdfAttachment(_Attachment):
    kind: Literal["pdf"]
    file_id: int

    def file_ids(self) -> list[tuple[int, FileKind]]:
        return [(self.file_id, FileKind.PDF)]


class LinkAttachment(_Attachment):
    kind: Literal["link"]
    url: HttpsUrl


def _block_tag(value: Any) -> str | None:
    data = value if isinstance(value, dict) else value.__dict__
    if data.get("type") == "attachment":
        return f"attachment:{data.get('kind')}"
    return data.get("type")


Block = Annotated[
    Annotated[TextBlock, Tag("text")]
    | Annotated[ImageAttachment, Tag("attachment:image")]
    | Annotated[VideoAttachment, Tag("attachment:video")]
    | Annotated[AudioAttachment, Tag("attachment:audio")]
    | Annotated[PdfAttachment, Tag("attachment:pdf")]
    | Annotated[LinkAttachment, Tag("attachment:link")],
    Discriminator(_block_tag),
]


class LessonBlocks(BaseModel):
    """Whole content of a lesson. Unknown fields (e.g. `file_url` sent back) are ignored."""

    blocks: Annotated[list[Block], Field(max_length=MAX_BLOCKS)]

    @model_validator(mode="after")
    def _unique_ids(self) -> Self:
        ids = [block.id for block in self.blocks]
        if len(set(ids)) != len(ids):
            raise ValueError("block ids must be unique in a lesson")
        return self
