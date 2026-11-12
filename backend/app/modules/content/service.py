from pathlib import Path, PurePath
from typing import Any, BinaryIO
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.content import readiness
from app.modules.content.blocks import LessonBlocks, youtube_id
from app.modules.content.files import KIND_BY_CONTENT_TYPE, extension, file_type_for
from app.modules.content.models import File, LessonContent
from app.modules.content.schemas import UploadedFileResponse
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.readiness import Issue
from app.modules.identity.models import User, UserRole

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


FORMS = ("V", "A", "K")


def _content(db: Session, lesson_id: int, form: str) -> LessonContent | None:
    return db.scalar(
        select(LessonContent).where(
            LessonContent.lesson_id == lesson_id, LessonContent.form == form
        )
    )


def _stored_blocks(db: Session, lesson_id: int, form: str) -> list[dict[str, Any]]:
    content = _content(db, lesson_id, form)
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


def get_version(db: Session, lesson_id: int, form: str) -> list[dict[str, Any]]:
    """For other modules: blocks of one version, ready to show (access checked by the caller)."""
    return _present(db, _stored_blocks(db, lesson_id, form))


def stored_versions(db: Session, lesson_id: int) -> dict[str, list[dict[str, Any]]]:
    """Blocks of all three versions as saved (an empty list for a missing version)."""
    return {form: _stored_blocks(db, lesson_id, form) for form in FORMS}


def get_versions(db: Session, lesson_id: int, user: User) -> dict[str, list[dict[str, Any]]]:
    """All three versions for the author (editor, preview) and the admin (read only)."""
    lesson = curriculum.get_visible_lesson(db, lesson_id, user)
    if user.role != UserRole.ADMIN and lesson.course.owner_id != user.id:
        raise AppError(404, "LESSON_NOT_FOUND")
    return {form: get_version(db, lesson.id, form) for form in FORMS}


def _used_file_ids(db: Session, lesson_id: int) -> set[int]:
    """Files already used in any version of the lesson."""
    return {
        block["file_id"]
        for blocks in stored_versions(db, lesson_id).values()
        for block in blocks
        if block.get("file_id") is not None
    }


def _check_files(db: Session, data: LessonBlocks, owner_id: int, lesson_id: int) -> None:
    """Every file must match the attachment kind and belong to the course owner or be used
    in the lesson already (a new owner keeps the attachments of the previous one, D56)."""
    wanted = [
        item for block in data.blocks if block.type == "attachment" for item in block.file_ids()
    ]
    if not wanted:
        return
    used = _used_file_ids(db, lesson_id)
    files = {
        file.id: file
        for file in db.scalars(select(File).where(File.id.in_({file_id for file_id, _ in wanted})))
        if file.owner_id == owner_id or file.id in used
    }
    for file_id, kind in wanted:
        file = files.get(file_id)
        if file is None:
            raise AppError(400, "FILE_NOT_FOUND")
        if KIND_BY_CONTENT_TYPE[file.content_type] != kind:
            raise AppError(400, "FILE_KIND_MISMATCH")


def version_issues(db: Session, lesson_id: int) -> list[Issue]:
    """For authoring: what the three versions lack before publication (R11), V, A, K order."""
    versions = stored_versions(db, lesson_id)
    return [issue for form in FORMS for issue in readiness.version_issues(form, versions[form])]


def save_version(
    db: Session, lesson_id: int, form: str, user: User, data: LessonBlocks
) -> list[dict[str, Any]]:
    """Replace the blocks of one version; a published lesson must stay complete (R11)."""
    lesson = curriculum.get_owned_lesson(db, lesson_id, user)
    _check_files(db, data, lesson.course.owner_id, lesson.id)
    blocks = [block.model_dump(exclude_none=True) for block in data.blocks]
    if lesson.is_published:
        before = readiness.version_issues(form, _stored_blocks(db, lesson_id, form))
        missing = [i for i in readiness.version_issues(form, blocks) if i not in before]
        if missing:
            raise AppError(409, "PUBLISHED_LESSON_INCOMPLETE", issues=missing)
    content = _content(db, lesson_id, form)
    if content is None:
        db.add(LessonContent(lesson_id=lesson_id, form=form, blocks=blocks))
    else:
        content.blocks = blocks
    db.commit()
    return _present(db, blocks)
