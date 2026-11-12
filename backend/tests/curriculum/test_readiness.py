"""R11, lesson part: outline and conclusions (pure functions)."""

from typing import Any

import pytest

from app.modules.curriculum.readiness import is_empty_document, lesson_issues
from tests.curriculum.conftest import CONCLUSIONS, EMPTY_DOC, OUTLINE


@pytest.mark.parametrize(
    "document",
    [
        None,
        {},
        {"type": "doc"},
        {"type": "doc", "content": []},
        EMPTY_DOC,
        {"type": "doc", "content": [{"type": "paragraph", "content": []}, {"type": "paragraph"}]},
    ],
)
def test_empty_documents(document: dict[str, Any] | None) -> None:
    assert is_empty_document(document)


@pytest.mark.parametrize(
    "document",
    [
        OUTLINE,
        {"type": "doc", "content": [{"type": "heading", "attrs": {"level": 2}}]},
        {"type": "doc", "content": [{"type": "bulletList", "content": []}]},
        {
            "type": "doc",
            "content": [
                {"type": "paragraph"},
                {"type": "paragraph", "content": [{"type": "inlineMath", "attrs": {"latex": "x"}}]},
            ],
        },
    ],
)
def test_documents_with_content(document: dict[str, Any]) -> None:
    assert not is_empty_document(document)


def test_complete_lesson_has_no_issues() -> None:
    assert lesson_issues(OUTLINE, CONCLUSIONS) == []


def test_missing_outline_and_conclusions() -> None:
    assert lesson_issues(None, EMPTY_DOC) == [
        {"area": "lesson", "code": "OUTLINE_MISSING"},
        {"area": "lesson", "code": "CONCLUSIONS_MISSING"},
    ]


def test_missing_only_conclusions() -> None:
    assert lesson_issues(OUTLINE, None) == [{"area": "lesson", "code": "CONCLUSIONS_MISSING"}]
