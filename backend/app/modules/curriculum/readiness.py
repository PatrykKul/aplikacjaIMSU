"""What a lesson lacks before it can be published (R11, lesson part): pure functions."""

from typing import Any

from app.core.rich_text import is_empty_document

Issue = dict[str, int | str]


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
