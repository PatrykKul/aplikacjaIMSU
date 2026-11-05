"""Lesson step dictionaries (as in course files) shared by content tests."""

from pathlib import Path
from typing import Any

import yaml

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


# --- Course packages -------------------------------------------------------------------------

COURSE: dict[str, Any] = {
    "key": "test-course",
    "title": "Kurs testowy",
    "units": [
        {
            "key": "basics",
            "title": "Podstawy",
            "skills": [
                {"key": "base", "title": "Podstawa"},
                {"key": "advanced", "title": "Rozszerzenie", "requires": ["base"]},
            ],
        }
    ],
}


def lesson(skill: str = "base", method: str = "common", **fields: Any) -> dict[str, Any]:
    return {
        "skill": skill,
        "method": method,
        "title": f"Lekcja {skill} ({method})",
        "steps": [TEXT_STEP, number_question()],
        **fields,
    }


def write_package(
    root: Path,
    *,
    course: dict[str, Any] | None = COURSE,
    lessons: list[dict[str, Any]] | None = None,
    files: dict[str, str] | None = None,
) -> Path:
    """Write a course package to `root`; `files` adds raw files (relative path -> text)."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "lessons").mkdir(exist_ok=True)
    if course is not None:
        _write_yaml(root / "course.yaml", course)
    for data in lessons if lessons is not None else [lesson("base"), lesson("advanced")]:
        _write_yaml(root / "lessons" / f"{data['skill']}.{data['method']}.yaml", data)
    for name, text in (files or {}).items():
        (root / name).write_text(text, encoding="utf-8")
    return root


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
