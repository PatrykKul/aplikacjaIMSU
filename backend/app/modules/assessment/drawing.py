"""Drawing questions for one quiz attempt (R9): pure function, no database and no FastAPI."""

import random
from collections.abc import Collection, Sequence

from app.modules.learning_style.rules import QUIZ_SIZE


def draw_questions(
    pool_ids: Sequence[str],
    last_ids: Collection[str],
    k: int = QUIZ_SIZE,
    rng: random.Random | None = None,
) -> list[str]:
    """Pick `min(k, len(pool))` questions, preferring those outside the last submitted set.

    First questions the student did not get last time (at random), then the rest from the last
    set (at random). The chosen questions are shuffled, so the repeated ones are not always at
    the end. Pool of 8 with 5 drawn before: the repeat gives 3 new + 2 from the previous set.
    """
    rng = rng or random.Random()
    fresh = [qid for qid in pool_ids if qid not in last_ids]
    repeated = [qid for qid in pool_ids if qid in last_ids]
    size = min(k, len(pool_ids))
    chosen = rng.sample(fresh, min(size, len(fresh)))
    chosen += rng.sample(repeated, size - len(chosen))
    rng.shuffle(chosen)
    return chosen
