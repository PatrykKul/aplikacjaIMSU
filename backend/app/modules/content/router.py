from fastapi import APIRouter, UploadFile, status
from fastapi.responses import FileResponse

from app.core.db import DbSession
from app.modules.content import service
from app.modules.content.blocks import Form, LessonBlocks
from app.modules.content.schemas import (
    LessonBlocksResponse,
    LessonVersionsResponse,
    UploadedFileResponse,
)
from app.modules.identity.dependencies import CurrentUser, TeacherUser

lesson_versions_router = APIRouter(prefix="/lessons", tags=["content"])
files_router = APIRouter(prefix="/files", tags=["content"])


@lesson_versions_router.get("/{lesson_id}/versions")
def get_versions(lesson_id: int, db: DbSession, user: CurrentUser) -> LessonVersionsResponse:
    versions = service.get_versions(db, lesson_id, user)
    return LessonVersionsResponse.model_validate(
        {form: {"blocks": blocks} for form, blocks in versions.items()}
    )


@lesson_versions_router.put("/{lesson_id}/versions/{form}")
def save_version(
    lesson_id: int, form: Form, data: LessonBlocks, db: DbSession, user: CurrentUser
) -> LessonBlocksResponse:
    return LessonBlocksResponse(blocks=service.save_version(db, lesson_id, form, user, data))


@files_router.post("", status_code=status.HTTP_201_CREATED)
def upload_file(file: UploadFile, db: DbSession, user: TeacherUser) -> UploadedFileResponse:
    saved = service.save_upload(db, user, file.filename or "", file.file)
    return service.file_response(saved)


@files_router.get("/{file_id}")
def download_file(file_id: int, db: DbSession, _user: CurrentUser) -> FileResponse:
    file = service.get_file(db, file_id)
    # inline: shown in <img>, <video>, <audio> and the PDF viewer; Range requests let video seek
    return FileResponse(
        service.file_path(file),
        media_type=file.content_type,
        filename=file.original_name,
        content_disposition_type="inline",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=3600"},
    )
