"""Simplified adaptation: pure functions, no database or FastAPI (from v1 `adaptacja.py`).

Rules:
- start: style weights = survey points,
- quiz >= 70% is a success; each letter of the student's style gets +1 (success) / -1 (failure),
- only the first success and the first failure in a lesson and style count (no weight farming),
- when another style becomes the sole leader of the weights, the student gets a proposal
  to switch; a manually chosen style and a rejected proposal are respected.
"""

from collections.abc import Iterable, Mapping

from app.modules.learning_style.personalization import SOURCE_MANUAL
from app.modules.learning_style.scoring import STYLES

PASS_THRESHOLD = 70
WEIGHT_MIN = 0
WEIGHT_MAX = 30

MATERIALS = {"V": "wzrokowymi", "A": "słuchowymi", "K": "praktycznymi"}
MATERIALS_NOMINATIVE = {"V": "wzrokowe", "A": "słuchowe", "K": "praktyczne"}

Weights = dict[str, int]


def is_passed(percent: int) -> bool:
    return percent >= PASS_THRESHOLD


def _clamp(value: int) -> int:
    return max(WEIGHT_MIN, min(WEIGHT_MAX, value))


def initial_weights(points: Mapping[str, int]) -> Weights:
    """Starting weights = survey points (clamped to the allowed range)."""
    return {style: _clamp(int(points.get(style, 0))) for style in STYLES}


def update_weights(weights: Mapping[str, int], style: str, success: bool) -> Weights:
    """+1 / -1 for every letter of the style the student learned in (e.g. 'A' or 'VA')."""
    delta = 1 if success else -1
    return {
        letter: _clamp(int(weights.get(letter, 0)) + (delta if letter in style else 0))
        for letter in STYLES
    }


def counts_for_weights(previous_results: Iterable[bool], success: bool) -> bool:
    """Only the first success / first failure in a lesson and style changes the weights."""
    return success not in set(previous_results)


def ranking(weights: Mapping[str, int]) -> list[str]:
    """Styles from the highest weight; ties in V, A, K order."""
    return sorted(STYLES, key=lambda style: (-int(weights.get(style, 0)), STYLES.index(style)))


def proposed_style(
    weights: Mapping[str, int], style: str, source: str, rejected: str | None
) -> str | None:
    """The sole weight leader that is not part of the current style, or None.

    A manual choice always wins, and a rejected proposal is not repeated.
    """
    if source == SOURCE_MANUAL:
        return None
    leader, second = ranking(weights)[:2]
    if int(weights.get(leader, 0)) == int(weights.get(second, 0)):
        return None
    if leader in style or leader == rejected:
        return None
    return leader


def proposal_message(style: str) -> str:
    return f"Lepiej Ci idzie z materiałami {MATERIALS[style]} – przełączyć?"


def proposal_why(weights: Mapping[str, int], style: str) -> str:
    return (
        f"Wagi stylów po quizach: V {weights.get('V', 0)} / A {weights.get('A', 0)} / "
        f"K {weights.get('K', 0)} – najlepiej wypadają materiały {MATERIALS_NOMINATIVE[style]}."
    )


def quiz_why(lesson_title: str, percent: int) -> str:
    verdict = "zaliczony" if is_passed(percent) else "poniżej progu"
    return f"Bo quiz w lekcji „{lesson_title}”: {percent}% – {verdict} (próg {PASS_THRESHOLD}%)."
