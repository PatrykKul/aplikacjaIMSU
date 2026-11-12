"""What a lesson version lacks before the lesson can be published (R11): pure function.

V: text and an image or a video; A: a recording (file or transcript) and a short text
description; K: a text instruction and a PDF worksheet.
"""

from collections.abc import Sequence
from typing import Any

from app.modules.curriculum.readiness import Issue, is_empty_document


def _has_text(blocks: Sequence[dict[str, Any]]) -> bool:
    return any(
        block.get("type") == "text" and not is_empty_document(block.get("doc")) for block in blocks
    )


def _kinds(blocks: Sequence[dict[str, Any]]) -> set[str]:
    return {block.get("kind", "") for block in blocks if block.get("type") == "attachment"}


def version_issues(form: str, blocks: Sequence[dict[str, Any]]) -> list[Issue]:
    """Missing parts of one version, given its blocks as saved."""
    if not blocks:
        return [{"area": form, "code": "VERSION_EMPTY"}]
    has_text = _has_text(blocks)
    kinds = _kinds(blocks)
    codes: list[str] = []
    if form == "V":
        if not (has_text and kinds & {"image", "video"}):
            codes.append("V_VISUAL_MISSING")
    elif form == "A":
        if "audio" not in kinds:
            codes.append("A_AUDIO_MISSING")
        if not has_text:
            codes.append("A_DESCRIPTION_MISSING")
    elif form == "K":
        if not has_text:
            codes.append("K_INSTRUCTION_MISSING")
        if "pdf" not in kinds:
            codes.append("K_WORKSHEET_MISSING")
    return [{"area": form, "code": code} for code in codes]
