"""Demo data for the presentation (idempotent; never deletes anyone else's data).

Run from `backend/` (uploads go to UPLOAD_DIR, relative to it):

    python -m app.demo.seed                    # create what is missing
    python -m app.demo.seed --reset-students   # also clear survey/quiz data of demo students
    python -m app.demo.seed --refresh-demo-media  # upload demo MP3/MP4 again (after re-recording)

Creates: a teacher with three courses (math, English, Python) whose lessons have
V / A / K / mixed materials; a student without the survey (to show the redirect); a student
with a survey and quiz results whose profile shows a proposal to switch the learning style;
the teacher's classroom with both students and the Python course, which is private (it is
not in the catalog, the students of the classroom see it in the classroom).
"""

import argparse
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.demo.courses import (
    COURSES,
    PYTHON,
    QUIZZES,
    Block,
    Course,
    Image,
    Pdf,
    Speech,
    Text,
    Video,
    doc,
    speech_file,
)
from app.modules.assessment import service as assessment
from app.modules.assessment.models import LessonQuiz
from app.modules.assessment.schemas import QuizContent
from app.modules.content import service as content
from app.modules.content.blocks import LessonBlocks
from app.modules.curriculum import classrooms
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Classroom, Lesson
from app.modules.curriculum.models import Course as CourseModel
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
# The demo classroom: both demo students and the Python course, made private when the
# classroom is created (it leaves the catalog and stays available in the classroom)
CLASSROOM_NAME = "Klasa 7a"
CLASSROOM_COURSE = PYTHON.title


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


def _block(
    db: Session, teacher: User, block: Block, audio_file: str | None = None
) -> dict[str, Any]:
    """Block as saved by the content module; `audio_file` = MP3 of a Speech block."""
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
    # The content module accepts a file OR a transcript; demo audio is a recorded MP3
    assert audio_file is not None, block.id
    return common | {"kind": "audio", "file_id": _upload(db, teacher, audio_file)}


def find_course(db: Session, teacher: User, title: str) -> CourseModel | None:
    return db.scalar(
        select(CourseModel).where(
            CourseModel.owner_id == teacher.id,
            CourseModel.title == title,
            CourseModel.is_archived.is_(False),
        )
    )


MEDIA_KINDS = {Speech: "audio", Video: "video"}


def _is_demo_media(block: Block, stored: dict[str, Any]) -> bool:
    """A stored block that is our demo audio/video (same id and kind), safe to replace."""
    kind = MEDIA_KINDS.get(type(block))
    return kind is not None and stored.get("type") == "attachment" and stored.get("kind") == kind


def ensure_blocks(
    db: Session,
    teacher: User,
    course: Course,
    lesson_index: int,
    lesson: Lesson,
    refresh_media: bool = False,
) -> None:
    """Add demo blocks missing in the lesson (by id); other blocks are kept as they are.

    With `refresh_media`, demo audio and video blocks are uploaded again from `assets/`
    (e.g. after re-recording). Blocks added by the teacher are never touched.
    """
    data = course.lessons[lesson_index]
    stored = {block["id"]: block for block in content.get_blocks(db, lesson.id, teacher)}
    rebuild = [
        block
        for block in data.blocks
        if block.id not in stored or (refresh_media and _is_demo_media(block, stored[block.id]))
    ]
    if not rebuild:
        return
    rebuilt_ids = {block.id for block in rebuild}

    def build(block: Block) -> dict[str, Any]:
        if block.id not in rebuilt_ids:
            return stored[block.id]
        audio = speech_file(course, lesson_index, block) if isinstance(block, Speech) else None
        return _block(db, teacher, block, audio)

    wanted = {block.id for block in data.blocks}
    blocks = [build(block) for block in data.blocks]
    blocks += [block for block_id, block in stored.items() if block_id not in wanted]
    content.save_blocks(db, lesson.id, teacher, LessonBlocks.model_validate({"blocks": blocks}))
    added = [b.id for b in rebuild if b.id not in stored]
    refreshed = [b.id for b in rebuild if b.id in stored]
    if added:
        log(f"  {lesson.title}: dodano bloki {', '.join(added)}")
    if refreshed:
        log(f"  {lesson.title}: odświeżono media {', '.join(refreshed)}")


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


def ensure_course(
    db: Session, teacher: User, data: Course, refresh_media: bool = False
) -> CourseModel:
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
    for lesson_index, lesson_data in enumerate(data.lessons):
        lessons = {lesson.title: lesson for lesson in curriculum.active_lessons(course)}
        lesson = lessons.get(lesson_data.title)
        if lesson is None:
            lesson = curriculum.create_lesson(db, course.id, teacher, lesson_data.title)
            db.refresh(course, ["lessons"])
        ensure_blocks(db, teacher, data, lesson_index, lesson, refresh_media)
        ensure_quiz(db, teacher, lesson)
    if created:
        curriculum.update_course(
            db,
            course.id,
            teacher,
            CourseUpdateRequest(is_published=True, introduction=doc(*data.introduction)),
        )
    return course


# --- Classroom -----------------------------------------------------------------------------------


def find_classroom(db: Session, teacher: User) -> Classroom | None:
    return db.scalar(
        select(Classroom).where(
            Classroom.teacher_id == teacher.id, Classroom.name == CLASSROOM_NAME
        )
    )


def ensure_classroom(db: Session, teacher: User, students: list[User]) -> Classroom:
    """Create the demo classroom if missing; in any case add missing students and the course.

    The course is made private only when the classroom is created, so a teacher who
    publishes it again during the presentation keeps it published on the next run.
    """
    course = find_course(db, teacher, CLASSROOM_COURSE)
    assert course is not None, CLASSROOM_COURSE
    classroom = find_classroom(db, teacher)
    if classroom is None:
        classroom = classrooms.create_classroom(db, teacher, CLASSROOM_NAME)
        curriculum.update_course(db, course.id, teacher, CourseUpdateRequest(is_published=False))
        log(f"utworzono klasę: {CLASSROOM_NAME} (kurs prywatny: {course.title})")
    else:
        log(f"klasa istnieje: {CLASSROOM_NAME}")
    for student in students:
        classrooms.add_student(db, classroom.id, teacher, student.id)
    classrooms.assign_course(db, classroom.id, teacher, course.id)
    log(f"  uczniowie: {', '.join(student.email for student in students)}; kurs: {course.title}")
    return classroom


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
    parser.add_argument(
        "--refresh-demo-media",
        action="store_true",
        help="upload the demo audio (MP3) and video blocks again from app/demo/assets",
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
            ensure_course(db, teacher, course, refresh_media=args.refresh_demo_media)
        print("Klasa:")
        ensure_classroom(db, teacher, [new_student, visual_student])
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
