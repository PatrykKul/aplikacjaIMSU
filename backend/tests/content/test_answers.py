import pytest

from app.modules.content.answers import (
    AnswerNotANumberError,
    InvalidChoiceError,
    check_answer,
    correct_answer_text,
)
from app.modules.content.steps import NumberAnswer, QuestionStep
from tests.content.builders import choice_question, number_question

NUMBER = QuestionStep.model_validate(number_question())
CHOICE = QuestionStep.model_validate(choice_question())


@pytest.mark.parametrize("answer", ["30", "30 zł", " 30,0 ", 30])
def test_number_correct(answer):
    result = check_answer(NUMBER, answer)
    assert result.correct is True
    assert result.feedback is None
    assert result.explanation == "25% ze 120 zł to 30 zł."
    assert result.correct_answer == "30 zł"


def test_number_typical_mistake_gets_feedback_but_no_solution():
    result = check_answer(NUMBER, "90")
    assert result.correct is False
    assert result.feedback == "To cena po rabacie."
    assert result.explanation is None
    assert result.correct_answer is None


def test_number_other_mistake_has_no_feedback():
    result = check_answer(NUMBER, "31")
    assert (result.correct, result.feedback) == (False, None)


def test_reveal_shows_solution_after_wrong_answer():
    result = check_answer(NUMBER, "31", reveal=True)
    assert result.correct is False
    assert result.correct_answer == "30 zł"
    assert result.explanation is not None


@pytest.mark.parametrize("answer", ["abc", "", "30 euro"])
def test_number_not_a_number(answer):
    with pytest.raises(AnswerNotANumberError):
        check_answer(NUMBER, answer)


def test_choice_correct():
    result = check_answer(CHOICE, 0)
    assert result.correct is True
    assert result.correct_answer == "$\\tfrac{p}{100} \\cdot n$"


def test_choice_wrong_with_and_without_feedback():
    assert check_answer(CHOICE, 1).feedback == "Sprawdź na bluzie."
    assert check_answer(CHOICE, 2).feedback is None
    assert check_answer(CHOICE, 2).correct is False


@pytest.mark.parametrize("answer", [3, -1, True, "0"])
def test_choice_invalid_index(answer):
    with pytest.raises(InvalidChoiceError):
        check_answer(CHOICE, answer)


def test_percent_unit_has_no_space():
    answer = NumberAnswer.model_validate({"type": "number", "value": "25", "unit": "%"})
    assert correct_answer_text(answer) == "25%"
