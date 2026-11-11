from pathlib import Path

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.demo import seed
from app.demo.courses import COURSES, speech_blocks
from app.modules.assessment.models import LessonQuiz
from app.modules.content import service as content
from app.modules.content.blocks import LessonBlocks
from app.modules.content.models import File
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import ClassroomCourse, ClassroomStudent, Course
from app.modules.curriculum.schemas import CourseUpdateRequest
from app.modules.learning_style import service as learning_style
from app.modules.learning_style.models import LearningProfile, QuizAttempt


@pytest.fixture(autouse=True)
def upload_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setattr(get_settings(), "upload_dir", tmp_path / "uploads")
    return tmp_path / "uploads"


def _run(db: Session) -> tuple:
    teacher = seed.ensure_user(db, seed.TEACHER)
    new_student = seed.ensure_user(db, seed.NEW_STUDENT)
    student = seed.ensure_user(db, seed.VISUAL_STUDENT)
    for course in COURSES:
        seed.ensure_course(db, teacher, course)
    seed.ensure_classroom(db, teacher, [new_student, student])
    seed.ensure_visual_student(db, student, teacher)
    return teacher, new_student, student


def _count(db: Session, model, *where) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*where))


def test_seed_creates_courses_with_files(db: Session, upload_dir: Path):
    teacher, _, _ = _run(db)
    courses = db.scalars(select(Course).where(Course.owner_id == teacher.id)).all()
    assert {c.title for c in courses} == {c.title for c in COURSES}
    # Published, except the course of the demo classroom
    assert {c.title for c in courses if not c.is_published} == {seed.CLASSROOM_COURSE}
    files = _count(db, File, File.owner_id == teacher.id)
    assert files > 0
    assert len(list(upload_dir.iterdir())) == files


def test_seed_adds_quiz_to_every_lesson_and_videos(db: Session):
    teacher, _, _ = _run(db)
    lessons = [
        lesson
        for course in db.scalars(select(Course).where(Course.owner_id == teacher.id))
        for lesson in course.lessons
    ]
    assert len(lessons) == sum(len(c.lessons) for c in COURSES)
    assert _count(
        db, LessonQuiz, LessonQuiz.lesson_id.in_([lesson.id for lesson in lessons])
    ) == len(lessons)
    videos = [
        block
        for lesson in lessons
        for block in content.get_blocks(db, lesson.id, teacher)
        if block.get("kind") == "video"
    ]
    assert len(videos) == 2
    assert all(video["forms"] == ["V", "A"] for video in videos)


def test_seed_adds_missing_parts_to_an_existing_course(db: Session):
    teacher, _, _ = _run(db)
    lesson = db.scalars(select(Course).where(Course.owner_id == teacher.id)).first().lessons[0]
    db.execute(delete(LessonQuiz).where(LessonQuiz.lesson_id == lesson.id))
    db.commit()
    _run(db)
    assert _count(db, LessonQuiz, LessonQuiz.lesson_id == lesson.id) == 1


def _first_math_lesson(db: Session, teacher):
    course = seed.find_course(db, teacher, COURSES[0].title)
    return course.lessons[0]


def test_demo_audio_blocks_are_mp3_files(db: Session):
    teacher, _, _ = _run(db)
    audio = [
        block
        for course in db.scalars(select(Course).where(Course.owner_id == teacher.id))
        for lesson in course.lessons
        for block in content.get_blocks(db, lesson.id, teacher)
        if block.get("kind") == "audio"
    ]
    assert len(audio) == sum(len(speech_blocks(c)) for c in COURSES)
    assert all(block["file_name"].endswith(".mp3") and "transcript" not in block for block in audio)
    assert all(block["forms"][0] == "A" for block in audio)


def test_refresh_replaces_old_demo_audio_and_keeps_teacher_blocks(db: Session):
    teacher, _, _ = _run(db)
    lesson = _first_math_lesson(db, teacher)
    blocks = content.get_blocks(db, lesson.id, teacher)
    # Old version of the demo: audio read by the browser + a block added by the teacher
    for block in blocks:
        if block["id"] == "a-wyjasnienie":
            block.pop("file_id")
            block["transcript"] = "Stara wersja czytana przez przeglądarkę."
    own = {"id": "moj-link", "type": "attachment", "kind": "link", "forms": ["K"],
           "title": "Mój link", "url": "https://example.com"}  # fmt: skip
    content.save_blocks(
        db, lesson.id, teacher, LessonBlocks.model_validate({"blocks": [*blocks, own]})
    )

    seed.ensure_course(db, teacher, COURSES[0])  # without the flag nothing is replaced
    stored = {b["id"]: b for b in content.get_blocks(db, lesson.id, teacher)}
    assert "transcript" in stored["a-wyjasnienie"]

    seed.ensure_course(db, teacher, COURSES[0], refresh_media=True)
    stored = {b["id"]: b for b in content.get_blocks(db, lesson.id, teacher)}
    assert "transcript" not in stored["a-wyjasnienie"]
    assert stored["a-wyjasnienie"]["file_name"] == "m1_a-wyjasnienie.mp3"
    assert stored["va-film"]["title"] == "Film: funkcja liniowa w skrócie"
    assert stored["moj-link"]["url"] == "https://example.com"
    assert list(stored)[-1] == "moj-link"


def test_seed_student_has_proposal_and_new_student_has_no_survey(db: Session):
    _, new_student, student = _run(db)
    assert db.get(LearningProfile, new_student.id) is None
    profile = learning_style.profile_response(db, student)
    assert profile.style == "V"
    assert profile.weights == {"V": 7, "A": 8, "K": 3}
    assert profile.proposal is not None and profile.proposal.style == "A"


def test_seed_classroom_has_both_students_and_the_private_course(db: Session):
    teacher, new_student, student = _run(db)
    classroom = seed.find_classroom(db, teacher)
    assert classroom is not None
    course = seed.find_course(db, teacher, seed.CLASSROOM_COURSE)
    members = db.scalars(
        select(ClassroomStudent.student_id).where(ClassroomStudent.classroom_id == classroom.id)
    ).all()
    assert set(members) == {new_student.id, student.id}
    assert db.scalars(
        select(ClassroomCourse.course_id).where(ClassroomCourse.classroom_id == classroom.id)
    ).all() == [course.id]
    # Not in the catalog, but open to the students of the classroom
    assert course.id not in {c.id for c in curriculum.list_courses(db, student)}
    assert curriculum.get_visible_course(db, course.id, student).id == course.id


def test_seed_keeps_the_classroom_course_published_again_by_the_teacher(db: Session):
    teacher, _, _ = _run(db)
    course = seed.find_course(db, teacher, seed.CLASSROOM_COURSE)
    curriculum.update_course(db, course.id, teacher, CourseUpdateRequest(is_published=True))
    _run(db)
    db.refresh(course)
    assert course.is_published


def test_seed_is_idempotent(db: Session):
    teacher, _, student = _run(db)
    files = _count(db, File, File.owner_id == teacher.id)
    _run(db)
    assert _count(db, Course, Course.owner_id == teacher.id) == len(COURSES)
    assert _count(db, File, File.owner_id == teacher.id) == files
    assert _count(db, QuizAttempt, QuizAttempt.user_id == student.id) == len(seed.VISUAL_QUIZZES)
    classroom = seed.find_classroom(db, teacher)
    assert _count(db, ClassroomStudent, ClassroomStudent.classroom_id == classroom.id) == 2
    assert _count(db, ClassroomCourse, ClassroomCourse.classroom_id == classroom.id) == 1


def test_reset_clears_only_learning_data(db: Session):
    _, _, student = _run(db)
    seed.reset_student(db, student)
    assert db.get(LearningProfile, student.id) is None
    assert _count(db, QuizAttempt, QuizAttempt.user_id == student.id) == 0
    assert seed.ensure_user(db, seed.VISUAL_STUDENT).id == student.id
