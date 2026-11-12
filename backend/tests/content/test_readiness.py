"""R11, version part: what each version must contain (pure function)."""

from typing import Any

import pytest

from app.modules.content.readiness import version_issues
from tests.content.conftest import attachment, text_block

EMPTY_TEXT = {"id": "e", "type": "text", "doc": {"type": "doc", "content": [{"type": "paragraph"}]}}
IMAGE = attachment("image", "img", file_id=1)
VIDEO = attachment("video", "vid", youtube_url="https://youtu.be/dQw4w9WgXcQ")
AUDIO_FILE = attachment("audio", "aud", file_id=2)
AUDIO_TRANSCRIPT = attachment("audio", "lek", transcript="Tekst lektora")
PDF = attachment("pdf", "pdf", file_id=3)
LINK = attachment("link", "lnk", url="https://example.com")


def _codes(form: str, blocks: list[dict[str, Any]]) -> list[str]:
    issues = version_issues(form, blocks)
    assert {issue["area"] for issue in issues} <= {form}
    return [str(issue["code"]) for issue in issues]


@pytest.mark.parametrize("form", ["V", "A", "K"])
def test_empty_version(form: str) -> None:
    assert version_issues(form, []) == [{"area": form, "code": "VERSION_EMPTY"}]


# --- V -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("visual", [IMAGE, VIDEO])
def test_visual_version_complete(visual: dict[str, Any]) -> None:
    assert _codes("V", [text_block(), visual]) == []


@pytest.mark.parametrize(
    "blocks",
    [
        [text_block()],  # no picture
        [IMAGE],  # no text
        [EMPTY_TEXT, IMAGE],  # empty text does not count
        [text_block(), PDF, LINK, AUDIO_FILE],  # other attachments do not count
    ],
)
def test_visual_version_missing(blocks: list[dict[str, Any]]) -> None:
    assert _codes("V", blocks) == ["V_VISUAL_MISSING"]


# --- A -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("audio", [AUDIO_FILE, AUDIO_TRANSCRIPT])
def test_audio_version_complete(audio: dict[str, Any]) -> None:
    assert _codes("A", [audio, text_block()]) == []


@pytest.mark.parametrize(
    ("blocks", "codes"),
    [
        ([text_block()], ["A_AUDIO_MISSING"]),
        ([AUDIO_FILE], ["A_DESCRIPTION_MISSING"]),
        ([AUDIO_TRANSCRIPT, EMPTY_TEXT], ["A_DESCRIPTION_MISSING"]),
        ([IMAGE, VIDEO], ["A_AUDIO_MISSING", "A_DESCRIPTION_MISSING"]),
    ],
)
def test_audio_version_missing(blocks: list[dict[str, Any]], codes: list[str]) -> None:
    assert _codes("A", blocks) == codes


# --- K -----------------------------------------------------------------------------------------


def test_kinesthetic_version_complete() -> None:
    assert _codes("K", [text_block(), PDF]) == []


@pytest.mark.parametrize(
    ("blocks", "codes"),
    [
        ([text_block()], ["K_WORKSHEET_MISSING"]),
        ([PDF], ["K_INSTRUCTION_MISSING"]),
        ([EMPTY_TEXT, LINK], ["K_INSTRUCTION_MISSING", "K_WORKSHEET_MISSING"]),
    ],
)
def test_kinesthetic_version_missing(blocks: list[dict[str, Any]], codes: list[str]) -> None:
    assert _codes("K", blocks) == codes
