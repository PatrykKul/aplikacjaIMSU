"""Quiz statistics: question analysis for the author, questions to review for the student.

Pure functions, no database and no FastAPI. Answers are read from submitted draws
(`quiz_draws.answers`) and checked against the current pool: a question removed from the pool
is left out, an edited key changes what counts as correct.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.modules.learning_style.stats import rate

# --- Constants (docs/08 "Stałe"; repeated in the frontend's explain.ts) --------------------------

QUESTION_MIN_DRAWS = 5  # question analysis: shares and the rating
HARD_BELOW = 40  # rating "hard": correct_percent < 40
EASY_ABOVE = 90  # rating "easy": correct_percent > 90
REVIEW_LIMIT = 5  # "To review": at most this many questions

Question = Mapping[str, Any]  # a pool question: id, text, answers, correct_answer_id, explanation


@dataclass(frozen=True)
class SubmittedDraw:
    draw_id: int
    lesson_id: int
    question_ids: tuple[str, ...]  # in the order shown
    answers: Mapping[str, str]  # question id -> chosen answer id
    submitted_at: datetime


# --- Teacher: question analysis ------------------------------------------------------------------


@dataclass(frozen=True)
class WrongAnswer:
    answer_id: str
    text: str
    count: int  # times chosen
    percent: int | None  # count / drawn; None below QUESTION_MIN_DRAWS


@dataclass(frozen=True)
class QuestionStatsRow:
    question_id: str
    text: str
    drawn: int  # submitted draws with the question
    correct: int  # answered correctly
    correct_percent: int | None  # None below QUESTION_MIN_DRAWS
    top_wrong: WrongAnswer | None  # the most chosen wrong answer; None when nobody was wrong
    rating: str | None  # "hard", "easy" or "normal"; None below QUESTION_MIN_DRAWS


def rating(correct_percent: int) -> str:
    if correct_percent < HARD_BELOW:
        return "hard"
    if correct_percent > EASY_ABOVE:
        return "easy"
    return "normal"


def question_stats(
    questions: Sequence[Question], draws: Iterable[SubmittedDraw]
) -> list[QuestionStatsRow]:
    """Per pool question: how often drawn, answered correctly, the most chosen wrong answer.

    A tie of wrong answers goes in the question's answer order. Hardest first: correct_percent
    ascending, questions without it at the end, then the pool order.
    """
    items = list(draws)
    rows = []
    for question in questions:
        qid = question["id"]
        chosen = [d.answers.get(qid) for d in items if qid in d.question_ids]
        drawn = len(chosen)
        correct = sum(1 for answer in chosen if answer == question["correct_answer_id"])
        enough = drawn >= QUESTION_MIN_DRAWS
        correct_percent = rate(correct, drawn) if enough else None
        rows.append(
            QuestionStatsRow(
                question_id=qid,
                text=question["text"],
                drawn=drawn,
                correct=correct,
                correct_percent=correct_percent,
                top_wrong=_top_wrong(question, chosen, drawn, enough),
                rating=None if correct_percent is None else rating(correct_percent),
            )
        )
    order = {row.question_id: index for index, row in enumerate(rows)}
    return sorted(
        rows,
        key=lambda row: (
            row.correct_percent is None,
            row.correct_percent or 0,
            order[row.question_id],
        ),
    )


def _top_wrong(
    question: Question, chosen: Sequence[str | None], drawn: int, enough: bool
) -> WrongAnswer | None:
    best = None
    for answer in question["answers"]:
        if answer["id"] == question["correct_answer_id"]:
            continue
        count = chosen.count(answer["id"])
        if count > 0 and (best is None or count > best.count):
            best = WrongAnswer(
                answer_id=answer["id"],
                text=answer["text"],
                count=count,
                percent=rate(count, drawn) if enough else None,
            )
    return best


# --- Student: questions to review ----------------------------------------------------------------


@dataclass(frozen=True)
class LessonInfo:
    course_id: int
    course_title: str
    lesson_id: int
    lesson_title: str
    number: int


@dataclass(frozen=True)
class AnswerRef:
    id: str
    text: str


@dataclass(frozen=True)
class ReviewQuestion:
    course_id: int
    course_title: str
    lesson_id: int
    lesson_title: str
    number: int
    question_id: str
    text: str
    chosen_answer: AnswerRef
    correct_answer: AnswerRef
    explanation: str
    answered_at: datetime


def review_questions(
    lessons: Sequence[LessonInfo],
    pools: Mapping[int, Sequence[Question]],
    draws: Iterable[SubmittedDraw],
    limit: int = REVIEW_LIMIT,
) -> list[ReviewQuestion]:
    """Questions answered wrong in the last submitted draw of each lesson, still in the pool.

    Only the given lessons count. Newest draws first, then the order in the draw; at most
    `limit`. A wrong answer the author has removed since is left out (nothing to show).
    """
    info = {lesson.lesson_id: lesson for lesson in lessons}
    last: dict[int, SubmittedDraw] = {}
    for draw in draws:
        current = last.get(draw.lesson_id)
        key = (draw.submitted_at, draw.draw_id)
        if draw.lesson_id in info and (
            current is None or key > (current.submitted_at, current.draw_id)
        ):
            last[draw.lesson_id] = draw
    newest_first = sorted(last.values(), key=lambda d: (d.submitted_at, d.draw_id), reverse=True)
    found = []
    for draw in newest_first:
        lesson = info[draw.lesson_id]
        pool = {question["id"]: question for question in pools.get(draw.lesson_id, [])}
        for qid in draw.question_ids:
            question = pool.get(qid)
            if question is None:
                continue
            answers = {answer["id"]: answer["text"] for answer in question["answers"]}
            chosen = draw.answers.get(qid)
            correct = question["correct_answer_id"]
            if chosen is None or chosen == correct or chosen not in answers:
                continue
            found.append(
                ReviewQuestion(
                    course_id=lesson.course_id,
                    course_title=lesson.course_title,
                    lesson_id=lesson.lesson_id,
                    lesson_title=lesson.lesson_title,
                    number=lesson.number,
                    question_id=qid,
                    text=question["text"],
                    chosen_answer=AnswerRef(chosen, answers[chosen]),
                    correct_answer=AnswerRef(correct, answers[correct]),
                    explanation=question["explanation"],
                    answered_at=draw.submitted_at,
                )
            )
            if len(found) == limit:
                return found
    return found
