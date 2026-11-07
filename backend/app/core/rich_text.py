from typing import Annotated, Any

from pydantic import AfterValidator


def _check_document(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
        raise ValueError("not a rich text document")
    return value


RichTextDocument = Annotated[dict[str, Any], AfterValidator(_check_document)]
"""TipTap document stored as JSON: {"type": "doc", "content": [...]}."""
