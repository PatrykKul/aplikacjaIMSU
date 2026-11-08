"""Choosing lesson blocks for a learning style: pure functions (ported from v1 `personalizacja.py`).

In v2 a text block is common to everyone, and an attachment is marked with the forms
(V / A / K) it suits, so it is shown when those forms share a letter with the student's style.
"""

from collections.abc import Iterable, Mapping
from typing import Any

from app.modules.learning_style.scoring import describe_style

SOURCE_SURVEY = "survey"
SOURCE_MANUAL = "manual"
SOURCE_ADAPTATION = "adaptation"

TEACHER_PREVIEW = "Podgląd nauczyciela: widzisz materiały dla wszystkich stylów."


def block_visible(block: Mapping[str, Any], style: str) -> bool:
    if block.get("type") != "attachment":
        return True
    return any(form in style for form in block.get("forms", []))


def personalize(blocks: Iterable[dict[str, Any]], style: str) -> tuple[list[dict[str, Any]], int]:
    """Visible blocks in the teacher's order and how many were hidden."""
    visible: list[dict[str, Any]] = []
    hidden = 0
    for block in blocks:
        if block_visible(block, style):
            visible.append(block)
        else:
            hidden += 1
    return visible, hidden


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
