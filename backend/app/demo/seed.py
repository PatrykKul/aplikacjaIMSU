"""Demo data for the presentation (v3): accounts, three courses and real student histories.

Run from `backend/` (uploads go to UPLOAD_DIR, relative to it):

    python -m app.demo.seed                       # create what is missing ("bez zmian" otherwise)
    python -m app.demo.seed --reset-students      # bring every demo account back to its start state
    python -m app.demo.seed --refresh-demo-media  # texts and versions from courses.py, new MP3

Everything goes through the module services (the same checks as the application): courses are
built from `courses.py` by their teachers (one per course, D55) and published by `authoring`
(readiness R11); in an existing database the admin moves a demo course back to its teacher
(`curriculum.change_owner`). Students fill in the
survey, enrol, draw and answer quizzes, change lesson forms and accept proposals. The only
direct SQL moves the students' timestamps back by days, so the charts have a time axis.
"""

import argparse
import random
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.orm import InstrumentedAttribute, Session

from app.core.db import SessionLocal
from app.demo.courses import ASSETS_DIR, COURSES, Block, Course, Text, block_payload
from app.modules.assessment import service as assessment
from app.modules.assessment.models import LessonQuiz, QuizDraw
from app.modules.assessment.schemas import AttemptResponse, QuizContent
from app.modules.authoring import service as authoring
from app.modules.content import service as content
from app.modules.content.blocks import LessonBlocks
from app.modules.content.models import File
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Course as CourseModel
from app.modules.curriculum.models import Enrollment, EnrollmentStatus, Lesson, LessonCompletion
from app.modules.curriculum.schemas import (
    CourseCreateRequest,
    CourseUpdateRequest,
    LessonUpdateRequest,
)
from app.modules.identity import service as identity
from app.modules.identity.models import ApprovalStatus, User, UserRole
from app.modules.learning_style import service as learning_style
from app.modules.learning_style.models import (
    DecisionEvent,
    LearningProfile,
    LessonForm,
    QuizResult,
    StyleHistory,
    StyleProposal,
    StyleTrial,
    SurveyAnswer,
    SurveyResult,
)
from app.modules.learning_style.schemas import SurveyChoice

PASSWORD = "Demo123!"
SEED = 2026  # quiz draws are random; a fixed seed gives the same histories every time

# --- Accounts --------------------------------------------------------------------------------


@dataclass(frozen=True)
class Account:
    email: str
    name: str
    role: UserRole
    approval: ApprovalStatus = ApprovalStatus.APPROVED


ADMIN = Account("admin.demo@imsu.pl", "Adam Admin", UserRole.ADMIN)
TEACHER = Account("nauczyciel.demo@imsu.pl", "Anna Nowak", UserRole.TEACHER)
ENGLISH_TEACHER = Account("nauczyciel.angielski@imsu.pl", "Katarzyna Wróbel", UserRole.TEACHER)
PYTHON_TEACHER = Account("nauczyciel.programowanie@imsu.pl", "Paweł Sikora", UserRole.TEACHER)
NEW_TEACHER = Account(
    "nauczyciel.nowy@imsu.pl", "Piotr Zieliński", UserRole.TEACHER, ApprovalStatus.PENDING
)
# Teacher of each demo course (D55); Anna Nowak stays the heroine of the show (Matematyka)
OWNERS = {"m": TEACHER, "e": ENGLISH_TEACHER, "p": PYTHON_TEACHER}
# A demo course is found by its title among the courses of these accounts: the admin may have
# moved it to another demo teacher during the show
DEMO_TEACHERS = (TEACHER, ENGLISH_TEACHER, PYTHON_TEACHER, NEW_TEACHER)

# --- Student histories -----------------------------------------------------------------------
# Steps run through the services one after another; after each step all timestamps of the
# student move one day back, so the history spreads over days and keeps its order.


@dataclass(frozen=True)
class Survey:
    v: int
    a: int
    k: int


@dataclass(frozen=True)
class Enrol:
    course: str  # course code: "m", "e", "p"
    accept: bool = True


@dataclass(frozen=True)
class Quiz:
    course: str
    lesson: int  # 1-based number
    percent: int  # 0, 20, ..., 100 (k of 5 questions answered correctly)


@dataclass(frozen=True)
class ChooseForm:
    course: str
    lesson: int
    form: str
    source: str = "suggestion"


@dataclass(frozen=True)
class AcceptProposal:
    pass


Step = Survey | Enrol | Quiz | ChooseForm | AcceptProposal


@dataclass(frozen=True)
class Student:
    email: str
    name: str
    steps: tuple[Step, ...] = ()


STUDENTS: tuple[Student, ...] = (
    # No survey: the system sends her to the survey first
    Student("uczen.nowy@imsu.pl", "Ola Kowalska"),
    # Survey A 50 / V 30 / K 20, style A; waits for the teacher to accept her in Matematyka
    Student("uczen.zapis@imsu.pl", "Zosia Mazur", (Survey(6, 10, 4), Enrol("m", accept=False))),
    # "Just before the suggestion": 45 / 40 / 15, style V, lesson 3 of Matematyka available
    Student(
        "uczen.demo@imsu.pl",
        "Kuba Wiśniewski",
        (
            Survey(9, 8, 3),
            Enrol("m"),
            Quiz("m", 1, 80),  # V 55 / A 33 / K 12
            Quiz("m", 2, 40),  # back to 45 / 40 / 15, suggestion A (survey) – ignored
            Quiz("m", 2, 80),  # second attempt in V: not counted, passes, unlocks lesson 3
        ),
    ),
    # Suggestion -> form V -> proposal accepted -> trial "helped" 40% -> 90%, praise 3 x V
    Student(
        "uczen.zmiana@imsu.pl",
        "Marta Lewandowska",
        (
            Survey(7, 3, 10),
            Enrol("p"),
            Quiz("p", 1, 40),
            ChooseForm("p", 1, "V"),
            Quiz("p", 1, 80),
            AcceptProposal(),
            Quiz("p", 2, 100),
            Quiz("p", 3, 80),
        ),
    ),
    # Class of six (first group)
    Student(
        "uczen1@imsu.pl",
        "Antoni Wójcik",
        (
            Survey(10, 5, 5),
            Enrol("m"),
            Enrol("e"),
            Quiz("m", 1, 80),
            Quiz("m", 2, 40),
            Quiz("e", 1, 100),
        ),
    ),
    Student(
        "uczen2@imsu.pl",
        "Julia Kamińska",
        # fails in V, redoes the lesson in A, passes – the proposal to switch to A stays open
        (Survey(9, 8, 3), Enrol("m"), Quiz("m", 1, 60), ChooseForm("m", 1, "A"), Quiz("m", 1, 80)),
    ),
    Student(
        "uczen3@imsu.pl",
        "Szymon Wojciechowski",
        (
            Survey(5, 11, 4),
            Enrol("m"),
            Enrol("e"),
            Quiz("m", 1, 80),
            Quiz("m", 2, 100),
            Quiz("m", 3, 80),
            Quiz("e", 1, 80),
        ),
    ),
    Student(
        "uczen4@imsu.pl",
        "Lena Dąbrowska",
        (Survey(4, 12, 4), Enrol("m"), Quiz("m", 1, 80), Quiz("m", 2, 80), Quiz("m", 3, 100)),
    ),
    Student(
        "uczen5@imsu.pl",
        "Filip Kozłowski",
        (
            Survey(5, 4, 11),
            Enrol("m"),
            Enrol("p"),
            Quiz("m", 1, 80),
            Quiz("m", 2, 60),
            Quiz("p", 1, 60),
        ),
    ),
    Student(
        "uczen6@imsu.pl",
        "Maja Jankowska",
        (Survey(6, 3, 11), Enrol("m"), Quiz("m", 1, 80), Quiz("m", 2, 60)),
    ),
    # Second group in Matematyka (course statistics): appended after the first group, so the
    # draws above stay the same. Lesson 2 is the hardest; lesson 3 works in A, not in V.
    Student(
        "uczen7@imsu.pl",
        "Natalia Zając",
        # strong in A; fails lesson 2 once and passes it again in A
        (
            Survey(6, 11, 3),
            Enrol("m"),
            Quiz("m", 1, 100),
            Quiz("m", 2, 60),
            Quiz("m", 2, 80),
            Quiz("m", 3, 100),
            Quiz("m", 4, 80),
        ),
    ),
    Student(
        "uczen8@imsu.pl",
        "Mikołaj Król",
        # lesson 3 in V 40% -> suggestion A -> A 80%; back in V for lesson 4
        (
            Survey(11, 5, 4),
            Enrol("m"),
            Quiz("m", 1, 80),
            Quiz("m", 2, 80),
            Quiz("m", 3, 40),
            ChooseForm("m", 3, "A"),
            Quiz("m", 3, 80),
            Quiz("m", 4, 80),
        ),
    ),
    Student(
        "uczen9@imsu.pl",
        "Hanna Pawlak",
        # V fails twice, A passes twice -> accepts V -> A; trial running (1 of 2 lessons)
        (
            Survey(10, 7, 3),
            Enrol("m"),
            Quiz("m", 1, 80),
            Quiz("m", 2, 60),
            ChooseForm("m", 2, "A"),
            Quiz("m", 2, 80),
            Quiz("m", 3, 40),
            ChooseForm("m", 3, "A"),
            Quiz("m", 3, 100),
            AcceptProposal(),
            Quiz("m", 4, 60),
            Quiz("m", 4, 100),
        ),
    ),
    Student(
        "uczen10@imsu.pl",
        "Wiktor Michalski",
        # K fails lessons 3 and 4, passes both in A -> open proposal K -> A
        (
            Survey(4, 5, 11),
            Enrol("m"),
            Quiz("m", 1, 80),
            Quiz("m", 2, 80),
            Quiz("m", 3, 60),
            ChooseForm("m", 3, "A"),
            Quiz("m", 3, 80),
            Quiz("m", 4, 60),
            ChooseForm("m", 4, "A"),
            Quiz("m", 4, 80),
        ),
    ),
    Student(
        "uczen11@imsu.pl",
        "Amelia Grabowska",
        # V 100, 100, then lesson 3 60% (passed again in V) and lesson 4 60% (not passed yet)
        (
            Survey(12, 4, 4),
            Enrol("m"),
            Quiz("m", 1, 100),
            Quiz("m", 2, 100),
            Quiz("m", 3, 60),
            Quiz("m", 3, 80),
            Quiz("m", 4, 60),
        ),
    ),
    Student(
        "uczen12@imsu.pl",
        "Igor Nowicki",
        # lesson 2 failed in V, A and K: three counted failures in a row (R12, "wymaga uwagi")
        (
            Survey(9, 6, 5),
            Enrol("m"),
            Quiz("m", 1, 80),
            Quiz("m", 2, 40),
            ChooseForm("m", 2, "A"),
            Quiz("m", 2, 60),
            ChooseForm("m", 2, "K", "manual"),
            Quiz("m", 2, 40),
        ),
    ),
)

# --- Question difficulty -----------------------------------------------------------------------
# A quiz keeps its percent (k of 5 correct); in Matematyka the wrong answers go to the hardest
# drawn questions, so every lesson has a hard question (one common wrong answer) and an easy one.


@dataclass(frozen=True)
class Difficulty:
    order: tuple[str, ...]  # question ids of the pool, hardest first
    trap: tuple[str, int]  # the hard question and its common wrong answer (index among wrong)

    def rank(self, question_id: str) -> int:
        return self.order.index(question_id) if question_id in self.order else len(self.order)

    def wrong_index(self, question_id: str) -> int:
        return self.trap[1] if question_id == self.trap[0] else 0


# (course, lesson number) -> difficulty; ids and answers from `courses.py`
DIFFICULTY: dict[tuple[str, int], Difficulty] = {
    # q8 "y = 4x − 1 has value 7": x = 27 (7 put in place of x)
    ("m", 1): Difficulty(("q8", "q6", "q5", "q7", "q3", "q4", "q1", "q2"), ("q8", 0)),
    # q4 "the steepest line": y = 3x (sign of a taken into account)
    ("m", 2): Difficulty(("q4", "q6", "q7", "q5", "q8", "q2", "q3", "q1"), ("q4", 0)),
    # q4 "where y = 2x − 4 crosses the x axis": (0, −4) (the y-axis point)
    ("m", 3): Difficulty(("q4", "q7", "q8", "q5", "q6", "q3", "q1", "q2"), ("q4", 1)),
    # q1 "taxi formula": y = 8x + 3 (a and b swapped)
    ("m", 4): Difficulty(("q1", "q7", "q5", "q3", "q8", "q4", "q6", "q2"), ("q1", 0)),
}

# --- Output ----------------------------------------------------------------------------------


def log(message: str) -> None:
    print(f"  {message}")


# --- Accounts and courses ---------------------------------------------------------------------


def ensure_user(db: Session, account: Account) -> User:
    user = identity.get_by_email(db, account.email)
    if user is not None:
        log(f"bez zmian: {account.email}")
        return user
    user = identity.create_user(
        db,
        email=account.email,
        password=PASSWORD,
        display_name=account.name,
        role=account.role,
        approval_status=account.approval,
    )
    log(f"utworzono: {account.email} ({account.name})")
    return user


def demo_teacher_ids(db: Session) -> list[int]:
    found = (identity.get_by_email(db, account.email) for account in DEMO_TEACHERS)
    return [user.id for user in found if user is not None]


def find_course(db: Session, title: str) -> CourseModel | None:
    """Demo course by its title among the courses of the demo teachers (any of them)."""
    return db.scalar(
        select(CourseModel)
        .where(
            CourseModel.owner_id.in_(demo_teacher_ids(db)),
            CourseModel.title == title,
            CourseModel.is_archived.is_(False),
        )
        .order_by(CourseModel.id)
        .limit(1)
    )


def owner_of(db: Session, course: CourseModel) -> User:
    owner = db.get(User, course.owner_id)
    assert owner is not None, course.title
    return owner


def upload(db: Session, teacher: User, name: str) -> int:
    with (ASSETS_DIR / name).open("rb") as stream:
        return content.save_upload(db, teacher, name, stream).id


def save_blocks(
    db: Session,
    teacher: User,
    lesson_id: int,
    form: str,
    blocks: Sequence[Block],
    files: dict[str, int],
) -> None:
    for block in blocks:
        if not isinstance(block, Text) and block.file not in files:
            files[block.file] = upload(db, teacher, block.file)
    data = LessonBlocks.model_validate({"blocks": [block_payload(b, files) for b in blocks]})
    content.save_version(db, lesson_id, form, teacher, data)


def create_course(db: Session, teacher: User, spec: Course) -> CourseModel:
    """Course, lessons, files, three versions, question pool; lessons published by authoring."""
    course = curriculum.create_course(
        db, teacher, CourseCreateRequest(title=spec.title, description=spec.description)
    )
    curriculum.update_course(
        db,
        course.id,
        teacher,
        CourseUpdateRequest(introduction=spec.introduction, summary=spec.summary),
    )
    for lesson_spec in spec.lessons:
        lesson = curriculum.create_lesson(db, course.id, teacher, lesson_spec.title)
        curriculum.update_lesson(
            db,
            lesson.id,
            teacher,
            LessonUpdateRequest(outline=lesson_spec.outline, conclusions=lesson_spec.conclusions),
        )
        files: dict[str, int] = {}
        for form, blocks in lesson_spec.versions.items():
            save_blocks(db, teacher, lesson.id, form, blocks, files)
        pool = QuizContent.model_validate({"questions": lesson_spec.quiz()})
        assessment.save_quiz(db, lesson.id, teacher, pool)
        # authoring checks readiness (R11) before publishing – the demo must pass it
        authoring.set_publication(db, lesson.id, teacher, True)
    curriculum.update_course(db, course.id, teacher, CourseUpdateRequest(is_published=True))
    return course


def ensure_course(
    db: Session, spec: Course, teacher: User, admin: User, refresh_media: bool
) -> None:
    """Create the course as its teacher, or move it back to that teacher (as the admin)."""
    course = find_course(db, spec.title)
    if course is None:
        create_course(db, teacher, spec)
        log(f"utworzono kurs: {spec.title} ({len(spec.lessons)} lekcje, opublikowany)")
        return
    changed = False
    if course.owner_id != teacher.id:
        previous = owner_of(db, course).display_name
        curriculum.change_owner(db, course.id, admin, teacher.id)
        log(f"zmieniono autora kursu {spec.title}: {previous} → {teacher.display_name}")
        changed = True
    if refresh_media:
        refresh_course(db, course, spec, teacher)
        log(f"odświeżono treść i nagrania wersji A: {spec.title}")
        changed = True
    if not changed:
        log(f"bez zmian: kurs {spec.title}")


def stored_files(db: Session, blocks: list[dict[str, Any]]) -> dict[str, int]:
    """Asset name -> id of the files a stored version already uses."""
    ids = [block["file_id"] for block in blocks if block.get("file_id") is not None]
    rows = db.execute(select(File.original_name, File.id).where(File.id.in_(ids)))
    return {name: file_id for name, file_id in rows}


def refresh_course(db: Session, course: CourseModel, spec: Course, teacher: User) -> None:
    """Texts and versions of an existing course from `courses.py` (as its teacher).

    Version A gets the current recordings uploaded again; V and K keep their stored images and
    PDFs (D56 allows files already used in the lesson). Old files stay in `files` and uploads.
    """
    curriculum.update_course(
        db,
        course.id,
        teacher,
        CourseUpdateRequest(introduction=spec.introduction, summary=spec.summary),
    )
    lessons = curriculum.active_lessons(course)
    for lesson, lesson_spec in zip(lessons, spec.lessons, strict=False):
        curriculum.update_lesson(
            db,
            lesson.id,
            teacher,
            LessonUpdateRequest(outline=lesson_spec.outline, conclusions=lesson_spec.conclusions),
        )
        stored = content.stored_versions(db, lesson.id)
        for form, blocks in lesson_spec.versions.items():
            files = {} if form == "A" else stored_files(db, stored[form])
            save_blocks(db, teacher, lesson.id, form, blocks, files)


def courses_by_code(db: Session) -> dict[str, CourseModel]:
    found = {spec.code: find_course(db, spec.title) for spec in COURSES}
    return {code: course for code, course in found.items() if course is not None}


# --- Student histories ------------------------------------------------------------------------


def survey_choices(db: Session, survey: Survey) -> list[SurveyChoice]:
    """Answers giving exactly the V / A / K points (one answer per question)."""
    styles = "V" * survey.v + "A" * survey.a + "K" * survey.k
    questions = learning_style.active_questions(db)
    choices = []
    for question, style in zip(questions, styles, strict=True):
        answer = next(a for a in question.answers if a.style == style)
        choices.append(SurveyChoice(question_id=question.id, answer_id=answer.id))
    return choices


def take_quiz(
    db: Session,
    student: User,
    lesson: Lesson,
    percent: int,
    difficulty: Difficulty | None = None,
) -> AttemptResponse:
    """Draw (or reuse the open draw) and answer k of 5 questions correctly.

    Without `difficulty` the first k drawn questions are right; with it the hardest drawn ones
    are wrong. A wrong answer is the first wrong one of the question (the trap of the hard one).
    """
    lesson = curriculum.get_study_lesson(db, lesson.id, student)
    draw = assessment.current_draw(db, student, lesson)
    quiz = db.scalar(select(LessonQuiz).where(LessonQuiz.lesson_id == lesson.id))
    assert quiz is not None
    pool = {question["id"]: question for question in quiz.questions}
    correct = percent * len(draw.question_ids) // 100
    ranked = list(draw.question_ids)
    if difficulty is not None:
        ranked = sorted(ranked, key=difficulty.rank, reverse=True)  # easiest first
    right = set(ranked[:correct])
    answers = {}
    for question_id in draw.question_ids:
        question = pool[question_id]
        key = question["correct_answer_id"]
        wrong = [a["id"] for a in question["answers"] if a["id"] != key]
        index = 0 if difficulty is None else difficulty.wrong_index(question_id)
        answers[question_id] = key if question_id in right else wrong[index]
    result = assessment.submit_attempt(db, lesson.id, student, draw.id, answers)
    assert result.percent == percent, (student.email, lesson.title, result.percent)
    return result


Column = InstrumentedAttribute[Any]

# Timestamps of a student's rows, moved back together (keeps their order)
AGED: tuple[tuple[Any, Column, tuple[Column, ...]], ...] = (
    (SurveyResult, SurveyResult.user_id, (SurveyResult.created_at,)),
    (LearningProfile, LearningProfile.user_id, (LearningProfile.updated_at,)),
    (StyleHistory, StyleHistory.user_id, (StyleHistory.created_at,)),
    (DecisionEvent, DecisionEvent.user_id, (DecisionEvent.created_at,)),
    (QuizResult, QuizResult.user_id, (QuizResult.created_at,)),
    (QuizDraw, QuizDraw.user_id, (QuizDraw.created_at, QuizDraw.submitted_at)),
    (StyleProposal, StyleProposal.user_id, (StyleProposal.created_at, StyleProposal.decided_at)),
    (StyleTrial, StyleTrial.user_id, (StyleTrial.started_at, StyleTrial.finished_at)),
    (LessonForm, LessonForm.user_id, (LessonForm.updated_at,)),
    (LessonCompletion, LessonCompletion.user_id, (LessonCompletion.passed_at,)),
    (Enrollment, Enrollment.student_id, (Enrollment.requested_at, Enrollment.decided_at)),
)


def age(db: Session, user_id: int, days: int = 1) -> None:
    """Move every timestamp of the student `days` back (the only direct SQL of the seed)."""
    delta = timedelta(days=days)
    for model, owner, columns in AGED:
        values = {column.key: column - delta for column in columns}
        db.execute(update(model).where(owner == user_id).values(**values))
    db.commit()


def run_step(db: Session, step: Step, student: User, courses: dict[str, CourseModel]) -> str:
    """One step of a history through the services; returns a short description."""
    if isinstance(step, Survey):
        learning_style.submit_survey(db, student, survey_choices(db, step))
        return f"ankieta V {step.v} / A {step.a} / K {step.k}"
    if isinstance(step, Enrol):
        course = courses[step.course]
        curriculum.request_enrollment(db, course.id, student)
        if not step.accept:
            return f"prośba o zapis: {course.title}"
        # the teacher of the course accepts the student
        accepted = EnrollmentStatus.ACCEPTED
        curriculum.decide_enrollment(db, course.id, student.id, owner_of(db, course), accepted)
        return f"przyjęty do kursu {course.title}"
    if isinstance(step, Quiz | ChooseForm):
        lesson = curriculum.published_lessons(courses[step.course])[step.lesson - 1]
        if isinstance(step, Quiz):
            difficulty = DIFFICULTY.get((step.course, step.lesson))
            take_quiz(db, student, lesson, step.percent, difficulty)
            return f"{lesson.title}: {step.percent}%"
        learning_style.set_lesson_form(db, lesson.id, student, step.form, step.source)
        return f"{lesson.title}: forma {step.form} ({step.source})"
    proposal = learning_style.open_proposal(db, student.id)
    assert proposal is not None, student.email
    learning_style.accept_proposal(db, student, proposal.id)
    return f"przyjęta propozycja {proposal.from_style} → {proposal.to_style}"


def build_history(
    db: Session, spec: Student, student: User, courses: dict[str, CourseModel]
) -> None:
    for step in spec.steps:
        description = run_step(db, step, student, courses)
        age(db, student.id)
        log(f"{spec.email}: {description}")


def ensure_student(db: Session, spec: Student, courses: dict[str, CourseModel]) -> User:
    student = ensure_user(db, Account(spec.email, spec.name, UserRole.STUDENT))
    if learning_style.get_profile(db, student.id) is None and spec.steps:
        build_history(db, spec, student, courses)
    return student


def reset_student(db: Session, student: User) -> None:
    """Delete everything the student did (learning data and enrolments); the account stays."""
    for model, owner in (
        (QuizResult, QuizResult.user_id),
        (QuizDraw, QuizDraw.user_id),
        (StyleHistory, StyleHistory.user_id),
        (DecisionEvent, DecisionEvent.user_id),
        (StyleProposal, StyleProposal.user_id),
        (StyleTrial, StyleTrial.user_id),
        (LessonForm, LessonForm.user_id),
        (LessonCompletion, LessonCompletion.user_id),
        (Enrollment, Enrollment.student_id),
        (LearningProfile, LearningProfile.user_id),
        (SurveyResult, SurveyResult.user_id),
    ):
        db.execute(delete(model).where(owner == student.id))
    db.commit()
    log(f"wyczyszczono: {student.email}")


# --- Summary ----------------------------------------------------------------------------------


def student_summary(db: Session, student: User, courses: dict[str, CourseModel]) -> str:
    profile = learning_style.get_profile(db, student.id)
    if profile is None:
        return f"{student.email}: bez ankiety"
    p = profile.percentages
    parts = [f"{student.email}: styl {profile.style}, V {p['V']} / A {p['A']} / K {p['K']}"]
    for course in courses.values():
        enrollment = db.scalar(
            select(Enrollment).where(
                Enrollment.course_id == course.id, Enrollment.student_id == student.id
            )
        )
        if enrollment is None:
            continue
        name = course.title.split(":")[0]
        if enrollment.status != EnrollmentStatus.ACCEPTED:
            parts.append(f"{name} – prośba {enrollment.status}")
            continue
        passed, total = curriculum.course_progress(db, course, student.id)
        parts.append(f"{name} {passed}/{total}")
    proposal = learning_style.open_proposal(db, student.id)
    if proposal is not None:
        parts.append(f"otwarta propozycja {proposal.from_style} → {proposal.to_style}")
    trial = learning_style.last_trial(db, student.id)
    if trial is not None:
        parts.append(
            f"okres próbny {trial.from_style} → {trial.to_style}: "
            f"{trial.result or 'trwa'} ({trial.before_average} → {trial.after_average})"
        )
    return ", ".join(parts)


def course_summary(db: Session, course: CourseModel) -> str:
    owner = owner_of(db, course)
    stats = learning_style.course_stats(db, course.id, owner)
    forms = " · ".join(
        f"{form} {'–' if item.average is None else f'{item.average}%'} ({item.students} ucz.)"
        for form, item in stats.forms.items()
    )
    return f"{course.title} ({owner.display_name}): {forms}"


# --- Entry point ------------------------------------------------------------------------------


def seed(db: Session, *, reset_students: bool = False, refresh_media: bool = False) -> None:
    if db.scalar(select(SurveyAnswer.id).limit(1)) is None:
        raise SystemExit("Brak pytań ankiety – najpierw uruchom: python -m alembic upgrade head")
    assessment.rng = random.Random(SEED)
    print("Konta:")
    admin = ensure_user(db, ADMIN)
    teachers = {code: ensure_user(db, account) for code, account in OWNERS.items()}
    new_teacher = ensure_user(db, NEW_TEACHER)
    print("Kursy:")
    for spec in COURSES:
        ensure_course(db, spec, teachers[spec.code], admin, refresh_media)
    courses = courses_by_code(db)
    if reset_students:
        print("Reset kont demo:")
        identity.set_teacher_approval(db, user_id=new_teacher.id, status=ApprovalStatus.PENDING)
        log(f"{NEW_TEACHER.email}: czeka na zatwierdzenie")
        for spec in STUDENTS:
            student = identity.get_by_email(db, spec.email)
            if student is not None:
                reset_student(db, student)
    print("Uczniowie:")
    students = [ensure_student(db, spec, courses) for spec in STUDENTS]
    print("Stan kont:")
    log(f"{NEW_TEACHER.email}: konto {new_teacher.approval_status}")
    for student in students:
        log(student_summary(db, student, courses))
    print("Skuteczność form (policzone wyniki):")
    for course in courses.values():
        log(course_summary(db, course))


def main(
    argv: list[str] | None = None, session_factory: Callable[[], Session] = SessionLocal
) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.demo.seed", description=__doc__)
    parser.add_argument(
        "--reset-students",
        action="store_true",
        help="bring every demo account back to its start state (courses stay)",
    )
    parser.add_argument(
        "--refresh-demo-media",
        action="store_true",
        help="rewrite texts and versions of the demo courses from courses.py (new MP3 files)",
    )
    args = parser.parse_args(argv)
    # Polish letters and arrows must not crash the seed on a cp1250 console or pipe
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    with session_factory() as db:
        seed(db, reset_students=args.reset_students, refresh_media=args.refresh_demo_media)
    print(f"Gotowe. Hasło wszystkich kont demo: {PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
