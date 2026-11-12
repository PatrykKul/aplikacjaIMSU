from fastapi import APIRouter, status

from app.core.db import DbSession
from app.modules.assessment import service
from app.modules.assessment.schemas import (
    QuizContent,
    QuizEditResponse,
)
from app.modules.identity.dependencies import TeacherUser

quiz_router = APIRouter(prefix="/lessons", tags=["assessment"])


@quiz_router.get("/{lesson_id}/quiz/edit")
def get_quiz_for_editing(lesson_id: int, db: DbSession, user: TeacherUser) -> QuizEditResponse:
    return service.quiz_for_editing(db, lesson_id, user)


@quiz_router.put("/{lesson_id}/quiz")
def save_quiz(
    lesson_id: int, data: QuizContent, db: DbSession, user: TeacherUser
) -> QuizEditResponse:
    return service.save_quiz(db, lesson_id, user, data)


@quiz_router.delete("/{lesson_id}/quiz", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(lesson_id: int, db: DbSession, user: TeacherUser) -> None:
    service.delete_quiz(db, lesson_id, user)
