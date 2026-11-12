import pytest

from app.modules.assessment.grading import GradingError, grade
from tests.assessment.conftest import question

QUESTIONS = [question("q1"), question("qv"), question("qa", correct="b")]


def test_grade_counts_correct_answers():
    graded = grade(QUESTIONS, {"q1": "a", "qv": "b", "qa": "b"})
    assert (graded.correct_count, graded.total, graded.percent) == (2, 3, 67)
    assert [r["correct"] for r in graded.results] == [True, False, True]
    assert graded.results[1]["correct_answer_id"] == "a"


def test_all_correct_and_all_wrong():
    assert grade(QUESTIONS, {"q1": "a", "qv": "a", "qa": "b"}).percent == 100
    assert grade(QUESTIONS, {"q1": "c", "qv": "c", "qa": "c"}).percent == 0


@pytest.mark.parametrize(
    ("answers", "code"),
    [
        ({"q1": "a", "qv": "a"}, "QUIZ_INCOMPLETE"),
        ({"q1": "a", "qv": "a", "qa": "b", "extra": "a"}, "QUIZ_INCOMPLETE"),
        ({"q1": "a", "qv": "a", "qa": "zzz"}, "QUIZ_ANSWER_MISMATCH"),
    ],
)
def test_invalid_answers(answers, code):
    with pytest.raises(GradingError) as error:
        grade(QUESTIONS, answers)
    assert error.value.code == code


def test_no_questions():
    with pytest.raises(GradingError):
        grade([], {})
