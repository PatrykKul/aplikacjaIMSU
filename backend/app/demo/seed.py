"""Demo data for the presentation (idempotent; never deletes anyone else's data).

Run from `backend/` (uploads go to UPLOAD_DIR, relative to it):

    python -m app.demo.seed                    # create what is missing
    python -m app.demo.seed --reset-students   # also clear survey/quiz data of demo students

Creates: a teacher with three published courses (math, English, Python) whose lessons have
V / A / K / mixed materials; a student without the survey (to show the redirect); a student
with a survey and quiz results whose profile shows a proposal to switch the learning style.
"""

import argparse
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.demo.courses import COURSES, QUIZZES, Block, Course, Image, Pdf, Text, Video, doc
from app.demo.courses import Lesson as LessonData
from app.modules.assessment import service as assessment
from app.modules.assessment.models import LessonQuiz
from app.modules.assessment.schemas import QuizContent
from app.modules.content import service as content
from app.modules.content.blocks import LessonBlocks
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Course as CourseModel
from app.modules.curriculum.models import Lesson
from app.modules.curriculum.schemas import CourseCreateRequest, CourseUpdateRequest
from app.modules.identity import service as identity
from app.modules.identity.models import User, UserRole
from app.modules.learning_style import service as learning_style
from app.modules.learning_style.hooks import record_quiz_result
from app.modules.learning_style.models import (
    LearningProfile,
    QuizAttempt,
    SurveyAnswer,
    SurveyResult,
)
from app.modules.learning_style.schemas import SurveyChoice

ASSETS = Path(__file__).resolve().parent / "assets"
PASSWORD = "Demo123!"

TEACHER = ("nauczyciel.demo@imsu.pl", "Anna Nowak", UserRole.TEACHER)
ADMIN = ("admin.demo@imsu.pl", "Adam Admin", UserRole.ADMIN)
NEW_STUDENT = ("uczen.nowy@imsu.pl", "Ola Kowalska", UserRole.STUDENT)
VISUAL_STUDENT = ("uczen.demo@imsu.pl", "Kuba Wiśniewski", UserRole.STUDENT)

# Survey of the demo student: answers per style (20 questions) -> V 9 / A 8 / K 3, style V
VISUAL_SURVEY = "V" * 9 + "A" * 8 + "K" * 3
# Quiz results in the first lessons: one pass, three failures -> weights V 7 / A 8 / K 3,
# so the auditory style leads and the profile shows a proposal to switch
VISUAL_QUIZZES = (
    ("Matematyka: funkcja liniowa", 0, 85),
    ("Matematyka: funkcja liniowa", 1, 55),
    ("Matematyka: funkcja liniowa", 2, 40),
    ("Angielski: Present Perfect", 0, 45),
)


def log(message: str) -> None:
    print(f"  {message}")


# --- Users ---------------------------------------------------------------------------------------


def ensure_user(db: Session, account: tuple[str, str, UserRole]) -> User:
    email, name, role = account
    user = identity.get_by_email(db, email)
    if user is not None:
        log(f"konto istnieje: {email}")
        if user.display_name != name:  # demo accounts only; the password is left alone
            user.display_name = name
            db.commit()
        return user
    user = identity.create_user(db, email=email, password=PASSWORD, display_name=name, role=role)
    log(f"utworzono konto: {email} ({role.value})")
    return user


# --- Courses -------------------------------------------------------------------------------------


def _upload(db: Session, teacher: User, name: str) -> int:
    with (ASSETS / name).open("rb") as stream:
        return content.save_upload(db, teacher, name, stream).id


def _block(db: Session, teacher: User, block: Block) -> dict[str, Any]:
    if isinstance(block, Text):
        return {"id": block.id, "type": "text", "doc": doc(*block.nodes)}
    common = {
        "id": block.id,
        "type": "attachment",
        "forms": list(block.forms),
        "title": block.title,
        "description": block.description,
    }
    if isinstance(block, Image):
        return common | {
            "kind": "image",
            "file_id": _upload(db, teacher, block.file),
            "alt": block.alt,
        }
    if isinstance(block, Pdf):
        return common | {"kind": "pdf", "file_id": _upload(db, teacher, block.file)}
    if isinstance(block, Video):
        return common | {"kind": "video", "file_id": _upload(db, teacher, block.file)}
    return common | {"kind": "audio", "transcript": block.transcript}


def find_course(db: Session, teacher: User, title: str) -> CourseModel | None:
    return db.scalar(
        select(CourseModel).where(
            CourseModel.owner_id == teacher.id,
            CourseModel.title == title,
            CourseModel.is_archived.is_(False),
        )
    )


def ensure_blocks(db: Session, teacher: User, lesson: Lesson, data: LessonData) -> None:
    """Add demo blocks missing in the lesson (by id); blocks already there are kept as they are."""
    stored = {block["id"]: block for block in content.get_blocks(db, lesson.id, teacher)}
    missing = [block for block in data.blocks if block.id not in stored]
    if not missing:
        return
    wanted = {block.id for block in data.blocks}
    blocks = [stored.get(b.id) or _block(db, teacher, b) for b in data.blocks]
    blocks += [block for block_id, block in stored.items() if block_id not in wanted]
    content.save_blocks(db, lesson.id, teacher, LessonBlocks.model_validate({"blocks": blocks}))
    log(f"  {lesson.title}: dodano bloki {', '.join(b.id for b in missing)}")


def ensure_quiz(db: Session, teacher: User, lesson: Lesson) -> None:
    questions = QUIZZES.get(lesson.title)
    if not questions or db.scalar(select(LessonQuiz.id).where(LessonQuiz.lesson_id == lesson.id)):
        return
    quiz = QuizContent.model_validate(
        {
            "questions": [
                {
                    "id": q.id,
                    "text": q.text,
                    "form": q.form,
                    "answers": [{"id": f"a{i}", "text": text} for i, text in enumerate(q.answers)],
                    "correct_answer_id": f"a{q.correct}",
                }
                for q in questions
            ]
        }
    )
    assessment.save_quiz(db, lesson.id, teacher, quiz)
    log(f"  {lesson.title}: dodano quiz ({len(questions)} pytań)")


def ensure_course(db: Session, teacher: User, data: Course) -> CourseModel:
    """Create the course if missing; in any case add missing lessons, blocks and quizzes."""
    course = find_course(db, teacher, data.title)
    created = course is None
    if course is None:
        course = curriculum.create_course(
            db, teacher, CourseCreateRequest(title=data.title, description=data.description)
        )
        log(f"utworzono kurs: {data.title}")
    else:
        log(f"kurs istnieje: {data.title}")
    for lesson_data in data.lessons:
        lessons = {lesson.title: lesson for lesson in curriculum.active_lessons(course)}
        lesson = lessons.get(lesson_data.title)
        if lesson is None:
            lesson = curriculum.create_lesson(db, course.id, teacher, lesson_data.title)
            db.refresh(course, ["lessons"])
        ensure_blocks(db, teacher, lesson, lesson_data)
        ensure_quiz(db, teacher, lesson)
    if created:
        curriculum.update_course(
            db,
            course.id,
            teacher,
            CourseUpdateRequest(is_published=True, introduction=doc(*data.introduction)),
        )
    return course


# --- Students ------------------------------------------------------------------------------------


def reset_student(db: Session, user: User) -> None:
    for model in (QuizAttempt, SurveyResult):
        db.execute(delete(model).where(model.user_id == user.id))
    db.execute(delete(LearningProfile).where(LearningProfile.user_id == user.id))
    db.commit()
    log(f"wyczyszczono ankietę i quizy: {user.email}")


def _survey_choices(db: Session, styles: str) -> list[SurveyChoice]:
    questions = learning_style.active_questions(db)
    choices = []
    for question, style in zip(questions, styles, strict=True):
        answer = next(a for a in question.answers if a.style == style)
        choices.append(SurveyChoice(question_id=question.id, answer_id=answer.id))
    return choices


def _lesson(db: Session, teacher: User, course_title: str, index: int) -> Lesson:
    course = find_course(db, teacher, course_title)
    assert course is not None, course_title
    return curriculum.active_lessons(course)[index]


def ensure_visual_student(db: Session, student: User, teacher: User) -> None:
    if db.get(LearningProfile, student.id) is None:
        learning_style.submit_survey(db, student, _survey_choices(db, VISUAL_SURVEY))
        log(f"wypełniono ankietę: {student.email} (V 9 / A 8 / K 3)")
    has_quizzes = db.scalar(select(QuizAttempt.id).where(QuizAttempt.user_id == student.id))
    if has_quizzes is None:
        for course_title, index, percent in VISUAL_QUIZZES:
            lesson = _lesson(db, teacher, course_title, index)
            record_quiz_result(
                db, user=student, lesson_id=lesson.id, block_id="demo-quiz", percent=percent
            )
            log(f"wynik quizu: {lesson.title} – {percent}%")
    profile = learning_style.profile_response(db, student)
    weights = profile.weights or {}
    log(
        f"profil {student.email}: styl {profile.style}, wagi V {weights.get('V')} / "
        f"A {weights.get('A')} / K {weights.get('K')}, propozycja: "
        f"{profile.proposal.style if profile.proposal else 'brak'}"
    )


def ensure_survey_answers_exist(db: Session) -> None:
    if db.scalar(select(SurveyAnswer.id).limit(1)) is None:
        raise SystemExit("Brak pytań ankiety – najpierw uruchom: python -m alembic upgrade head")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.demo.seed", description=__doc__)
    parser.add_argument(
        "--reset-students",
        action="store_true",
        help="clear survey and quiz data of the demo students before seeding",
    )
    args = parser.parse_args(argv)

    with SessionLocal() as db:
        ensure_survey_answers_exist(db)
        print("Konta:")
        teacher = ensure_user(db, TEACHER)
        ensure_user(db, ADMIN)
        new_student = ensure_user(db, NEW_STUDENT)
        visual_student = ensure_user(db, VISUAL_STUDENT)
        print("Kursy:")
        for course in COURSES:
            ensure_course(db, teacher, course)
        print("Uczniowie:")
        if args.reset_students:
            reset_student(db, new_student)
            reset_student(db, visual_student)
        if db.get(LearningProfile, new_student.id) is not None:
            log(f"uwaga: {new_student.email} ma już ankietę (użyj --reset-students)")
        ensure_visual_student(db, visual_student, teacher)
    print(f"Gotowe. Hasło wszystkich kont demo: {PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
