"""What the quiz pool lacks before the lesson can be published (R11): pure function."""

from app.modules.learning_style.rules import QUIZ_SIZE


def quiz_issues(question_count: int) -> list[dict[str, int | str]]:
    """The pool needs at least as many questions as one attempt draws."""
    if question_count >= QUIZ_SIZE:
        return []
    return [
        {
            "area": "quiz",
            "code": "QUIZ_TOO_FEW_QUESTIONS",
            "count": question_count,
            "min": QUIZ_SIZE,
        }
    ]
