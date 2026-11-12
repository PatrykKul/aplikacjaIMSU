from typing import Annotated, Any

from pydantic import AfterValidator


def _check_document(value: dict[str, Any]) -> dict[str, Any]:
    if value.get("type") != "doc" or not isinstance(value.get("content", []), list):
        raise ValueError("not a rich text document")
    return value


RichTextDocument = Annotated[dict[str, Any], AfterValidator(_check_document)]
"""TipTap document stored as JSON: {"type": "doc", "content": [...]}.

Only the root is checked, so every node and mark of the editor is accepted as it is, e.g.
`codeBlock` ({"type": "codeBlock", "attrs": {"language": ...}, "content": [text]}) and the
inline `code` mark (D59); the frontend renders them in a monospace font.
"""


def is_empty_document(doc: dict[str, Any] | None) -> bool:
    """True for a missing TipTap document or one with only empty paragraphs.

    Any other top-level node (heading, list, table, `codeBlock` with code...) makes it not empty.

    Same rule as `isEmptyDocument` in the frontend (`shared/rich-text/is-empty.ts`).
    """
    if not doc:
        return True
    return not any(
        node.get("type") != "paragraph" or node.get("content")
        for node in doc.get("content") or []
        if isinstance(node, dict)
    )
