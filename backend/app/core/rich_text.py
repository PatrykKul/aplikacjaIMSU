from typing import Annotated, Any

from pydantic import AfterValidator


def _check_document(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
        raise ValueError("not a rich text document")
    return value


RichTextDocument = Annotated[dict[str, Any], AfterValidator(_check_document)]
"""TipTap document stored as JSON: {"type": "doc", "content": [...]}."""


def is_empty_document(doc: dict[str, Any] | None) -> bool:
    """True for a missing TipTap document or one with only empty paragraphs.

    Same rule as `isEmptyDocument` in the frontend (`shared/rich-text/is-empty.ts`).
    """
    if not doc:
        return True
    return not any(
        node.get("type") != "paragraph" or node.get("content")
        for node in doc.get("content") or []
        if isinstance(node, dict)
    )
