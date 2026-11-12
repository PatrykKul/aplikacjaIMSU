"""What a lesson lacks before it can be published (R11, lesson part): pure functions."""

from typing import Any

Issue = dict[str, int | str]


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


def lesson_issues(
    outline: dict[str, Any] | None, conclusions: dict[str, Any] | None
) -> list[Issue]:
    """The outline and the conclusions must both have content."""
    issues: list[Issue] = []
    if is_empty_document(outline):
        issues.append({"area": "lesson", "code": "OUTLINE_MISSING"})
    if is_empty_document(conclusions):
        issues.append({"area": "lesson", "code": "CONCLUSIONS_MISSING"})
    return issues
