"""VAK survey scoring: pure functions, no database and no FastAPI (ported from v1 `vak.py`)."""

from collections.abc import Iterable
from dataclasses import dataclass

STYLES = ("V", "A", "K")


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
