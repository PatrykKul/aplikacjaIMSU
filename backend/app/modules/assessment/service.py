from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.assessment.models import LessonQuiz
from app.modules.assessment.schemas import QuizContent, QuizEditResponse, QuizQuestion
from app.modules.curriculum import service as curriculum
from app.modules.identity.models import User


def _quiz(db: Session, lesson_id: int) -> LessonQuiz | None:
    return db.scalar(select(LessonQuiz).where(LessonQuiz.lesson_id == lesson_id))


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
