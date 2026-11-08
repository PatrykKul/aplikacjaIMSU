"""Choosing and scoring quiz questions: pure functions, no database and no FastAPI."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


class GradingError(ValueError):
    """The submitted answers do not match the quiz; `code` is sent to the client."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class Graded:
    percent: int
    correct_count: int
    total: int
    results: list[dict[str, Any]]


def question_visible(question: Mapping[str, Any], style: str | None) -> bool:
    """Common questions for everyone; a question about a V / A / K material only for that style.

    `style` None means "see everything" (teacher preview).
    """
    form = question.get("form")
    return style is None or form is None or form in style


def visible_questions(
    questions: Sequence[Mapping[str, Any]], style: str | None
) -> list[Mapping[str, Any]]:
    return [question for question in questions if question_visible(question, style)]


def grade(questions: Sequence[Mapping[str, Any]], answers: Mapping[str, str]) -> Graded:
    """Score answers to exactly the given questions (all must be answered)."""
    if not questions:
        raise GradingError("QUIZ_NOT_FOUND")
    if answers.keys() != {question["id"] for question in questions}:
        raise GradingError("QUIZ_INCOMPLETE")
    results = []
    for question in questions:
        chosen = answers[question["id"]]
        if chosen not in {answer["id"] for answer in question["answers"]}:
            raise GradingError("QUIZ_ANSWER_MISMATCH")
        results.append(
            {
                "question_id": question["id"],
                "correct": chosen == question["correct_answer_id"],
                "chosen_answer_id": chosen,
                "correct_answer_id": question["correct_answer_id"],
            }
        )
    correct = sum(result["correct"] for result in results)
    return Graded(
        percent=round(100 * correct / len(questions)),
        correct_count=correct,
        total=len(questions),
        results=results,
    )
