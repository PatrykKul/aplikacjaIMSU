from pathlib import Path, PurePath
from typing import Any, BinaryIO
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.content.blocks import LessonBlocks, youtube_id
from app.modules.content.files import KIND_BY_CONTENT_TYPE, extension, file_type_for
from app.modules.content.models import File, LessonContent
from app.modules.content.schemas import UploadedFileResponse
from app.modules.curriculum import service as curriculum
from app.modules.identity.models import User

CHUNK_SIZE = 1024 * 1024

# --- Files -------------------------------------------------------------------------------------


def file_url(file_id: int) -> str:
    return f"/files/{file_id}"


def file_path(file: File) -> Path:
    return get_settings().upload_dir / file.storage_name


def file_response(file: File) -> UploadedFileResponse:
    return UploadedFileResponse(
        id=file.id,
        url=file_url(file.id),
        original_name=file.original_name,
        content_type=file.content_type,
        size=file.size,
        kind=KIND_BY_CONTENT_TYPE[file.content_type],
    )


def save_upload(db: Session, owner: User, filename: str, stream: BinaryIO) -> File:
    """Store an uploaded file under a random name; type from the extension (whitelist)."""
    file_type = file_type_for(filename)
    if file_type is None:
        raise AppError(400, "FILE_TYPE_NOT_ALLOWED")
    settings = get_settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    storage_name = f"{uuid4().hex}{extension(filename)}"
    path = settings.upload_dir / storage_name
    size = 0
    try:
        with path.open("wb") as target:
            while chunk := stream.read(CHUNK_SIZE):
                size += len(chunk)
                if size > settings.max_upload_bytes:
                    raise AppError(413, "FILE_TOO_LARGE")
                target.write(chunk)
        if size == 0:
            raise AppError(400, "FILE_EMPTY")
        file = File(
            owner_id=owner.id,
            original_name=PurePath(filename).name[:255],
            content_type=file_type.content_type,
            size=size,
            storage_name=storage_name,
        )
        db.add(file)
        db.commit()
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    db.refresh(file)
    return file


def get_file(db: Session, file_id: int) -> File:
    file = db.get(File, file_id)
    if file is None or not file_path(file).is_file():
        raise AppError(404, "FILE_NOT_FOUND")
    return file


# --- Lesson blocks -----------------------------------------------------------------------------


def _stored_blocks(db: Session, lesson_id: int) -> list[dict[str, Any]]:
    content = db.scalar(select(LessonContent).where(LessonContent.lesson_id == lesson_id))
    return [] if content is None else content.blocks


def _present(db: Session, blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Add display-only fields; the stored blocks stay as the teacher saved them."""
    ids = {block["file_id"] for block in blocks if block.get("file_id") is not None}
    rows = db.execute(select(File.id, File.original_name).where(File.id.in_(ids))) if ids else []
    names = {file_id: name for file_id, name in rows}
    presented = []
    for block in blocks:
        extra: dict[str, Any] = {}
        if block.get("file_id") is not None:
            extra = {
                "file_url": file_url(block["file_id"]),
                "file_name": names.get(block["file_id"]),
            }
        if block.get("youtube_url"):
            extra = {"youtube_id": youtube_id(block["youtube_url"])}
        presented.append(block | extra)
    return presented


def get_blocks(db: Session, lesson_id: int, user: User) -> list[dict[str, Any]]:
    lesson = curriculum.get_visible_lesson(db, lesson_id, user)
    return _present(db, _stored_blocks(db, lesson.id))


def _check_files(db: Session, data: LessonBlocks, owner_id: int) -> None:
    """Every file must belong to the course owner and match the attachment kind."""
    wanted = [
        item for block in data.blocks if block.type == "attachment" for item in block.file_ids()
    ]
    if not wanted:
        return
    files = {
        file.id: file
        for file in db.scalars(
            select(File).where(
                File.id.in_({file_id for file_id, _ in wanted}), File.owner_id == owner_id
            )
        )
    }
    for file_id, kind in wanted:
        file = files.get(file_id)
        if file is None:
            raise AppError(400, "FILE_NOT_FOUND")
        if KIND_BY_CONTENT_TYPE[file.content_type] != kind:
            raise AppError(400, "FILE_KIND_MISMATCH")


def save_blocks(
    db: Session, lesson_id: int, user: User, data: LessonBlocks
) -> list[dict[str, Any]]:
    lesson = curriculum.get_owned_lesson(db, lesson_id, user)
    _check_files(db, data, lesson.course.owner_id)
    blocks = [block.model_dump(exclude_none=True) for block in data.blocks]
    content = db.scalar(select(LessonContent).where(LessonContent.lesson_id == lesson_id))
    if content is None:
        db.add(LessonContent(lesson_id=lesson_id, blocks=blocks))
    else:
        content.blocks = blocks
    db.commit()
    return _present(db, blocks)
