"""Checking answers to lesson questions - pure functions, no database, no framework."""

from dataclasses import dataclass

from app.modules.content.numbers import parse_number
from app.modules.content.steps import ChoiceAnswer, NumberAnswer, QuestionStep


class AnswerNotANumberError(ValueError):
    """The answer to a number question cannot be read as a number."""


class InvalidChoiceError(ValueError):
    """The answer to a choice question is not the index of one of the options."""


@dataclass(frozen=True)
class CheckResult:
    correct: bool
    # Message for a typical mistake, written in the course content
    feedback: str | None
    # Shown only after a correct answer or when the student asks for the solution
    explanation: str | None
    correct_answer: str | None


def check_answer(step: QuestionStep, answer: str | int, *, reveal: bool = False) -> CheckResult:
    if isinstance(step.answer, NumberAnswer):
        correct, feedback = _check_number(step.answer, answer)
    else:
        correct, feedback = _check_choice(step.answer, answer)
    show_solution = correct or reveal
    return CheckResult(
        correct=correct,
        feedback=None if correct else feedback,
        explanation=step.explanation if show_solution else None,
        correct_answer=correct_answer_text(step.answer) if show_solution else None,
    )


def correct_answer_text(answer: NumberAnswer | ChoiceAnswer) -> str:
    if isinstance(answer, ChoiceAnswer):
        return answer.options[answer.correct].text
    if not answer.unit:
        return answer.value
    # Polish typography
    separator = "" if answer.unit == "%" else " "
    return f"{answer.value}{separator}{answer.unit}"


def _check_number(answer: NumberAnswer, given: str | int) -> tuple[bool, str | None]:
    try:
        value = parse_number(str(given), unit=answer.unit)
    except ValueError as error:
        raise AnswerNotANumberError(str(given)) from error
    if value == parse_number(answer.value):
        return True, None
    feedback = next((f.message for f in answer.feedback if parse_number(f.when) == value), None)
    return False, feedback


def _check_choice(answer: ChoiceAnswer, given: str | int) -> tuple[bool, str | None]:
    # bool is a subclass of int, but True / False is not an option index
    valid_index = isinstance(given, int) and not isinstance(given, bool)
    if not valid_index or not 0 <= given < len(answer.options):
        raise InvalidChoiceError(repr(given))
    if given == answer.correct:
        return True, None
    return False, answer.options[given].feedback
