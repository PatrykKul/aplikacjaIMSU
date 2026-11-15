import random
from collections.abc import Collection
from dataclasses import asdict
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.assessment import stats
from app.modules.assessment.drawing import draw_questions
from app.modules.assessment.grading import GradingError, grade
from app.modules.assessment.models import LessonQuiz, QuizDraw
from app.modules.assessment.readiness import quiz_issues
from app.modules.assessment.schemas import (
    AttemptResponse,
    LessonQuestionStatsResponse,
    QuestionResultResponse,
    QuestionStatsRowResponse,
    QuizContent,
    QuizEditResponse,
    QuizQuestion,
    ReviewQuestionResponse,
    StudentQuestionResponse,
    StudentQuizResponse,
)
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Lesson
from app.modules.identity.models import User, UserRole
from app.modules.learning_style import hooks
from app.modules.learning_style import service as learning_style
from app.modules.learning_style.rules import QUIZ_SIZE

# Random source of the draws; tests may replace it with a seeded `random.Random`
rng = random.Random()


def _quiz(db: Session, lesson_id: int) -> LessonQuiz | None:
    return db.scalar(select(LessonQuiz).where(LessonQuiz.lesson_id == lesson_id))


# --- Teacher -------------------------------------------------------------------------------------


def quiz_for_editing(db: Session, lesson_id: int, user: User) -> QuizEditResponse:
    """The pool with the key: the author edits it, the admin reads it."""
    if user.role == UserRole.ADMIN:
        curriculum.get_visible_lesson(db, lesson_id, user)
    elif user.role == UserRole.TEACHER:
        curriculum.get_owned_lesson(db, lesson_id, user)
    else:
        raise AppError(403, "FORBIDDEN")
    quiz = _quiz(db, lesson_id)
    questions = [] if quiz is None else [QuizQuestion.model_validate(q) for q in quiz.questions]
    return QuizEditResponse(questions=questions)


def _check_published(lesson: Lesson, question_count: int) -> None:
    """A published lesson must keep a full pool: unpublish it first (R11)."""
    issues = quiz_issues(question_count)
    if lesson.is_published and issues:
        raise AppError(409, "PUBLISHED_LESSON_INCOMPLETE", issues=issues)


def save_quiz(db: Session, lesson_id: int, user: User, data: QuizContent) -> QuizEditResponse:
    lesson = curriculum.get_owned_lesson(db, lesson_id, user)
    _check_published(lesson, len(data.questions))
    questions = [question.model_dump() for question in data.questions]
    quiz = _quiz(db, lesson_id)
    if quiz is None:
        db.add(LessonQuiz(lesson_id=lesson_id, questions=questions))
    else:
        quiz.questions = questions
    db.commit()
    return QuizEditResponse(questions=data.questions)


def delete_quiz(db: Session, lesson_id: int, user: User) -> None:
    lesson = curriculum.get_owned_lesson(db, lesson_id, user)
    _check_published(lesson, 0)
    quiz = _quiz(db, lesson_id)
    if quiz is not None:
        db.delete(quiz)
        db.commit()


def question_count(db: Session, lesson_id: int) -> int:
    """For authoring: size of the lesson's question pool (0 without a quiz)."""
    quiz = _quiz(db, lesson_id)
    return 0 if quiz is None else len(quiz.questions)


# --- Student: drawing ----------------------------------------------------------------------------


def _student_lesson(db: Session, lesson_id: int, user: User) -> tuple[Lesson, str]:
    """(lesson, active style): survey done, enrolled, lesson unlocked (403 otherwise)."""
    profile = learning_style.require_style(db, user)
    assert profile.style is not None
    return curriculum.get_study_lesson(db, lesson_id, user), profile.style


def _pool(db: Session, lesson_id: int) -> dict[str, dict[str, Any]]:
    quiz = _quiz(db, lesson_id)
    if quiz is None or not quiz.questions:
        raise AppError(404, "QUIZ_NOT_FOUND")
    return {question["id"]: question for question in quiz.questions}


def _draws(db: Session, user_id: int, lesson_id: int) -> list[QuizDraw]:
    """The student's draws in the lesson, newest first."""
    return list(
        db.scalars(
            select(QuizDraw)
            .where(QuizDraw.user_id == user_id, QuizDraw.lesson_id == lesson_id)
            .order_by(QuizDraw.id.desc())
        )
    )


def _lesson_form(db: Session, user: User, lesson: Lesson) -> str:
    profile = learning_style.require_style(db, user)
    assert profile.style is not None
    form, _ = learning_style.lesson_form(db, user.id, lesson.id, profile.style)
    return form


def current_draw(db: Session, user: User, lesson: Lesson) -> QuizDraw:
    """The open draw (a page refresh keeps the questions) or a new one (R9).

    A new draw prefers questions outside the last submitted set. An open draw whose questions
    are no longer in the pool (the teacher edited it) or drawn in another form than the
    lesson's form now (D61) is replaced.
    """
    pool = _pool(db, lesson.id)
    form = _lesson_form(db, user, lesson)
    draws = _draws(db, user.id, lesson.id)
    open_draw = next((d for d in draws if d.submitted_at is None), None)
    if open_draw is not None:
        same_form = open_draw.form is None or open_draw.form == form
        if same_form and all(qid in pool for qid in open_draw.question_ids):
            return open_draw
        db.delete(open_draw)
    last = next((d for d in draws if d.submitted_at is not None), None)
    draw = QuizDraw(
        user_id=user.id,
        lesson_id=lesson.id,
        form=form,
        question_ids=draw_questions(
            list(pool), [] if last is None else last.question_ids, QUIZ_SIZE, rng
        ),
    )
    db.add(draw)
    db.commit()
    return draw


def student_quiz(db: Session, lesson_id: int, user: User) -> StudentQuizResponse:
    """Questions of the current draw without the key."""
    lesson, _ = _student_lesson(db, lesson_id, user)
    draw = current_draw(db, user, lesson)
    pool = _pool(db, lesson.id)
    return StudentQuizResponse(
        draw_id=draw.id,
        questions=[StudentQuestionResponse.model_validate(pool[qid]) for qid in draw.question_ids],
        pool_size=len(pool),
        form=_lesson_form(db, user, lesson),
    )


# --- Student: submitting -------------------------------------------------------------------------


def submit_attempt(
    db: Session, lesson_id: int, user: User, draw_id: int, answers: dict[str, str]
) -> AttemptResponse:
    """Grade the answers against the drawn set and pass the score to the student model."""
    lesson, _ = _student_lesson(db, lesson_id, user)
    draw = db.get(QuizDraw, draw_id)
    if (
        draw is None
        or draw.user_id != user.id
        or draw.lesson_id != lesson.id
        or draw.submitted_at is not None
    ):
        raise AppError(409, "DRAW_NOT_OPEN")
    pool = _pool(db, lesson.id)
    if not all(qid in pool for qid in draw.question_ids):
        # The pool changed after the draw: the set cannot be graded, the next GET draws again
        db.delete(draw)
        db.commit()
        raise AppError(409, "DRAW_NOT_OPEN")
    questions = [pool[qid] for qid in draw.question_ids]
    try:
        graded = grade(questions, answers)
    except GradingError as error:
        raise AppError(400, error.code) from None

    draw.answers = dict(answers)
    draw.percent = graded.percent
    draw.submitted_at = learning_style.now()
    db.flush()
    feedback = hooks.record_quiz_result(
        db, user=user, lesson=lesson, draw_id=draw.id, percent=graded.percent
    )
    return AttemptResponse(
        draw_id=draw_id,
        percent=graded.percent,
        correct_count=graded.correct_count,
        total=graded.total,
        passed=feedback.passed,
        results=[
            QuestionResultResponse(
                question_id=question["id"],
                text=question["text"],
                answers=question["answers"],
                chosen_answer_id=item["chosen_answer_id"],
                correct_answer_id=item["correct_answer_id"],
                correct=item["correct"],
                explanation=question["explanation"],
            )
            for question, item in zip(questions, graded.results, strict=True)
        ],
        feedback=feedback,
    )


# --- Statistics: questions to review (student), question analysis (author) ----------------------


def _pools(db: Session, lesson_ids: Collection[int]) -> dict[int, list[dict[str, Any]]]:
    if not lesson_ids:
        return {}
    quizzes = db.scalars(select(LessonQuiz).where(LessonQuiz.lesson_id.in_(lesson_ids)))
    return {quiz.lesson_id: list(quiz.questions) for quiz in quizzes}


def _submitted_draws(
    db: Session, lesson_ids: Collection[int], user_ids: Collection[int]
) -> list[stats.SubmittedDraw]:
    if not lesson_ids or not user_ids:
        return []
    rows = db.scalars(
        select(QuizDraw)
        .where(
            QuizDraw.lesson_id.in_(lesson_ids),
            QuizDraw.user_id.in_(user_ids),
            QuizDraw.submitted_at.is_not(None),
        )
        .order_by(QuizDraw.id)
    )
    return [
        stats.SubmittedDraw(
            draw_id=row.id,
            lesson_id=row.lesson_id,
            question_ids=tuple(row.question_ids),
            answers=row.answers or {},
            submitted_at=row.submitted_at,
        )
        for row in rows
        if row.submitted_at is not None
    ]


def review_questions(db: Session, user: User) -> list[ReviewQuestionResponse]:
    """ "To review": wrong answers of the last submitted draw of each lesson the student can
    still study (published lessons of the courses they are accepted in), newest first."""
    learning_style.require_student(user)
    lessons = []
    for course in curriculum.list_courses(db, user):
        if not curriculum.is_accepted(db, course.id, user.id):
            continue
        for number, lesson in enumerate(curriculum.published_lessons(course), 1):
            lessons.append(
                stats.LessonInfo(course.id, course.title, lesson.id, lesson.title, number)
            )
    ids = [lesson.lesson_id for lesson in lessons]
    found = stats.review_questions(lessons, _pools(db, ids), _submitted_draws(db, ids, [user.id]))
    return [ReviewQuestionResponse.model_validate(asdict(item)) for item in found]


def question_stats(db: Session, course_id: int, teacher: User) -> list[LessonQuestionStatsResponse]:
    """Question analysis of each published lesson, from the submitted draws of the students
    accepted in the course now."""
    course = curriculum.get_owned_course(db, course_id, teacher)
    lessons = curriculum.published_lessons(course)
    ids = [lesson.id for lesson in lessons]
    pools = _pools(db, ids)
    draws = _submitted_draws(db, ids, curriculum.accepted_student_ids(db, course.id))
    return [
        LessonQuestionStatsResponse(
            lesson_id=lesson.id,
            title=lesson.title,
            number=number,
            questions=[
                QuestionStatsRowResponse.model_validate(asdict(row))
                for row in stats.question_stats(
                    pools.get(lesson.id, []), [d for d in draws if d.lesson_id == lesson.id]
                )
            ],
        )
        for number, lesson in enumerate(lessons, 1)
    ]
