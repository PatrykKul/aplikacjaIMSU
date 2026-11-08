import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.learning_style.hooks import record_quiz_result
from app.modules.learning_style.models import QuizAttempt


@pytest.fixture
def visual_student(fill_survey, student):
    fill_survey(student, "VVA")  # V 14 / A 6 / K 0
    return student


def test_success_raises_weight_once(db: Session, lesson_with_styles, visual_student):
    lesson_id = lesson_with_styles["lesson_id"]
    first = record_quiz_result(
        db, user=visual_student, lesson_id=lesson_id, block_id="q1", percent=80
    )
    assert first.passed is True
    assert first.weights_changed is True
    assert first.weights == {"V": 15, "A": 6, "K": 0}
    assert "„Wykres”: 80%" in first.why

    again = record_quiz_result(
        db, user=visual_student, lesson_id=lesson_id, block_id="q1", percent=100
    )
    assert again.weights_changed is False
    assert again.weights == {"V": 15, "A": 6, "K": 0}
    attempts = db.scalar(select(func.count()).where(QuizAttempt.user_id == visual_student.id))
    assert attempts == 2


def test_failure_lowers_weight(db: Session, lesson_with_styles, visual_student):
    feedback = record_quiz_result(
        db,
        user=visual_student,
        lesson_id=lesson_with_styles["lesson_id"],
        block_id="q1",
        percent=40,
    )
    assert feedback.passed is False
    assert feedback.weights == {"V": 13, "A": 6, "K": 0}
    assert "poniżej progu" in feedback.why


def test_mixed_style_changes_both_weights(db: Session, lesson_with_styles, fill_survey, student):
    fill_survey(student, "VA")  # tie V 10 / A 10 -> style "VA"
    feedback = record_quiz_result(
        db, user=student, lesson_id=lesson_with_styles["lesson_id"], block_id="q", percent=20
    )
    assert feedback.weights == {"V": 9, "A": 9, "K": 0}
    assert feedback.proposal is None  # still a tie, nobody leads alone


def test_proposal_appears_when_another_style_leads(
    db: Session, make_course, teacher, fill_survey, student
):
    course = make_course(teacher, lessons=tuple(f"L{i}" for i in range(9)), published=True)
    fill_survey(student, "VVA")  # V 14 / A 6 / K 0, style V
    feedback = None
    for lesson in course["lessons"]:
        feedback = record_quiz_result(
            db, user=student, lesson_id=lesson["id"], block_id="q", percent=30
        )
    assert feedback.weights == {"V": 5, "A": 6, "K": 0}
    assert feedback.proposal is not None
    assert feedback.proposal.style == "A"


def test_teacher_and_student_without_survey_get_none(
    db: Session, lesson_with_styles, teacher, student
):
    lesson_id = lesson_with_styles["lesson_id"]
    assert (
        record_quiz_result(db, user=teacher, lesson_id=lesson_id, block_id="q", percent=50) is None
    )
    assert (
        record_quiz_result(db, user=student, lesson_id=lesson_id, block_id="q", percent=50) is None
    )


def test_percent_out_of_range(db: Session, lesson_with_styles, visual_student):
    with pytest.raises(ValueError):
        record_quiz_result(
            db,
            user=visual_student,
            lesson_id=lesson_with_styles["lesson_id"],
            block_id="q",
            percent=120,
        )
