"""Demo seed: account states from the specification, idempotency, the show and --reset-students.

The seed runs once for the module (it uploads 43 files and builds 11 histories); the tests that
change data run last, in file order: the show, then the reset that undoes it.
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, inspect, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.demo import seed
from app.demo.courses import COURSES
from app.modules.assessment.models import LessonQuiz
from app.modules.authoring import service as authoring
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Course, Enrollment, EnrollmentStatus
from app.modules.identity import service as identity
from app.modules.identity.models import ApprovalStatus, User, UserRole
from app.modules.learning_style import rules
from app.modules.learning_style import service as learning_style
from app.modules.learning_style.models import DecisionEvent


@pytest.fixture(scope="module")
def db(engine: Engine, tmp_path_factory: pytest.TempPathFactory) -> Iterator[Session]:
    """One seeded database for the module, rolled back at the end; uploads in a temp dir."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    with pytest.MonkeyPatch.context() as monkeypatch:
        uploads: Path = tmp_path_factory.mktemp("uploads")
        monkeypatch.setattr(get_settings(), "upload_dir", uploads)
        seed.seed(session)
        yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="module")
def start_counts(db: Session) -> dict[str, int]:
    return row_counts(db)


def row_counts(db: Session) -> dict[str, int]:
    tables = inspect(db.get_bind()).get_table_names()
    return {t: db.execute(text(f'SELECT count(*) FROM "{t}"')).scalar_one() for t in tables}


def user(db: Session, email: str) -> User:
    found = identity.get_by_email(db, email)
    assert found is not None, email
    return found


def course(db: Session, code: str) -> Course:
    return seed.courses_by_code(db, user(db, seed.TEACHER.email))[code]


def percentages(db: Session, email: str) -> dict[str, int]:
    profile = learning_style.get_profile(db, user(db, email).id)
    assert profile is not None
    return profile.percentages


def events(db: Session, email: str, type_: str) -> list[DecisionEvent]:
    query = select(DecisionEvent).where(
        DecisionEvent.user_id == user(db, email).id, DecisionEvent.type == type_
    )
    return list(db.scalars(query.order_by(DecisionEvent.id)))


# --- Start state -----------------------------------------------------------------------------


def test_accounts(db: Session, start_counts: dict[str, int]) -> None:
    assert user(db, seed.ADMIN.email).role == UserRole.ADMIN
    assert user(db, seed.TEACHER.email).approval_status == ApprovalStatus.APPROVED
    assert user(db, seed.NEW_TEACHER.email).approval_status == ApprovalStatus.PENDING
    assert learning_style.get_profile(db, user(db, "uczen.nowy@imsu.pl").id) is None
    for number in range(1, 7):
        assert user(db, f"uczen{number}@imsu.pl").role == UserRole.STUDENT


def test_courses_are_published_and_complete(db: Session) -> None:
    for spec in COURSES:
        found = course(db, spec.code)
        assert found.is_published
        lessons = curriculum.published_lessons(found)
        assert [lesson.title for lesson in lessons] == [lesson.title for lesson in spec.lessons]
        for lesson in lessons:
            assert authoring.lesson_readiness(db, lesson) == []
            quiz = db.scalar(select(LessonQuiz).where(LessonQuiz.lesson_id == lesson.id))
            assert quiz is not None and len(quiz.questions) == 8


def test_zosia_waits_for_the_teacher(db: Session) -> None:
    profile = learning_style.get_profile(db, user(db, "uczen.zapis@imsu.pl").id)
    assert profile is not None and profile.style == "A"
    assert profile.percentages == {"V": 30, "A": 50, "K": 20}
    enrollment = db.scalar(
        select(Enrollment).where(Enrollment.student_id == user(db, "uczen.zapis@imsu.pl").id)
    )
    assert enrollment is not None and enrollment.status == EnrollmentStatus.PENDING
    assert enrollment.course_id == course(db, "m").id


def test_kuba_just_before_the_suggestion(db: Session) -> None:
    kuba = user(db, "uczen.demo@imsu.pl")
    profile = learning_style.get_profile(db, kuba.id)
    assert profile is not None and profile.style == "V"
    assert profile.percentages == {"V": 45, "A": 40, "K": 15}
    states = curriculum.student_lesson_states(db, course(db, "m"), kuba.id)
    assert [s.state for s in states] == ["passed", "passed", "available", "locked"]
    suggestion = events(db, "uczen.demo@imsu.pl", "retry_suggestion")[-1].data["suggested"]
    assert suggestion["form"] == "A" and suggestion["reason"] == "survey"
    assert learning_style.open_proposal(db, kuba.id) is None


def test_marta_trial_helped_with_praise(db: Session) -> None:
    marta = user(db, "uczen.zmiana@imsu.pl")
    profile = learning_style.get_profile(db, marta.id)
    assert profile is not None and profile.style == "V"
    trial = learning_style.last_trial(db, marta.id)
    assert trial is not None
    assert (trial.from_style, trial.to_style, trial.result) == ("K", "V", "helped")
    assert (trial.before_average, trial.after_average) == (40, 90)
    results = learning_style.rule_results(db, learning_style.user_results(db, marta.id))
    assert rules.praise(results) == rules.Praise(form="V", streak=3, average=87)
    types = [event.type for event in events(db, "uczen.zmiana@imsu.pl", "lesson_form_changed")]
    assert types == ["lesson_form_changed"]


def test_history_spreads_over_days_in_order(db: Session) -> None:
    history = learning_style.history(db, user(db, "uczen.zmiana@imsu.pl").id)
    days = [point.at.date() for point in history]
    assert days == sorted(days) and len(set(days)) == len(days)


def test_class_open_proposal(db: Session) -> None:
    proposal = learning_style.open_proposal(db, user(db, "uczen2@imsu.pl").id)
    assert proposal is not None and (proposal.from_style, proposal.to_style) == ("V", "A")


def test_math_form_effectiveness_and_course_hint(db: Session) -> None:
    math = course(db, "m")
    stats = learning_style.course_stats(db, math.id, user(db, seed.TEACHER.email))
    averages = {form: item.average for form, item in stats.forms.items()}
    assert averages["A"] is not None and averages["A"] >= 84
    assert averages == {"V": 60, "A": averages["A"], "K": 70}
    assert all(item.students >= 2 for item in stats.forms.values())
    rows = learning_style.as_course_results(learning_style.course_results(db, math.id))
    hint = rules.course_hint(rows, user(db, "uczen.zapis@imsu.pl").id)
    assert hint is not None and hint.form == "A" and hint.students == 3


# --- Changing data (in this order) -----------------------------------------------------------


def test_second_run_changes_nothing(
    db: Session, start_counts: dict[str, int], capsys: pytest.CaptureFixture[str]
) -> None:
    seed.seed(db)
    assert row_counts(db) == start_counts
    assert "bez zmian: kurs Matematyka: funkcja liniowa" in capsys.readouterr().out


def test_kuba_show(db: Session) -> None:
    """L3 in V 40% -> suggestion A from the survey; L3 in A 80% -> proposal A with evidence."""
    kuba = user(db, "uczen.demo@imsu.pl")
    lesson = curriculum.published_lessons(course(db, "m"))[2]

    failed = seed.take_quiz(db, kuba, lesson, 40).feedback
    assert failed.form == "V" and failed.counted
    assert failed.percentages_after == {"V": 35, "A": 47, "K": 18}
    assert failed.suggestion is not None
    assert failed.suggestion.suggested.form == "A"
    assert failed.suggestion.suggested.reason == "survey"
    assert failed.proposal is None

    learning_style.set_lesson_form(db, lesson.id, kuba, "A", "suggestion")
    passed = seed.take_quiz(db, kuba, lesson, 80).feedback
    assert passed.form == "A" and passed.counted and passed.passed
    assert passed.percentages_after == {"V": 28, "A": 57, "K": 15}
    assert passed.proposal is not None and passed.proposal.to == "A"
    evidence = passed.proposal.evidence
    assert (evidence["from"]["form"], evidence["from"]["lessons"]) == ("V", 3)
    assert evidence["from"]["average"] == 53
    assert (evidence["to"]["form"], evidence["to"]["lessons"], evidence["to"]["average"]) == (
        "A",
        1,
        80,
    )


def test_reset_brings_back_the_start_state(db: Session, start_counts: dict[str, int]) -> None:
    new_teacher = user(db, seed.NEW_TEACHER.email)
    identity.set_teacher_approval(db, user_id=new_teacher.id, status=ApprovalStatus.APPROVED)
    zosia = user(db, "uczen.zapis@imsu.pl")
    curriculum.decide_enrollment(
        db, course(db, "m").id, zosia.id, user(db, seed.TEACHER.email), EnrollmentStatus.ACCEPTED
    )

    seed.seed(db, reset_students=True)

    assert row_counts(db) == start_counts
    assert user(db, seed.NEW_TEACHER.email).approval_status == ApprovalStatus.PENDING
    assert percentages(db, "uczen.demo@imsu.pl") == {"V": 45, "A": 40, "K": 15}
    assert learning_style.open_proposal(db, user(db, "uczen.demo@imsu.pl").id) is None
    enrollment = db.scalar(select(Enrollment).where(Enrollment.student_id == zosia.id))
    assert enrollment is not None and enrollment.status == EnrollmentStatus.PENDING
