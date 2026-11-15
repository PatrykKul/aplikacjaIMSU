"""Question analysis and questions to review (pure functions)."""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.modules.assessment.stats import (
    EASY_ABOVE,
    HARD_BELOW,
    QUESTION_MIN_DRAWS,
    REVIEW_LIMIT,
    AnswerRef,
    LessonInfo,
    QuestionStatsRow,
    ReviewQuestion,
    SubmittedDraw,
    WrongAnswer,
    question_stats,
    rating,
    review_questions,
)
from tests.assessment.conftest import question

T0 = datetime(2026, 11, 15, 10, tzinfo=UTC)
_ids = iter(range(1, 10_000))


def draw(
    answers: dict[str, str], *, lesson_id: int = 10, at: datetime = T0, draw_id: int | None = None
) -> SubmittedDraw:
    return SubmittedDraw(
        draw_id=next(_ids) if draw_id is None else draw_id,
        lesson_id=lesson_id,
        question_ids=tuple(answers),
        answers=answers,
        submitted_at=at,
    )


def by_id(rows: list[QuestionStatsRow]) -> dict[str, QuestionStatsRow]:
    return {row.question_id: row for row in rows}


# --- Question analysis ---------------------------------------------------------------------------


def test_constants():
    assert (QUESTION_MIN_DRAWS, HARD_BELOW, EASY_ABOVE, REVIEW_LIMIT) == (5, 40, 90, 5)


def test_rating_boundaries():
    assert rating(39) == "hard"
    assert rating(40) == "normal"
    assert rating(90) == "normal"
    assert rating(91) == "easy"


def test_question_stats():
    pool = [question("q1"), question("q2"), question("q3")]
    draws = [
        draw({"q1": "a", "q2": "b"}),
        draw({"q1": "b", "q2": "b"}),
        draw({"q1": "c", "q2": "c"}),
        draw({"q1": "a", "q2": "a"}),
        draw({"q1": "b", "q2": "b"}),
        draw({"q2": "a"}),
    ]
    rows = question_stats(pool, draws)
    stats = by_id(rows)
    assert stats["q1"] == QuestionStatsRow(
        question_id="q1",
        text="Pytanie q1",
        drawn=5,
        correct=2,
        correct_percent=40,
        top_wrong=WrongAnswer("b", "B", 2, 40),
        rating="normal",
    )
    assert stats["q2"] == QuestionStatsRow(
        question_id="q2",
        text="Pytanie q2",
        drawn=6,
        correct=2,
        correct_percent=33,
        top_wrong=WrongAnswer("b", "B", 3, 50),
        rating="hard",
    )
    # never drawn: no shares, no wrong answer
    assert stats["q3"] == QuestionStatsRow("q3", "Pytanie q3", 0, 0, None, None, None)
    # hardest first, without a percentage at the end
    assert [row.question_id for row in rows] == ["q2", "q1", "q3"]


def test_question_stats_below_five_draws():
    rows = question_stats([question("q1")], [draw({"q1": "b"}) for _ in range(4)])
    assert rows == [
        QuestionStatsRow("q1", "Pytanie q1", 4, 0, None, WrongAnswer("b", "B", 4, None), None)
    ]


def test_top_wrong_tie_goes_in_answer_order_and_none_without_mistakes():
    pool = [question("q1", correct="b"), question("q2")]
    answers = ["c", "a", "c", "a", "b"]  # a and c chosen twice: a comes first in the question
    rows = by_id(question_stats(pool, [draw({"q1": x, "q2": "a"}) for x in answers]))
    assert rows["q1"].top_wrong == WrongAnswer("a", "A", 2, 40)
    assert rows["q2"].top_wrong is None
    assert (rows["q2"].correct_percent, rows["q2"].rating) == (100, "easy")


def test_question_stats_order_ties_follow_the_pool():
    pool = [question("q1"), question("q2"), question("q3"), question("q4")]
    draws = [draw({"q1": "a", "q2": "b", "q3": "a"}) for _ in range(5)]
    rows = question_stats(pool, draws)
    # q2 0%, q1 and q3 100% (pool order), q4 without data
    assert [row.question_id for row in rows] == ["q2", "q1", "q3", "q4"]


def test_question_stats_ignore_questions_outside_the_pool():
    rows = question_stats([question("q1")], [draw({"q1": "a", "old": "b"})])
    assert [row.question_id for row in rows] == ["q1"]
    assert question_stats([], [draw({"q1": "a"})]) == []


# --- Questions to review -------------------------------------------------------------------------

MATH_1 = LessonInfo(1, "Matematyka", 10, "Lekcja 1", 1)
MATH_2 = LessonInfo(1, "Matematyka", 11, "Lekcja 2", 2)


def review(
    pools: dict[int, list[dict[str, Any]]],
    draws: list[SubmittedDraw],
    lessons: tuple[LessonInfo, ...] = (MATH_1, MATH_2),
) -> list[tuple[int, str]]:
    return [(r.lesson_id, r.question_id) for r in review_questions(lessons, pools, draws)]


def test_review_question_fields():
    pools = {10: [question("q1"), question("q2")]}
    (item,) = review_questions([MATH_1], pools, [draw({"q1": "a", "q2": "c"})])
    assert item == ReviewQuestion(
        course_id=1,
        course_title="Matematyka",
        lesson_id=10,
        lesson_title="Lekcja 1",
        number=1,
        question_id="q2",
        text="Pytanie q2",
        chosen_answer=AnswerRef("c", "C"),
        correct_answer=AnswerRef("a", "A"),
        explanation="Wyjaśnienie q2",
        answered_at=T0,
    )


def test_review_uses_the_last_submitted_draw_of_each_lesson():
    pools = {10: [question("q1"), question("q2")]}
    draws = [
        draw({"q1": "b", "q2": "b"}, at=T0),
        draw({"q1": "a", "q2": "b"}, at=T0 + timedelta(minutes=5)),  # q1 corrected
    ]
    assert review(pools, draws) == [(10, "q2")]
    # a later correct draw clears the lesson
    draws.append(draw({"q1": "a", "q2": "a"}, at=T0 + timedelta(minutes=9)))
    assert review(pools, draws) == []


def test_review_newest_first_then_draw_order_and_limit():
    pools = {10: [question(f"q{n}") for n in range(1, 6)], 11: [question("p1"), question("p2")]}
    draws = [
        draw({"q3": "b", "q1": "b", "q2": "a", "q4": "c", "q5": "b"}, lesson_id=10, at=T0),
        draw({"p2": "b", "p1": "c"}, lesson_id=11, at=T0 + timedelta(hours=1)),
    ]
    assert review(pools, draws) == [(11, "p2"), (11, "p1"), (10, "q3"), (10, "q1"), (10, "q4")]
    assert len(review(pools, draws)) == REVIEW_LIMIT


def test_review_skips_questions_no_longer_in_the_pool_and_removed_answers():
    pools = {10: [question("q1"), question("q2", correct="b")]}
    draws = [draw({"q1": "z", "gone": "b", "q2": "b"})]
    # q1: the chosen answer no longer exists; gone: removed; q2: correct under the new key
    assert review(pools, draws) == []


def test_review_only_for_the_given_lessons():
    pools = {10: [question("q1")], 99: [question("q1")]}
    draws = [draw({"q1": "b"}, lesson_id=99), draw({"q1": "b"}, lesson_id=10)]
    assert review(pools, draws, lessons=(MATH_1,)) == [(10, "q1")]
    assert review(pools, [], lessons=(MATH_1,)) == []
    assert review({}, [draw({"q1": "b"})]) == []  # lesson without a pool
