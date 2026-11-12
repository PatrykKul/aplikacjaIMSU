"""Drawing questions (R9) with a seeded random generator."""

import random

from app.modules.assessment.drawing import draw_questions

POOL = [f"q{i}" for i in range(1, 9)]


def test_first_draw_takes_five_different_questions():
    drawn = draw_questions(POOL, [], rng=random.Random(1))
    assert len(drawn) == 5
    assert len(set(drawn)) == 5
    assert set(drawn) <= set(POOL)


def test_repeat_prefers_questions_outside_the_last_set():
    last = draw_questions(POOL, [], rng=random.Random(2))
    repeat = draw_questions(POOL, last, rng=random.Random(3))
    new = set(repeat) - set(last)
    assert new == set(POOL) - set(last)  # all 3 questions not shown last time
    assert len(set(repeat) & set(last)) == 2


def test_large_pool_gives_only_new_questions():
    pool = [f"q{i}" for i in range(12)]
    last = pool[:5]
    assert not set(draw_questions(pool, last, rng=random.Random(4))) & set(last)


def test_pool_of_five_gives_the_whole_pool_every_time():
    pool = POOL[:5]
    assert sorted(draw_questions(pool, pool, rng=random.Random(5))) == sorted(pool)


def test_pool_smaller_than_five_gives_all_questions():
    assert sorted(draw_questions(POOL[:3], [], rng=random.Random(6))) == sorted(POOL[:3])


def test_deterministic_with_the_same_seed():
    first = draw_questions(POOL, ["q1", "q2"], rng=random.Random(7))
    second = draw_questions(POOL, ["q1", "q2"], rng=random.Random(7))
    assert first == second


def test_order_is_shuffled():
    orders = {tuple(draw_questions(POOL[:5], [], rng=random.Random(seed))) for seed in range(20)}
    assert len(orders) > 1


def test_default_generator():
    assert len(draw_questions(POOL, [])) == 5
