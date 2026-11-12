from typing import Any


def question(qid: str, correct: str = "a") -> dict[str, Any]:
    return {
        "id": qid,
        "text": f"Pytanie {qid}",
        "answers": [{"id": "a", "text": "A"}, {"id": "b", "text": "B"}, {"id": "c", "text": "C"}],
        "correct_answer_id": correct,
        "explanation": f"Wyjaśnienie {qid}",
    }
