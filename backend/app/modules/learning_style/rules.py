"""Adaptation rules R1-R8 and R12 (docs/08): pure functions, no database and no FastAPI.

Every decision of the system comes from one function here and carries the numbers it was
made from. Inputs and outputs are plain dataclasses and dicts; the service turns them into
rows, responses and decision-log entries.

Arithmetic is exact (`Fraction`), so rounding never depends on floating-point noise:
percentages use the largest remainder method, averages round half up.
"""

from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from math import floor
from typing import Any

# --- Constants -----------------------------------------------------------------------------------

FORMS = ("V", "A", "K")  # also the order that breaks ties
PASS_THRESHOLD = 70  # passed: percent >= 70
STEP = 10  # change of a form's percentage after a counted result
MIN_PERCENT = 5  # every form keeps at least 5, so at most 90
MAX_PERCENT = 100 - 2 * MIN_PERCENT
QUIZ_SIZE = 5  # questions per attempt
TRIAL_LESSONS = 2  # trial period after a style change
HELPED_GAIN = 10  # average gain (points) from which the change "helped"
REVERT_DROP = 10  # average drop (points) from which we propose going back
RENEW_AFTER = 2  # new counted results after which a rejected proposal may come back
HINT_MIN_STUDENTS = 2  # course hint: min. students in a form
ATTENTION_STREAK = 3  # counted failures in a row that need attention (R12)

Percentages = dict[str, int]


# --- Input structures ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Result:
    """One quiz result of the student (all courses), in the order it was recorded."""

    lesson_id: int
    lesson_title: str
    form: str
    percent: int
    passed: bool
    counted: bool


@dataclass(frozen=True)
class Rejection:
    """A rejected proposal: the form it pointed to and the counted results at that moment."""

    to: str
    counted_at_decision: int


@dataclass(frozen=True)
class CourseResult:
    """A result of any student in one course (course hint, course statistics)."""

    student_id: int
    form: str
    percent: int
    counted: bool


# --- Helpers -------------------------------------------------------------------------------------


def is_passed(percent: int) -> bool:
    return percent >= PASS_THRESHOLD


def average(values: Iterable[int]) -> int | None:
    """Mean rounded half up (53.5 -> 54); None without values."""
    items = list(values)
    if not items:
        return None
    return floor(Fraction(sum(items), len(items)) + Fraction(1, 2))


def rate(part: int, whole: int) -> int:
    """`part / whole` in percent, rounded half up like `average` (1/8 -> 13); `whole` > 0."""
    return floor(Fraction(100 * part, whole) + Fraction(1, 2))


def _round_largest_remainder(shares: Mapping[str, Fraction]) -> Percentages:
    """Integers summing to the (integer) total of `shares`.

    Floor every share, then give the missing units to the largest fractional parts;
    a tie of remainders goes in V, A, K order.
    """
    floors = {form: floor(share) for form, share in shares.items()}
    missing = int(sum(shares.values())) - sum(floors.values())
    by_remainder = sorted(shares, key=lambda form: (-(shares[form] - floors[form]), _rank(form)))
    for form in by_remainder[:missing]:
        floors[form] += 1
    return {form: floors[form] for form in FORMS if form in floors}


def _rank(form: str) -> int:
    return FORMS.index(form)


def _share(total: int, weights: Mapping[str, Fraction | int]) -> dict[str, Fraction]:
    """Split `total` in proportion to `weights`, but never below MIN_PERCENT.

    A form whose share would fall below the minimum gets exactly the minimum and the rest is
    split again among the others (repeated until every share is high enough).
    """
    fixed: dict[str, Fraction] = {}
    free = {form: Fraction(weight) for form, weight in weights.items()}
    while True:
        rest = total - MIN_PERCENT * len(fixed)
        weight_sum = sum(free.values())  # > 0: a form without weight is fixed first
        shares = {form: rest * weight / weight_sum for form, weight in free.items()}
        low = [form for form, share in shares.items() if share < MIN_PERCENT]
        if not low:
            return {**fixed, **shares}
        for form in low:
            fixed[form] = Fraction(MIN_PERCENT)
            del free[form]


# --- R1. Profile from the survey -----------------------------------------------------------------


def survey_percentages(points: Mapping[str, int]) -> Percentages:
    """Survey points -> percentages (sum 100, each form 5-90).

    raw = points / total * 100; a form below 5% gets 5% and the others share the rest in
    proportion to their points. Example: A 11 / V 6 / K 3 -> A 55, V 30, K 15.
    """
    if sum(points.get(form, 0) for form in FORMS) <= 0:
        raise ValueError("no survey points")
    shares = _share(100, {form: points.get(form, 0) for form in FORMS})
    return _round_largest_remainder(shares)


def survey_leaders(points: Mapping[str, int]) -> list[str]:
    """Forms with the most points; one = the style, several = the student chooses."""
    best = max(points.get(form, 0) for form in FORMS)
    return [form for form in FORMS if points.get(form, 0) == best]


# --- R2. Change after a quiz ---------------------------------------------------------------------


def apply_result(percentages: Mapping[str, int], form: str, passed: bool) -> Percentages:
    """+10 (passed) or -10 (failed) for the lesson's form, within 5-90.

    The other two forms share the rest in proportion to their previous values.
    Example: V 45 / A 40 / K 15, V failed -> V 35 / A 47 / K 18.
    """
    changed = percentages[form] + (STEP if passed else -STEP)
    changed = max(MIN_PERCENT, min(MAX_PERCENT, changed))
    others = {other: percentages[other] for other in FORMS if other != form}
    shares = _share(100 - changed, others)
    return _round_largest_remainder({form: Fraction(changed), **shares})


def is_counted(previous_forms_in_lesson: Collection[str], form: str) -> bool:
    """Only the first attempt in a given form in a given lesson changes the percentages."""
    return form not in previous_forms_in_lesson


# --- R3. The student's form statistics -----------------------------------------------------------


@dataclass(frozen=True)
class FormStats:
    lessons: int  # counted results (one per lesson)
    average: int | None  # of counted results; None without data
    confirmed: bool  # at least one passed attempt (counted or not)


def form_stats(results: Iterable[Result]) -> dict[str, FormStats]:
    """Per form: counted lessons and their average; "confirmed" = passed at least once."""
    items = list(results)
    stats = {}
    for form in FORMS:
        counted = [r.percent for r in items if r.form == form and r.counted]
        stats[form] = FormStats(
            lessons=len(counted),
            average=average(counted),
            confirmed=any(r.form == form and r.passed for r in items),
        )
    return stats


def counted_total(stats: Mapping[str, FormStats]) -> int:
    """All counted results of the student (a rejected proposal waits for new ones)."""
    return sum(item.lessons for item in stats.values())


# --- R4. Praise ----------------------------------------------------------------------------------


@dataclass(frozen=True)
class Praise:
    form: str
    streak: int
    average: int


def praise(results: Sequence[Result]) -> Praise | None:
    """Praise a run of >= 2 counted passes in one form ending with the current result.

    `results` are the student's results in order; the last one is the current attempt and must
    be counted and passed. Earlier not counted attempts are skipped; the run stops at a counted
    result that failed or is in another form.
    Example: V 80, V 100, V 80 -> 3 lessons in a row in V, average 87.
    """
    if not results:
        return None
    current = results[-1]
    if not (current.counted and current.passed):
        return None
    run = []
    for result in reversed(results):
        if not result.counted:
            continue
        if result.form != current.form or not result.passed:
            break
        run.append(result.percent)
    if len(run) < 2:
        return None
    value = average(run)
    assert value is not None
    return Praise(form=current.form, streak=len(run), average=value)


# --- R5. Failed quiz: "redo this lesson in form X" -----------------------------------------------


@dataclass(frozen=True)
class LessonScore:
    lesson_id: int
    lesson_title: str
    percent: int


@dataclass(frozen=True)
class FailedForm:
    form: str
    percent: int  # this quiz
    previous: LessonScore | None  # previous counted result in this form in another lesson


@dataclass(frozen=True)
class SuggestedForm:
    form: str
    reason: str  # "confirmed" (passed before) or "survey" (second in the survey)
    percent: int  # current percentage of the form
    survey_percent: int
    best: LessonScore | None  # best passed result in this form ("confirmed" only)


@dataclass(frozen=True)
class Suggestion:
    failed: FailedForm
    suggested: SuggestedForm
    # "soft": the previous counted result in the failed form was passed; otherwise "strong"
    strength: str


def retry_suggestion(
    failed: Result,
    percentages: Mapping[str, int],
    stats: Mapping[str, FormStats],
    survey: Mapping[str, int],
    results: Sequence[Result],
) -> Suggestion:
    """Which other form to redo the failed lesson in, with the evidence.

    Candidates: the two forms other than the failed one. A form confirmed by results wins
    (highest percentage, then higher average, then V, A, K). Without one, the form ranked
    higher in the survey (then higher current percentage, then V, A, K).
    `results` are the student's results in order; the last one is `failed` itself.
    Strength: "soft" when the previous counted result in the failed form (any lesson, the
    current result excluded) was passed — a single slip; otherwise (a second failure in a row
    or nothing to compare with) "strong".
    """
    candidates = [form for form in FORMS if form != failed.form]
    confirmed = [form for form in candidates if stats[form].confirmed]
    if confirmed:
        form = min(
            confirmed,
            key=lambda f: (-percentages[f], -_or_minus_one(stats[f].average), _rank(f)),
        )
        reason, best = "confirmed", _best_pass(results, form)
    else:
        form = min(candidates, key=lambda f: (-survey[f], -percentages[f], _rank(f)))
        reason, best = "survey", None
    previous = next(
        (
            r
            for r in reversed(results)
            if r.counted and r.form == failed.form and r.lesson_id != failed.lesson_id
        ),
        None,
    )
    return Suggestion(
        failed=FailedForm(
            form=failed.form,
            percent=failed.percent,
            previous=None if previous is None else _score(previous),
        ),
        suggested=SuggestedForm(
            form=form,
            reason=reason,
            percent=percentages[form],
            survey_percent=survey[form],
            best=best,
        ),
        strength=_strength(failed.form, results[:-1]),
    )


def _strength(form: str, earlier: Sequence[Result]) -> str:
    last = next((r for r in reversed(earlier) if r.counted and r.form == form), None)
    return "soft" if last is not None and last.passed else "strong"


def _or_minus_one(value: int | None) -> int:
    return -1 if value is None else value


def _score(result: Result) -> LessonScore:
    return LessonScore(result.lesson_id, result.lesson_title, result.percent)


def _best_pass(results: Sequence[Result], form: str) -> LessonScore | None:
    """Highest passed result in the form; of equal ones the most recent."""
    best = None
    for result in results:
        if (
            result.form == form
            and result.passed
            and (best is None or result.percent >= best.percent)
        ):
            best = result
    return None if best is None else _score(best)


# --- R6. Proposal to change the style for good ---------------------------------------------------


@dataclass(frozen=True)
class ProposalDraft:
    kind: str  # "switch" or "revert"
    from_style: str
    to_style: str
    evidence: dict[str, Any]


def form_evidence(
    form: str, percentages: Mapping[str, int], stats: Mapping[str, FormStats]
) -> dict[str, Any]:
    return {
        "form": form,
        "lessons": stats[form].lessons,
        "average": stats[form].average,
        "percent": percentages[form],
    }


def switch_proposal(
    style: str | None,
    percentages: Mapping[str, int],
    stats: Mapping[str, FormStats],
    rejections: Iterable[Rejection],
    trial_active: bool,
) -> ProposalDraft | None:
    """Propose form Y when it is confirmed by results and has a higher percentage than the style.

    Several -> highest percentage, then higher average, then V, A, K. Not during a trial, and
    not for a form the student rejected until RENEW_AFTER new counted results have come in.
    Evidence: lessons, average and percentage of both forms.
    """
    if style is None or trial_active:
        return None
    candidates = [
        form
        for form in FORMS
        if form != style and stats[form].confirmed and percentages[form] > percentages[style]
    ]
    if not candidates:
        return None
    target = min(
        candidates,
        key=lambda f: (-percentages[f], -_or_minus_one(stats[f].average), _rank(f)),
    )
    total = counted_total(stats)
    if any(r.to == target and total - r.counted_at_decision < RENEW_AFTER for r in rejections):
        return None
    return ProposalDraft(
        kind="switch",
        from_style=style,
        to_style=target,
        evidence={
            "from": form_evidence(style, percentages, stats),
            "to": form_evidence(target, percentages, stats),
        },
    )


def forms_to_clear(
    chosen_forms: Mapping[int, str], passed_lesson_ids: Collection[int]
) -> list[int]:
    """Lessons whose explicit form choice goes away on a style change: the ones not passed yet.

    In passed lessons the choice stays as a record of how the lesson was done.
    """
    return sorted(lesson_id for lesson_id in chosen_forms if lesson_id not in passed_lesson_ids)


# --- R7. Trial period ----------------------------------------------------------------------------


@dataclass(frozen=True)
class TrialOutcome:
    after_average: int
    result: str  # "helped", "neutral", "worse" or "no_baseline"

    @property
    def propose_revert(self) -> bool:
        return self.result == "worse"


def trial_baseline(results: Sequence[Result], previous_style: str) -> int | None:
    """Average of the last <= 2 counted results in the previous style (None without any)."""
    counted = [r.percent for r in results if r.counted and r.form == previous_style]
    return average(counted[-TRIAL_LESSONS:])


def trial_outcome(
    before_average: int | None, form: str, after_results: Sequence[Result]
) -> TrialOutcome | None:
    """Result of the trial after TRIAL_LESSONS counted results in the new style.

    diff = after - before: >= +10 helped, <= -10 worse (propose going back), otherwise neutral;
    no "before" data -> no_baseline. Results in other forms do not count.
    """
    counted = [r.percent for r in after_results if r.counted and r.form == form]
    if len(counted) < TRIAL_LESSONS:
        return None
    after = average(counted[:TRIAL_LESSONS])
    assert after is not None
    if before_average is None:
        return TrialOutcome(after, "no_baseline")
    diff = after - before_average
    if diff >= HELPED_GAIN:
        return TrialOutcome(after, "helped")
    if diff <= -REVERT_DROP:
        return TrialOutcome(after, "worse")
    return TrialOutcome(after, "neutral")


def trial_progress(form: str, after_results: Iterable[Result]) -> int:
    """Counted results in the new style so far (at most TRIAL_LESSONS)."""
    done = sum(1 for r in after_results if r.counted and r.form == form)
    return min(done, TRIAL_LESSONS)


# --- R7a. Style change during a trial ------------------------------------------------------------


@dataclass(frozen=True)
class TrialInfo:
    """The running trial: the style it started from and its baseline."""

    id: int
    from_style: str
    to_style: str
    before_average: int | None


@dataclass(frozen=True)
class TrialDecision:
    # "start": the running trial (if any) ends without a result, a new one starts
    # "cancel": the change is undone, the running trial is cancelled, no new trial
    # "replace": the running trial is cancelled, a new one keeps its baseline
    # "none": no new trial (accepted `revert`); the running one ends without a result
    action: str
    from_style: str | None  # baseline style of the new trial ("start", "replace")
    before_average: int | None


def trial_on_style_change(
    active: TrialInfo | None,
    counted_in_trial: int,
    new_style: str,
    previous_style: str,
    before_average: int | None,
    *,
    starts_trial: bool = True,
) -> TrialDecision:
    """What a style change does to the trial period (R7a, D60).

    While a trial has no counted lesson in its new form yet, the change was not tried at all:
    going back to the trial's `from_style` cancels it (no new trial), switching to the third
    style replaces it with one keeping the original baseline (`from_style`, `before_average`).
    Otherwise a new trial starts from the previous style with `before_average` (its baseline).
    `starts_trial=False` (accepted `revert` proposal): no new trial.
    Example: A (2 lessons, 100%) -> V -> back to A before any lesson in V: "cancel";
    A -> V -> K before any lesson in V: "replace", trial A -> K with baseline 100.
    """
    if active is not None and counted_in_trial == 0:
        if new_style == active.from_style:
            return TrialDecision("cancel", None, None)
        if starts_trial:
            return TrialDecision("replace", active.from_style, active.before_average)
    if not starts_trial:
        return TrialDecision("none", None, None)
    return TrialDecision("start", previous_style, before_average)


# --- R8. Course hint -----------------------------------------------------------------------------


@dataclass(frozen=True)
class Hint:
    form: str
    average: int
    students: int
    results: int


def course_hint(course_results: Iterable[CourseResult], student_id: int) -> Hint | None:
    """For a student without any result in the course: the form that works best for others.

    Counted results of other students grouped by form; only forms with >= 2 students; highest
    average, then more students, then V, A, K. No automatic change, just information.
    """
    items = list(course_results)
    if any(r.student_id == student_id for r in items):
        return None
    hints = []
    for form in FORMS:
        counted = [r for r in items if r.form == form and r.counted]
        students = len({r.student_id for r in counted})
        if students >= HINT_MIN_STUDENTS:
            value = average(r.percent for r in counted)
            assert value is not None
            hints.append(Hint(form, value, students, len(counted)))
    if not hints:
        return None
    return min(hints, key=lambda h: (-h.average, -h.students, _rank(h.form)))


# --- R12. A run of failures ----------------------------------------------------------------------


@dataclass(frozen=True)
class FormScore:
    lesson_id: int
    lesson_title: str
    form: str
    percent: int


@dataclass(frozen=True)
class Attention:
    streak: int  # counted failures in a row, from the newest backwards
    results: tuple[FormScore, ...]  # the last ATTENTION_STREAK counted results, oldest first


def attention(results: Sequence[Result]) -> Attention | None:
    """>= 3 counted results in a row below the threshold (all courses, any form).

    Counted from the newest backwards; not counted attempts are skipped and the first counted
    pass ends the run, so a pass makes the attention go away.
    Example: 55, 40, 50 (counted, failed) -> streak 3 with these three results.
    """
    counted = [r for r in results if r.counted]
    streak = 0
    for result in reversed(counted):
        if result.passed:
            break
        streak += 1
    if streak < ATTENTION_STREAK:
        return None
    return Attention(
        streak=streak,
        results=tuple(
            FormScore(r.lesson_id, r.lesson_title, r.form, r.percent)
            for r in counted[-ATTENTION_STREAK:]
        ),
    )
