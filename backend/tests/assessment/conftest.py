from typing import Any

# Survey, courses with question pools and students (shared with the learning-style tests)
from tests.learning_style.conftest import answer_key, fill_survey, learner, quiz_course  # noqa: F401


def question(qid: str, correct: str = "a") -> dict[str, Any]:
    return {
        "id": qid,
        "text": f"Pytanie {qid}",
        "answers": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}, {"id": "c", "text": "C"}],
        "correct_answer_id": correct,
        "explanation": f"Wyjaśnienie {qid}",
    }
