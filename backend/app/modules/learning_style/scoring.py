"""VAK survey scoring: pure functions, no database and no FastAPI (ported from v1 `vak.py`)."""

from collections.abc import Iterable
from dataclasses import dataclass

STYLES = ("V", "A", "K")
STYLE_NAMES = {"V": "wzrokowiec", "A": "słuchowiec", "K": "kinestetyk"}


@dataclass(frozen=True)
class SurveyScore:
    points: dict[str, int]
    # One letter for a clear winner, several (in V-A-K order) for a tie, e.g. "VA" or "VAK"
    dominant_style: str


def dominant_styles(points: dict[str, int]) -> str:
    """Styles with the most points; a tie gives several letters in V, A, K order."""
    best = max(points.get(style, 0) for style in STYLES)
    return "".join(style for style in STYLES if points.get(style, 0) == best)


def compute_score(answer_styles: Iterable[str]) -> SurveyScore:
    """Every answer gives one point to the style it is assigned to."""
    points = dict.fromkeys(STYLES, 0)
    for style in answer_styles:
        if style not in points:
            raise ValueError(f"unknown answer style: {style!r}")
        points[style] += 1
    if sum(points.values()) == 0:
        raise ValueError("no answers to score")
    return SurveyScore(points=points, dominant_style=dominant_styles(points))


def is_valid_style(style: str | None) -> bool:
    """A non-empty set of V/A/K letters without repeats, written in V, A, K order."""
    if not style or any(letter not in STYLES for letter in style):
        return False
    return style == "".join(letter for letter in STYLES if letter in style)


def describe_style(style: str) -> str:
    """'VA' -> 'wzrokowiec + słuchowiec'."""
    return " + ".join(STYLE_NAMES[letter] for letter in STYLES if letter in style)
