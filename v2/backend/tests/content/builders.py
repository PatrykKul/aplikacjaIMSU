"""Lesson step dictionaries (as in course files) shared by content tests."""

from typing import Any

TEXT_STEP: dict[str, Any] = {"type": "text", "key": "hook", "body": "Bluza kosztuje **120 zł**."}


def number_question(key: str = "q-saving", **answer: Any) -> dict[str, Any]:
    return {
        "type": "question",
        "key": key,
        "prompt": "Ile złotych oszczędzasz przy rabacie 25%?",
        "answer": {
            "type": "number",
            "value": "30",
            "unit": "zł",
            "feedback": [{"when": "90", "message": "To cena po rabacie."}],
            **answer,
        },
        "hint": "25% to jedna czwarta.",
        "explanation": "25% ze 120 zł to 30 zł.",
    }


def choice_question(key: str = "q-rule", **answer: Any) -> dict[str, Any]:
    return {
        "type": "question",
        "key": key,
        "prompt": "Jak policzyć $p\\%$ z liczby $n$?",
        "answer": {
            "type": "choice",
            "options": [
                {"text": "$\\tfrac{p}{100} \\cdot n$"},
                {"text": "$\\tfrac{n}{p} \\cdot 100$", "feedback": "Sprawdź na bluzie."},
                {"text": "$p \\cdot n$"},
            ],
            "correct": 0,
            **answer,
        },
        "explanation": "Procent to setne części.",
    }
