"""Demo seed: account states from the specification, idempotency, the show and --reset-students.

The seed runs once for the module (it uploads 79 files and builds 11 histories); the tests that
change data run last, in file order: the show, the reset that undoes it, then the media refresh.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from sqlalchemy import Engine, func, inspect, select, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.demo import seed
from app.demo.courses import COURSES, Audio
from app.modules.assessment.models import LessonQuiz
from app.modules.authoring import service as authoring
from app.modules.content import service as content
from app.modules.content.models import File
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Course, CourseOwnerChange, Enrollment, EnrollmentStatus
from app.modules.curriculum.schemas import CourseUpdateRequest
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
    return seed.courses_by_code(db)[code]


def percentages(db: Session, email: str) -> dict[str, int]:
    profile = learning_style.get_profile(db, user(db, email).id)
    assert profile is not None
    return profile.percentages


def events(db: Session, email: str, type_: str) -> list[DecisionEvent]:
    query = select(DecisionEvent).where(
        DecisionEvent.user_id == user(db, email).id, DecisionEvent.type == type_
    )
    return list(db.scalars(query.order_by(DecisionEvent.id)))


def owners(db: Session) -> dict[str, str]:
    """Course code -> e-mail of its owner."""
    return {
        code: seed.owner_of(db, found).email for code, found in seed.courses_by_code(db).items()
    }


def node_types(node: Any) -> set[str]:
    """Types of all nodes of a TipTap document (or of any part of it)."""
    if isinstance(node, list):
        return set().union(*(node_types(item) for item in node))
    if not isinstance(node, dict):
        return set()
    found = {node["type"]} if "type" in node else set()
    for mark in node.get("marks", []):
        found.add(f"mark:{mark['type']}")
    return found | node_types(node.get("content", []))


def audio_blocks(blocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [b for b in blocks if b["type"] == "attachment" and b["kind"] == "audio"]


EXPECTED_OWNERS = {
    "m": "nauczyciel.demo@imsu.pl",
    "e": "nauczyciel.angielski@imsu.pl",
    "p": "nauczyciel.programowanie@imsu.pl",
}

# --- Start state -----------------------------------------------------------------------------


def test_accounts(db: Session, start_counts: dict[str, int]) -> None:
    assert user(db, seed.ADMIN.email).role == UserRole.ADMIN
    for account in (seed.TEACHER, seed.ENGLISH_TEACHER, seed.PYTHON_TEACHER):
        teacher = user(db, account.email)
        assert teacher.role == UserRole.TEACHER
        assert teacher.approval_status == ApprovalStatus.APPROVED
    assert user(db, seed.NEW_TEACHER.email).approval_status == ApprovalStatus.PENDING
    assert learning_style.get_profile(db, user(db, "uczen.nowy@imsu.pl").id) is None
    for number in range(1, 7):
        assert user(db, f"uczen{number}@imsu.pl").role == UserRole.STUDENT


def test_each_course_has_its_teacher(db: Session) -> None:
    assert owners(db) == EXPECTED_OWNERS
    # a new database: courses created by their teachers, no owner changes
    assert db.scalar(select(func.count()).select_from(CourseOwnerChange)) == 0
    for code, found in seed.courses_by_code(db).items():
        files = {b["file_id"] for v in versions(db, found).values() for b in v if "file_id" in b}
        uploaded_by = set(db.scalars(select(File.owner_id).where(File.id.in_(files))))
        assert uploaded_by == {user(db, EXPECTED_OWNERS[code]).id}


def versions(db: Session, found: Course) -> dict[str, list[dict[str, Any]]]:
    """All versions of all lessons of a course, by "<lesson number><form>"."""
    return {
        f"{number}{form}": blocks
        for number, lesson in enumerate(curriculum.published_lessons(found), start=1)
        for form, blocks in content.stored_versions(db, lesson.id).items()
    }


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


def test_version_a_has_short_recordings_with_transcripts(db: Session) -> None:
    """D58: 2-3 recordings under section titles and a recap, each with a file and a transcript."""
    for spec in COURSES:
        for key, blocks in versions(db, course(db, spec.code)).items():
            if not key.endswith("A"):
                continue
            recordings = audio_blocks(blocks)
            assert 3 <= len(recordings) <= 4, key
            assert recordings[-1]["title"] == "Powtórka", key
            for recording in recordings:
                assert recording["file_id"] is not None, key
                assert len(recording["transcript"]) > 100, key
            assert blocks[0]["type"] == "text", key  # the description R11 asks for


def test_transcripts_are_written_not_phonetic() -> None:
    """The transcript shows code and formulas as written; the voice reads them in Polish."""
    blocks = {b.file: b for spec in COURSES for b in seed_audio(spec)}
    assert "y = ax + b" in blocks["m1_a1_wzor.mp3"].transcript()
    assert "igrek" not in blocks["m1_a1_wzor.mp3"].transcript()
    loop = blocks["p3_a1_dopoki.mp3"]
    assert "while licznik <= 5:" in loop.transcript()
    assert "łajl" not in loop.transcript().lower()
    spoken = " ".join(line.spoken for turn in loop.script for line in turn.lines)
    assert "łajl" in spoken and "<=" not in spoken
    assert blocks["e1_a1_budowa.mp3"].transcript().startswith("Nauczycielka: ")


def seed_audio(spec: Any) -> list[Audio]:
    return [b for lesson in spec.lessons for b in lesson.versions["A"] if isinstance(b, Audio)]


def test_python_code_in_code_blocks(db: Session) -> None:
    """D59: the programming lessons show code as codeBlock / code; math uses code for formulas."""
    for key, blocks in versions(db, course(db, "p")).items():
        if key.endswith("V"):
            types = node_types([b["doc"] for b in blocks if b["type"] == "text"])
            assert {"codeBlock", "mark:code"} <= types, key
    math = node_types([b["doc"] for b in versions(db, course(db, "m"))["1V"] if "doc" in b])
    assert "mark:code" in math


def test_course_texts_have_no_own_headings(db: Session) -> None:
    """The course page titles these sections itself (no "Podsumowanie i wnioski" twice)."""
    for spec in COURSES:
        found = course(db, spec.code)
        for document in (found.introduction, found.summary):
            assert "heading" not in node_types(document), spec.code
        for lesson in curriculum.published_lessons(found):
            for document in (lesson.outline, lesson.conclusions):
                assert "heading" not in node_types(document), lesson.title


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
    assert profile.percentages == {"V": 72, "A": 9, "K": 19}
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


def test_class_profiles(db: Session) -> None:
    """Students 1-6 end with the percentages of the specification (`06-demo.md`)."""
    assert percentages(db, "uczen1@imsu.pl") == {"V": 60, "A": 20, "K": 20}
    assert percentages(db, "uczen2@imsu.pl") == {"V": 28, "A": 57, "K": 15}
    assert percentages(db, "uczen3@imsu.pl") == {"V": 5, "A": 90, "K": 5}
    assert percentages(db, "uczen4@imsu.pl") == {"V": 5, "A": 90, "K": 5}
    assert percentages(db, "uczen5@imsu.pl") == {"V": 29, "A": 26, "K": 45}
    assert percentages(db, "uczen6@imsu.pl") == {"V": 30, "A": 15, "K": 55}


def test_class_open_proposal(db: Session) -> None:
    proposal = learning_style.open_proposal(db, user(db, "uczen2@imsu.pl").id)
    assert proposal is not None and (proposal.from_style, proposal.to_style) == ("V", "A")


def test_math_form_effectiveness_and_course_hint(db: Session) -> None:
    math = course(db, "m")
    stats = learning_style.course_stats(db, math.id, user(db, seed.TEACHER.email))
    averages = {form: item.average for form, item in stats.forms.items()}
    assert averages == {"V": 60, "A": 86, "K": 70}
    assert all(item.students >= 2 for item in stats.forms.values())
    rows = learning_style.as_course_results(learning_style.course_results(db, math.id))
    hint = rules.course_hint(rows, user(db, "uczen.zapis@imsu.pl").id)
    assert hint is not None and hint.form == "A" and hint.students == 3


def test_other_courses_belong_to_their_teachers(db: Session) -> None:
    """The panels of Angielski and Programowanie open for their teachers, not for Anna."""
    for code, account in (("e", seed.ENGLISH_TEACHER), ("p", seed.PYTHON_TEACHER)):
        stats = learning_style.course_stats(db, course(db, code).id, user(db, account.email))
        assert sum(item.students for item in stats.forms.values()) >= 2
        assert not curriculum.is_manager(course(db, code), user(db, seed.TEACHER.email))


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


def test_reset_brings_back_the_start_state(
    db: Session, start_counts: dict[str, int], capsys: pytest.CaptureFixture[str]
) -> None:
    admin = user(db, seed.ADMIN.email)
    new_teacher = user(db, seed.NEW_TEACHER.email)
    identity.set_teacher_approval(db, user_id=new_teacher.id, status=ApprovalStatus.APPROVED)
    zosia = user(db, "uczen.zapis@imsu.pl")
    curriculum.decide_enrollment(
        db, course(db, "m").id, zosia.id, user(db, seed.TEACHER.email), EnrollmentStatus.ACCEPTED
    )
    # on the show the admin moves Angielski to the newly approved teacher
    curriculum.change_owner(db, course(db, "e").id, admin, new_teacher.id)
    assert owners(db)["e"] == seed.NEW_TEACHER.email

    seed.seed(db, reset_students=True)

    assert owners(db) == EXPECTED_OWNERS
    assert "zmieniono autora kursu Angielski: Present Perfect" in capsys.readouterr().out
    counts = row_counts(db)
    # the two owner changes stay in the log, everything else is back
    assert counts.pop("course_owner_changes") == start_counts["course_owner_changes"] + 2
    assert counts == {t: n for t, n in start_counts.items() if t != "course_owner_changes"}
    assert user(db, seed.NEW_TEACHER.email).approval_status == ApprovalStatus.PENDING
    assert percentages(db, "uczen.demo@imsu.pl") == {"V": 45, "A": 40, "K": 15}
    assert learning_style.open_proposal(db, user(db, "uczen.demo@imsu.pl").id) is None
    enrollment = db.scalar(select(Enrollment).where(Enrollment.student_id == zosia.id))
    assert enrollment is not None and enrollment.status == EnrollmentStatus.PENDING


def test_refresh_media_rewrites_texts_and_version_a(db: Session) -> None:
    """--refresh-demo-media: texts from courses.py again (e.g. an old summary with its own
    heading), version A with newly uploaded recordings, V and K with their stored files."""
    math = course(db, "m")
    teacher = user(db, seed.TEACHER.email)
    old_summary = {"type": "doc", "content": [{"type": "heading", "attrs": {"level": 2}}]}
    curriculum.update_course(db, math.id, teacher, CourseUpdateRequest(summary=old_summary))
    lesson = curriculum.published_lessons(math)[0]
    before = {b["file_id"] for b in audio_blocks(content.get_version(db, lesson.id, "A"))}
    images = [b["file_id"] for b in content.get_version(db, lesson.id, "V") if "file_id" in b]
    files_before = db.scalar(select(func.count()).select_from(File))

    seed.seed(db, refresh_media=True)

    assert "heading" not in node_types(course(db, "m").summary)
    after = audio_blocks(content.get_version(db, lesson.id, "A"))
    assert len(after) == 4 and all(b["transcript"] for b in after)
    assert {b["file_id"] for b in after}.isdisjoint(before)
    assert [b["file_id"] for b in content.get_version(db, lesson.id, "V") if "file_id" in b] == (
        images
    )
    recordings = sum(len(seed_audio(spec)) for spec in COURSES)
    assert db.scalar(select(func.count()).select_from(File)) == files_before + recordings
    assert all(db.get(File, file_id) is not None for file_id in before)
    assert authoring.lesson_readiness(db, lesson) == []
    assert owners(db) == EXPECTED_OWNERS
