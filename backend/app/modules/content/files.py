"""Allowed file types: the type is decided by the extension, never by the client."""

from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePath


class FileKind(StrEnum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    PDF = "pdf"


@dataclass(frozen=True)
class FileType:
    kind: FileKind
    content_type: str


# No SVG or HTML: the backend serves files from its own origin
ALLOWED_TYPES: dict[str, FileType] = {
    ".png": FileType(FileKind.IMAGE, "image/png"),
    ".jpg": FileType(FileKind.IMAGE, "image/jpeg"),
    ".jpeg": FileType(FileKind.IMAGE, "image/jpeg"),
    ".webp": FileType(FileKind.IMAGE, "image/webp"),
    ".gif": FileType(FileKind.IMAGE, "image/gif"),
    ".mp3": FileType(FileKind.AUDIO, "audio/mpeg"),
    ".ogg": FileType(FileKind.AUDIO, "audio/ogg"),
    ".wav": FileType(FileKind.AUDIO, "audio/wav"),
    ".m4a": FileType(FileKind.AUDIO, "audio/mp4"),
    ".mp4": FileType(FileKind.VIDEO, "video/mp4"),
    ".webm": FileType(FileKind.VIDEO, "video/webm"),
    ".pdf": FileType(FileKind.PDF, "application/pdf"),
}

KIND_BY_CONTENT_TYPE = {
    file_type.content_type: file_type.kind for file_type in ALLOWED_TYPES.values()
}


def extension(filename: str) -> str:
    return PurePath(filename).suffix.lower()


def file_type_for(filename: str) -> FileType | None:
    return ALLOWED_TYPES.get(extension(filename))
