import pytest
from pydantic import ValidationError

from app.modules.content.steps import ChoiceAnswer, LessonSteps, NumberAnswer, QuestionStep
from tests.content.builders import TEXT_STEP, choice_question, number_question


def test_valid_lesson():
    lesson = LessonSteps.model_validate(
        {"steps": [TEXT_STEP, number_question(), choice_question()]}
    )
    assert isinstance(lesson.steps[1], QuestionStep)
    assert isinstance(lesson.steps[1].answer, NumberAnswer)
    assert isinstance(lesson.steps[2].answer, ChoiceAnswer)
    assert lesson.find("q-rule") is lesson.steps[2]
    assert lesson.find("missing") is None


def test_to_json_round_trip():
    lesson = LessonSteps.model_validate({"steps": [TEXT_STEP, number_question()]})
    assert LessonSteps.model_validate({"steps": lesson.to_json()}) == lesson


@pytest.mark.parametrize(
    "steps",
    [
        pytest.param([], id="no steps"),
        pytest.param([TEXT_STEP], id="no question"),
        pytest.param([TEXT_STEP, number_question(key="hook")], id="duplicate key"),
        pytest.param([{**TEXT_STEP, "key": "Hook"}, number_question()], id="key not kebab-case"),
        pytest.param([{**TEXT_STEP, "type": "video"}, number_question()], id="unknown step type"),
        pytest.param([{**TEXT_STEP, "boddy": "x"}, number_question()], id="unknown field"),
        pytest.param([{**TEXT_STEP, "body": "   "}, number_question()], id="empty body"),
        pytest.param([number_question(value="abc")], id="value not a number"),
        pytest.param(
            [number_question(feedback=[{"when": "30,0", "message": "x"}])],
            id="feedback equals value",
        ),
        pytest.param(
            [
                number_question(
                    feedback=[{"when": "90", "message": "a"}, {"when": "90.0", "message": "b"}]
                )
            ],
            id="duplicate feedback",
        ),
        pytest.param([choice_question(correct=3)], id="correct out of range"),
        pytest.param([choice_question(correct=1)], id="feedback on correct option"),
        pytest.param([choice_question(options=[{"text": "jedyna"}])], id="one option"),
    ],
)
def test_invalid_lesson(steps):
    with pytest.raises(ValidationError):
        LessonSteps.model_validate({"steps": steps})
