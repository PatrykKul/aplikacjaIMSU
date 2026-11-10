"""Lesson blocks for a learning style: pure functions (ported from v1 `personalizacja.py`).

A text block is common to everyone. An attachment is marked with the forms (V / A / K) it
suits: it matches the student when those forms share a letter with the student's style, and
otherwise it is shown collapsed in place. Forms of collapsed attachments the student opened
in a lesson add to the lesson's effective style (used by the quiz and the adaptation).
"""

from collections.abc import Iterable, Mapping
from typing import Any

from app.modules.learning_style.scoring import STYLES, describe_style

SOURCE_SURVEY = "survey"
SOURCE_MANUAL = "manual"
SOURCE_ADAPTATION = "adaptation"

TEACHER_PREVIEW = "Podgląd nauczyciela: widzisz materiały dla wszystkich stylów."


def matches_style(block: Mapping[str, Any], style: str) -> bool:
    """Text is for everyone; an attachment matches when one of its forms is in the style."""
    if block.get("type") != "attachment":
        return True
    return any(form in style for form in block.get("forms", []))


def collapsed_ids(blocks: Iterable[Mapping[str, Any]], style: str) -> list[str]:
    """Ids of attachments shown collapsed for the style, in the teacher's order."""
    return [block["id"] for block in blocks if not matches_style(block, style)]


def effective_style(style: str, opened_forms: Iterable[str]) -> str:
    """The style plus forms of opened materials, as letters in V, A, K order ("V" + "A" -> "VA")."""
    letters = set(style).union(*opened_forms)
    return "".join(letter for letter in STYLES if letter in letters)


def style_explanation(style: str, source: str, points: Mapping[str, int] | None) -> str:
    """Short "why you see this" for the current style."""
    shown = f"Widzisz materiały dla stylu: {describe_style(style)}"
    if source == SOURCE_MANUAL:
        return f"{shown}, bo ten styl został wybrany ręcznie w profilu."
    if source == SOURCE_ADAPTATION:
        return f"{shown}, bo styl zmieniono po propozycji opartej na wynikach quizów."
    if points:
        return (
            f"{shown}, bo tak wyszło w ankiecie "
            f"(V {points.get('V', 0)} / A {points.get('A', 0)} / K {points.get('K', 0)})."
        )
    return f"{shown}."
