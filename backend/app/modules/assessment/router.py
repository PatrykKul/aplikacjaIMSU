from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.db import DbSession
from app.modules.assessment import service
from app.modules.assessment.schemas import (
    AttemptRequest,
    AttemptResponse,
    QuizContent,
    QuizEditResponse,
    StudentQuizResponse,
)
from app.modules.identity.dependencies import CurrentUser, TeacherUser, require_role
from app.modules.identity.models import User, UserRole

StudentUser = Annotated[User, Depends(require_role(UserRole.STUDENT))]

quiz_router = APIRouter(prefix="/lessons", tags=["assessment"])


# --- Teacher (the admin reads the pool) ----------------------------------------------------------


@quiz_router.get("/{lesson_id}/quiz/edit")
def get_quiz_for_editing(lesson_id: int, db: DbSession, user: CurrentUser) -> QuizEditResponse:
    return service.quiz_for_editing(db, lesson_id, user)


@quiz_router.put("/{lesson_id}/quiz")
def save_quiz(
    lesson_id: int, data: QuizContent, db: DbSession, user: TeacherUser
) -> QuizEditResponse:
    return service.save_quiz(db, lesson_id, user, data)


@quiz_router.delete("/{lesson_id}/quiz", status_code=status.HTTP_204_NO_CONTENT)
def delete_quiz(lesson_id: int, db: DbSession, user: TeacherUser) -> None:
    service.delete_quiz(db, lesson_id, user)


# --- Student -------------------------------------------------------------------------------------


@quiz_router.get("/{lesson_id}/quiz")
def get_quiz(lesson_id: int, db: DbSession, user: StudentUser) -> StudentQuizResponse:
    # Without the key: the response schema has no correct answers or explanations
    return service.student_quiz(db, lesson_id, user)


@quiz_router.post("/{lesson_id}/quiz/attempts")
def submit_attempt(
    lesson_id: int, data: AttemptRequest, db: DbSession, user: StudentUser
) -> AttemptResponse:
    return service.submit_attempt(db, lesson_id, user, data.draw_id, data.answers)
