"""TipTap documents: code blocks and inline code are accepted and count as content (D59)."""

from typing import Any

import pytest
from pydantic import TypeAdapter, ValidationError

from app.core.rich_text import RichTextDocument, is_empty_document

DOCUMENT = TypeAdapter(RichTextDocument)

CODE_BLOCK = {
    "type": "codeBlock",
    "attrs": {"language": "python"},
    "content": [{"type": "text", "text": "for i in range(3):\n    print(i)"}],
}
INLINE_CODE = {
    "type": "paragraph",
    "content": [
        {"type": "text", "text": "Funkcja "},
        {"type": "text", "text": "range", "marks": [{"type": "code"}]},
    ],
}


def _doc(*nodes: dict[str, Any]) -> dict[str, Any]:
    return {"type": "doc", "content": list(nodes)}


def test_code_block_and_inline_code_are_accepted() -> None:
    document = _doc(INLINE_CODE, CODE_BLOCK)
    assert DOCUMENT.validate_python(document) == document


def test_default_tiptap_code_block_without_language() -> None:
    # TipTap's default output: `attrs.language` is null
    block = {
        "type": "codeBlock",
        "attrs": {"language": None},
        "content": [{"type": "text", "text": "x = 2 * a + b"}],
    }
    document = _doc(block, INLINE_CODE)
    assert DOCUMENT.validate_python(document) == document
    assert is_empty_document(_doc(block)) is False


@pytest.mark.parametrize("value", [{"type": "paragraph"}, {"type": "doc", "content": "x"}])
def test_not_a_document(value: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        DOCUMENT.validate_python(value)


@pytest.mark.parametrize(
    ("document", "empty"),
    [
        (None, True),
        (_doc(), True),
        (_doc({"type": "paragraph"}, {"type": "paragraph", "content": []}), True),
        (_doc(CODE_BLOCK), False),
        (_doc({"type": "paragraph"}, CODE_BLOCK), False),
        (_doc(INLINE_CODE), False),
    ],
)
def test_code_counts_as_content(document: dict[str, Any] | None, empty: bool) -> None:
    assert is_empty_document(document) is empty
