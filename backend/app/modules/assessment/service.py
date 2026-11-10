from collections.abc import Mapping
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.assessment.grading import GradingError, grade, visible_questions
from app.modules.assessment.models import LessonQuiz
from app.modules.assessment.schemas import (
    AttemptResponse,
    QuestionResult,
    QuizContent,
    QuizEditResponse,
    QuizQuestion,
    StudentQuestion,
    StudentQuizResponse,
)
from app.modules.curriculum import service as curriculum
from app.modules.identity.models import User, UserRole
from app.modules.learning_style import service as learning_style
from app.modules.learning_style.hooks import record_quiz_result


def _quiz(db: Session, lesson_id: int) -> LessonQuiz | None:
    return db.scalar(select(LessonQuiz).where(LessonQuiz.lesson_id == lesson_id))


def _style_filter(db: Session, user: User, lesson_id: int) -> str | None:
    """A student's effective style in the lesson (survey required); None = no filtering."""
    if user.role != UserRole.STUDENT:
        return None
    profile = learning_style.require_profile(db, user)
    return learning_style.lesson_style(db, profile, lesson_id)


def _questions_for(
    db: Session, lesson_id: int, user: User
) -> tuple[LessonQuiz, list[Mapping[str, Any]], int]:
    curriculum.get_visible_lesson(db, lesson_id, user)
    quiz = _quiz(db, lesson_id)
    if quiz is None:
        raise AppError(404, "QUIZ_NOT_FOUND")
    visible = visible_questions(quiz.questions, _style_filter(db, user, lesson_id))
    if not visible:
        raise AppError(404, "QUIZ_NOT_FOUND")
    return quiz, visible, len(quiz.questions) - len(visible)


# --- Student -------------------------------------------------------------------------------------


def student_quiz(db: Session, lesson_id: int, user: User) -> StudentQuizResponse:
    _, questions, hidden = _questions_for(db, lesson_id, user)
    return StudentQuizResponse(
        questions=[StudentQuestion.model_validate(q) for q in questions], hidden_count=hidden
    )


def submit_attempt(
    db: Session, lesson_id: int, user: User, answers: Mapping[str, str]
) -> AttemptResponse:
    """Score on the server, then let the adaptation update the student's style weights."""
    quiz, questions, _ = _questions_for(db, lesson_id, user)
    try:
        graded = grade(questions, answers)
    except GradingError as error:
        raise AppError(400, error.code) from None
    feedback = record_quiz_result(
        db, user=user, lesson_id=lesson_id, block_id=f"quiz-{quiz.id}", percent=graded.percent
    )
    return AttemptResponse(
        percent=graded.percent,
        correct_count=graded.correct_count,
        total=graded.total,
        results=[QuestionResult.model_validate(result) for result in graded.results],
        adaptation=feedback,
    )


# --- Teacher -------------------------------------------------------------------------------------


def quiz_for_editing(db: Session, lesson_id: int, user: User) -> QuizEditResponse:
    curriculum.get_owned_lesson(db, lesson_id, user)
    quiz = _quiz(db, lesson_id)
    questions = [] if quiz is None else [QuizQuestion.model_validate(q) for q in quiz.questions]
    return QuizEditResponse(questions=questions)


def save_quiz(db: Session, lesson_id: int, user: User, data: QuizContent) -> QuizEditResponse:
    curriculum.get_owned_lesson(db, lesson_id, user)
    questions = [question.model_dump() for question in data.questions]
    quiz = _quiz(db, lesson_id)
    if quiz is None:
        db.add(LessonQuiz(lesson_id=lesson_id, questions=questions))
    else:
        quiz.questions = questions
    db.commit()
    return QuizEditResponse(questions=data.questions)


def delete_quiz(db: Session, lesson_id: int, user: User) -> None:
    curriculum.get_owned_lesson(db, lesson_id, user)
    quiz = _quiz(db, lesson_id)
    if quiz is not None:
        db.delete(quiz)
        db.commit()
