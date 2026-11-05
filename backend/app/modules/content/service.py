from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.content.answers import (
    AnswerNotANumberError,
    CheckResult,
    InvalidChoiceError,
    check_answer,
)
from app.modules.content.models import Lesson
from app.modules.content.schemas import (
    ChoiceAnswerResponse,
    LessonResponse,
    NumberAnswerResponse,
    QuestionStepResponse,
    TextStepResponse,
)
from app.modules.content.steps import ChoiceAnswer, LessonSteps, QuestionStep, TextStep
from app.modules.curriculum import service as curriculum_service
from app.modules.identity.models import User


def get_skill_lesson(db: Session, skill_id: int, user: User) -> Lesson:
    if not curriculum_service.is_skill_visible(db, skill_id, user):
        raise AppError(404, "SKILL_NOT_FOUND")
    lesson = db.scalar(
        select(Lesson).where(Lesson.skill_id == skill_id, Lesson.is_archived.is_(False))
    )
    if lesson is None:
        raise AppError(404, "LESSON_NOT_FOUND")
    return lesson


def get_lesson(db: Session, lesson_id: int, user: User) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if (
        lesson is None
        or lesson.is_archived
        or not curriculum_service.is_skill_visible(db, lesson.skill_id, user)
    ):
        raise AppError(404, "LESSON_NOT_FOUND")
    return lesson


def check_step(
    db: Session, lesson_id: int, step_key: str, answer: str | int, reveal: bool, user: User
) -> CheckResult:
    step = _steps(get_lesson(db, lesson_id, user)).find(step_key)
    if step is None:
        raise AppError(404, "STEP_NOT_FOUND")
    if not isinstance(step, QuestionStep):
        raise AppError(400, "STEP_NOT_A_QUESTION")
    try:
        return check_answer(step, answer, reveal=reveal)
    except AnswerNotANumberError:
        raise AppError(400, "ANSWER_NOT_A_NUMBER") from None
    except InvalidChoiceError:
        raise AppError(400, "INVALID_CHOICE") from None


def lesson_response(lesson: Lesson) -> LessonResponse:
    return LessonResponse(
        id=lesson.id,
        skill_id=lesson.skill_id,
        title=lesson.title,
        steps=[_step_response(step) for step in _steps(lesson).steps],
    )


def _steps(lesson: Lesson) -> LessonSteps:
    return LessonSteps.model_validate({"steps": lesson.steps})


def _step_response(step: TextStep | QuestionStep) -> TextStepResponse | QuestionStepResponse:
    if isinstance(step, TextStep):
        return TextStepResponse(key=step.key, body=step.body)
    if isinstance(step.answer, ChoiceAnswer):
        answer = ChoiceAnswerResponse(options=[option.text for option in step.answer.options])
    else:
        answer = NumberAnswerResponse(unit=step.answer.unit)
    return QuestionStepResponse(key=step.key, prompt=step.prompt, hint=step.hint, answer=answer)
