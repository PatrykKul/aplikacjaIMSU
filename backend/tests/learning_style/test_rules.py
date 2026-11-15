"""Adaptation rules R1-R8 and R12 with the numbers from the specification (docs/08)."""

from itertools import product

import pytest

from app.modules.learning_style.rules import (
    ATTENTION_STREAK,
    FORMS,
    Attention,
    CourseResult,
    FormScore,
    FormStats,
    Hint,
    LessonScore,
    Praise,
    Rejection,
    Result,
    TrialDecision,
    TrialInfo,
    apply_result,
    attention,
    average,
    counted_total,
    course_hint,
    form_stats,
    forms_to_clear,
    is_counted,
    is_passed,
    praise,
    rate,
    retry_suggestion,
    survey_leaders,
    survey_percentages,
    switch_proposal,
    trial_baseline,
    trial_on_style_change,
    trial_outcome,
    trial_progress,
)


def result(
    lesson_id: int,
    form: str,
    percent: int,
    *,
    counted: bool = True,
    title: str | None = None,
) -> Result:
    return Result(
        lesson_id=lesson_id,
        lesson_title=title or f"Lekcja {lesson_id}",
        form=form,
        percent=percent,
        passed=is_passed(percent),
        counted=counted,
    )


def pct(v: int, a: int, k: int) -> dict[str, int]:
    return {"V": v, "A": a, "K": k}


def stats_of(*results: Result) -> dict[str, FormStats]:
    return form_stats(results)


# --- Helpers -------------------------------------------------------------------------------------


def test_pass_threshold_is_70():
    assert is_passed(70) and is_passed(100)
    assert not is_passed(69) and not is_passed(60)


def test_average_rounds_half_up():
    assert average([80, 40, 40]) == 53  # 53.33
    assert average([80, 100, 80]) == 87  # 86.67
    assert average([40, 41]) == 41  # 40.5 -> 41 (not banker's rounding)
    assert average([]) is None


def test_rate_rounds_half_up():
    assert rate(1, 2) == 50
    assert rate(2, 3) == 67  # 66.67
    assert rate(1, 3) == 33
    assert rate(1, 8) == 13  # 12.5 -> 13 (not banker's rounding)
    assert rate(0, 4) == 0 and rate(4, 4) == 100


# --- R1. Survey ----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("points", "expected"),
    [
        (pct(6, 11, 3), pct(30, 55, 15)),
        (pct(9, 8, 3), pct(45, 40, 15)),
        (pct(20, 0, 0), pct(90, 5, 5)),
        (pct(7, 3, 10), pct(35, 15, 50)),  # Marta
        (pct(6, 10, 4), pct(30, 50, 20)),  # Zosia
    ],
)
def test_survey_percentages_examples(points, expected):
    assert survey_percentages(points) == expected


def test_survey_minimum_five_percent_and_proportional_rest():
    # K 0 -> 5; V and A share 95 in proportion 19:1 -> A would get 4.75, so A is fixed at 5 too
    assert survey_percentages(pct(19, 1, 0)) == pct(90, 5, 5)
    # K 0 -> 5; V and A share 95 as 10:10
    assert survey_percentages(pct(10, 10, 0)) == pct(48, 47, 5)


def test_survey_remainder_tie_goes_in_v_a_k_order():
    # 33.33 each: one unit missing, equal remainders -> V gets it
    assert survey_percentages(pct(1, 1, 1)) == pct(34, 33, 33)
    # A and K share 95 equally (47.5 each): the unit goes to A before K
    assert survey_percentages(pct(0, 3, 3)) == pct(5, 48, 47)


def test_survey_without_points_is_an_error():
    with pytest.raises(ValueError):
        survey_percentages(pct(0, 0, 0))


def test_survey_property_sum_100_and_bounds():
    for points in product(range(21), repeat=3):
        if sum(points) == 0:
            continue
        percentages = survey_percentages(dict(zip(FORMS, points, strict=True)))
        assert sum(percentages.values()) == 100, points
        assert all(5 <= value <= 90 for value in percentages.values()), points


def test_survey_leaders():
    assert survey_leaders(pct(9, 8, 3)) == ["V"]
    assert survey_leaders(pct(8, 8, 4)) == ["V", "A"]
    assert survey_leaders(pct(2, 9, 9)) == ["A", "K"]


# --- R2. Change after a quiz ---------------------------------------------------------------------


def test_apply_result_examples_from_specification():
    assert apply_result(pct(45, 40, 15), "V", passed=False) == pct(35, 47, 18)
    assert apply_result(pct(35, 47, 18), "A", passed=True) == pct(28, 57, 15)


def test_apply_result_kuba_and_marta_paths():
    # Kuba: L1 in V 80% -> 55/33/12, L2 in V 40% -> back to 45/40/15
    assert apply_result(pct(45, 40, 15), "V", passed=True) == pct(55, 33, 12)
    assert apply_result(pct(55, 33, 12), "V", passed=False) == pct(45, 40, 15)
    # Marta: K fails, then V passes three times
    assert apply_result(pct(35, 15, 50), "K", passed=False) == pct(42, 18, 40)
    assert apply_result(pct(42, 18, 40), "V", passed=True) == pct(52, 15, 33)


def test_apply_result_limit_90_and_minimum_5():
    assert apply_result(pct(85, 10, 5), "V", passed=True) == pct(90, 5, 5)
    assert apply_result(pct(90, 5, 5), "V", passed=True) == pct(90, 5, 5)


def test_apply_result_at_minimum_does_not_change():
    assert apply_result(pct(5, 60, 35), "V", passed=False) == pct(5, 60, 35)


def test_apply_result_proportion_with_different_values():
    # A 50 -> 40; V and K share 60 as 30:20
    assert apply_result(pct(30, 50, 20), "A", passed=False) == pct(36, 40, 24)
    # K 10 -> 20; V and A share 80 as 45:45
    assert apply_result(pct(45, 45, 10), "K", passed=True) == pct(40, 40, 20)


GRID = [
    pct(v, a, 100 - v - a)
    for v in range(5, 91)
    for a in range(5, 91)
    if 5 <= 100 - v - a <= 90 and (v + a) % 3 == 0
]


@pytest.mark.parametrize("form", FORMS)
@pytest.mark.parametrize("passed", [True, False])
def test_apply_result_property_sum_100_and_bounds(form, passed):
    for profile in GRID:
        after = apply_result(profile, form, passed)
        assert sum(after.values()) == 100, profile
        assert all(5 <= value <= 90 for value in after.values()), profile
        expected = max(5, min(90, profile[form] + (10 if passed else -10)))
        assert after[form] == expected, profile


def test_is_counted_only_first_attempt_in_a_form():
    assert is_counted([], "V")
    assert not is_counted(["V"], "V")  # repeat in the same form
    assert is_counted(["V"], "A")  # another form in the same lesson
    assert not is_counted(["V", "A"], "A")


# --- R3. Form statistics -------------------------------------------------------------------------


def test_form_stats_counted_average_and_confirmation():
    stats = stats_of(
        result(1, "V", 80),
        result(2, "V", 40),
        result(2, "V", 80, counted=False),  # passed, not counted
        result(3, "V", 40),
        result(3, "A", 80),
    )
    assert stats["V"] == FormStats(lessons=3, average=53, confirmed=True)
    assert stats["A"] == FormStats(lessons=1, average=80, confirmed=True)
    assert stats["K"] == FormStats(lessons=0, average=None, confirmed=False)
    assert counted_total(stats) == 4


def test_form_confirmed_by_a_not_counted_pass():
    stats = stats_of(result(1, "K", 40), result(1, "K", 80, counted=False))
    assert stats["K"] == FormStats(lessons=1, average=40, confirmed=True)


def test_failed_form_is_not_confirmed():
    assert stats_of(result(1, "A", 60))["A"].confirmed is False


# --- R4. Praise ----------------------------------------------------------------------------------


def test_praise_for_marta():
    results = [result(1, "K", 40), result(1, "V", 80), result(2, "V", 100), result(3, "V", 80)]
    assert praise(results) == Praise(form="V", streak=3, average=87)


def test_praise_needs_two_in_a_row():
    assert praise([result(1, "V", 80)]) is None
    assert praise([result(1, "V", 80), result(2, "V", 90)]) == Praise("V", 2, 85)
    assert praise([]) is None


def test_praise_run_broken_by_another_form():
    assert praise([result(1, "V", 80), result(2, "A", 80), result(3, "V", 90)]) is None


def test_praise_run_broken_by_a_failure():
    assert praise([result(1, "V", 80), result(2, "V", 40), result(3, "V", 90)]) is None


def test_no_praise_for_a_not_counted_or_failed_current_result():
    assert (
        praise([result(1, "V", 80), result(2, "V", 80), result(2, "V", 90, counted=False)]) is None
    )
    assert praise([result(1, "V", 80), result(2, "V", 80), result(3, "V", 40)]) is None


def test_praise_skips_earlier_not_counted_attempts():
    results = [
        result(1, "V", 80),
        result(2, "V", 40),
        result(2, "V", 80, counted=False),
        result(3, "V", 90),
    ]
    # the counted failure in lesson 2 ends the run, the not counted pass is skipped
    assert praise(results) is None
    results = [result(1, "V", 80), result(1, "V", 100, counted=False), result(2, "V", 90)]
    assert praise(results) == Praise("V", 2, 85)


# --- R5. Retry suggestion ------------------------------------------------------------------------


def test_suggestion_from_survey_when_nothing_confirmed():
    # Kuba, lesson 3 in V failed: A was second in the survey
    history = [
        result(1, "V", 80),
        result(2, "V", 40),
        result(2, "V", 80, counted=False),
        result(3, "V", 40),
    ]
    suggestion = retry_suggestion(
        history[-1], pct(35, 47, 18), stats_of(*history), pct(45, 40, 15), history
    )
    assert suggestion.failed.form == "V"
    assert suggestion.failed.percent == 40
    assert suggestion.failed.previous == LessonScore(2, "Lekcja 2", 40)
    assert suggestion.suggested.form == "A"
    assert suggestion.suggested.reason == "survey"
    assert suggestion.suggested.percent == 47
    assert suggestion.suggested.survey_percent == 40
    assert suggestion.suggested.best is None


def test_suggestion_of_a_confirmed_form():
    history = [result(1, "A", 80), result(2, "A", 90), result(3, "V", 40)]
    suggestion = retry_suggestion(
        history[-1], pct(30, 55, 15), stats_of(*history), pct(50, 30, 20), history
    )
    assert suggestion.suggested.form == "A"
    assert suggestion.suggested.reason == "confirmed"
    assert suggestion.suggested.best == LessonScore(2, "Lekcja 2", 90)
    assert suggestion.failed.previous is None  # no earlier V result


def test_best_pass_of_equal_results_is_the_most_recent():
    history = [result(1, "A", 80), result(2, "A", 80), result(3, "V", 40)]
    suggestion = retry_suggestion(
        history[-1], pct(30, 55, 15), stats_of(*history), pct(50, 30, 20), history
    )
    assert suggestion.suggested.best == LessonScore(2, "Lekcja 2", 80)


def test_confirmed_form_wins_over_survey():
    # K is confirmed, A is higher in the survey and in percentages
    history = [result(1, "K", 80), result(2, "V", 40)]
    suggestion = retry_suggestion(
        history[-1], pct(30, 50, 20), stats_of(*history), pct(40, 45, 15), history
    )
    assert (suggestion.suggested.form, suggestion.suggested.reason) == ("K", "confirmed")


def test_two_confirmed_higher_percentage_wins():
    history = [result(1, "A", 80), result(2, "K", 90), result(3, "V", 40)]
    suggestion = retry_suggestion(
        history[-1], pct(30, 45, 25), stats_of(*history), pct(40, 30, 30), history
    )
    assert suggestion.suggested.form == "A"


def test_two_confirmed_equal_percentage_higher_average_wins():
    history = [result(1, "A", 80), result(2, "K", 90), result(3, "V", 40)]
    suggestion = retry_suggestion(
        history[-1], pct(30, 35, 35), stats_of(*history), pct(40, 30, 30), history
    )
    assert suggestion.suggested.form == "K"


def test_two_confirmed_full_tie_goes_in_v_a_k_order():
    history = [result(1, "A", 80), result(2, "K", 80), result(3, "V", 40)]
    suggestion = retry_suggestion(
        history[-1], pct(30, 35, 35), stats_of(*history), pct(40, 30, 30), history
    )
    assert suggestion.suggested.form == "A"


def test_survey_tie_higher_current_percentage_then_order():
    history = [result(1, "V", 40)]
    stats = stats_of(*history)
    survey = pct(40, 30, 30)
    by_percentage = retry_suggestion(history[-1], pct(30, 30, 40), stats, survey, history)
    assert by_percentage.suggested.form == "K"
    by_order = retry_suggestion(history[-1], pct(30, 35, 35), stats, survey, history)
    assert by_order.suggested.form == "A"


def test_failure_in_a_form_other_than_the_style():
    # Style V, the lesson was done in A (explicit choice) and failed: candidates V and K
    history = [result(1, "V", 80), result(2, "A", 40)]
    suggestion = retry_suggestion(
        history[-1], pct(55, 23, 22), stats_of(*history), pct(45, 40, 15), history
    )
    assert suggestion.failed.form == "A"
    assert suggestion.suggested.form == "V"
    assert suggestion.suggested.reason == "confirmed"
    assert suggestion.suggested.best == LessonScore(1, "Lekcja 1", 80)


def test_previous_result_is_from_another_lesson_and_counted():
    history = [
        result(1, "V", 60),
        result(2, "V", 50),
        result(2, "V", 20, counted=False),
        result(2, "V", 40, counted=False),
    ]
    suggestion = retry_suggestion(
        history[-1], pct(40, 40, 20), stats_of(*history), pct(45, 40, 15), history
    )
    # the earlier attempts in lesson 2 are skipped: previous = lesson 1
    assert suggestion.failed.previous == LessonScore(1, "Lekcja 1", 60)


# --- R5. Strength of the suggestion --------------------------------------------------------------


def strength_of(*history: Result) -> str:
    items = list(history)
    survey = pct(45, 40, 15)
    return retry_suggestion(items[-1], survey, stats_of(*items), survey, items).strength


def test_soft_after_a_passed_previous_result_in_the_form():
    assert strength_of(result(1, "V", 80), result(2, "V", 40)) == "soft"


def test_strong_after_a_failed_previous_result_in_the_form():
    # second failure in a row in V
    assert strength_of(result(1, "V", 40), result(2, "V", 60)) == "strong"


def test_strong_without_a_previous_counted_result_in_the_form():
    assert strength_of(result(1, "V", 40)) == "strong"
    # results in other forms do not count
    assert strength_of(result(1, "A", 80), result(2, "K", 100), result(3, "V", 40)) == "strong"


def test_strength_looks_at_the_most_recent_counted_result_in_the_form():
    # both directions: an older pass does not soften a newer failure and vice versa
    assert strength_of(result(1, "V", 80), result(2, "V", 40), result(3, "V", 60)) == "strong"
    assert strength_of(result(1, "V", 40), result(2, "V", 80), result(3, "V", 60)) == "soft"


def test_strength_skips_not_counted_results():
    # a passed retry in lesson 1 is not counted: the counted result there failed
    history = (result(1, "V", 40), result(1, "V", 80, counted=False), result(2, "V", 40))
    assert strength_of(*history) == "strong"
    history = (result(1, "V", 80), result(2, "V", 0, counted=False), result(3, "V", 40))
    assert strength_of(*history) == "soft"


def test_strength_of_a_not_counted_retry_in_the_same_form():
    # the retry itself is excluded; the previous counted V result is lesson 1's first attempt
    assert strength_of(result(1, "V", 40), result(1, "V", 60, counted=False)) == "strong"
    history = (result(1, "V", 80), result(2, "V", 40), result(2, "V", 60, counted=False))
    assert strength_of(*history) == "strong"  # lesson 2's counted V failed
    history = (result(1, "V", 40), result(2, "V", 80), result(2, "V", 60, counted=False))
    assert strength_of(*history) == "soft"  # lesson 2's counted V passed


def test_strength_of_a_failure_in_a_chosen_form():
    # style V, lesson redone in A: A's previous counted result decides
    history = (result(1, "A", 80), result(2, "V", 40), result(2, "A", 60))
    assert strength_of(*history) == "soft"


# --- R6. Switch proposal -------------------------------------------------------------------------

KUBA = [
    result(1, "V", 80),
    result(2, "V", 40),
    result(2, "V", 80, counted=False),
    result(3, "V", 40),
    result(3, "A", 80),
]


def test_proposal_for_kuba_with_evidence():
    draft = switch_proposal("V", pct(28, 57, 15), stats_of(*KUBA), [], trial_active=False)
    assert draft is not None
    assert (draft.kind, draft.from_style, draft.to_style) == ("switch", "V", "A")
    assert draft.evidence == {
        "from": {"form": "V", "lessons": 3, "average": 53, "percent": 28},
        "to": {"form": "A", "lessons": 1, "average": 80, "percent": 57},
    }


def test_no_proposal_for_an_unconfirmed_higher_form():
    history = [result(1, "V", 40), result(2, "V", 40)]
    assert switch_proposal("V", pct(25, 55, 20), stats_of(*history), [], False) is None


def test_no_proposal_when_the_confirmed_form_is_not_higher():
    history = [result(1, "V", 80), result(2, "A", 80)]
    assert switch_proposal("V", pct(50, 30, 20), stats_of(*history), [], False) is None


def test_no_proposal_during_a_trial_or_without_a_style():
    stats = stats_of(*KUBA)
    assert switch_proposal("V", pct(28, 57, 15), stats, [], trial_active=True) is None
    assert switch_proposal(None, pct(28, 57, 15), stats, [], trial_active=False) is None


def test_proposal_picks_highest_percentage_then_average_then_order():
    history = [result(1, "A", 80), result(2, "K", 90), result(3, "V", 40)]
    stats = stats_of(*history)
    assert switch_proposal("V", pct(20, 45, 35), stats, [], False).to_style == "A"
    assert switch_proposal("V", pct(20, 40, 40), stats, [], False).to_style == "K"
    history = [result(1, "A", 80), result(2, "K", 80), result(3, "V", 40)]
    assert switch_proposal("V", pct(20, 40, 40), stats_of(*history), [], False).to_style == "A"


def test_rejected_proposal_returns_after_two_new_counted_results():
    stats = stats_of(*KUBA)  # 4 counted results
    rejected_now = [Rejection(to="A", counted_at_decision=4)]
    assert switch_proposal("V", pct(28, 57, 15), stats, rejected_now, False) is None
    one_more = stats_of(*KUBA, result(4, "V", 60))
    assert switch_proposal("V", pct(28, 57, 15), one_more, rejected_now, False) is None
    two_more = stats_of(*KUBA, result(4, "V", 60), result(5, "V", 60))
    draft = switch_proposal("V", pct(28, 57, 15), two_more, rejected_now, False)
    assert draft is not None and draft.to_style == "A"


def test_not_counted_results_do_not_renew_a_rejected_proposal():
    rejected_now = [Rejection(to="A", counted_at_decision=4)]
    retries = stats_of(*KUBA, result(3, "A", 90, counted=False), result(3, "A", 100, counted=False))
    assert switch_proposal("V", pct(28, 57, 15), retries, rejected_now, False) is None


def test_rejection_of_another_form_does_not_block():
    rejected = [Rejection(to="K", counted_at_decision=4)]
    assert switch_proposal("V", pct(28, 57, 15), stats_of(*KUBA), rejected, False) is not None


# --- R6. Clearing lesson form choices ------------------------------------------------------------


def test_forms_to_clear_only_lessons_not_passed():
    assert forms_to_clear({3: "A", 5: "K", 4: "V"}, passed_lesson_ids={3}) == [4, 5]


def test_forms_to_clear_without_choices():
    assert forms_to_clear({}, passed_lesson_ids={1, 2}) == []


def test_forms_to_clear_all_passed():
    assert forms_to_clear({1: "A"}, passed_lesson_ids={1}) == []


# --- R7. Trial period ----------------------------------------------------------------------------


def test_trial_marta_helped():
    after = [result(2, "V", 100), result(3, "V", 80)]
    outcome = trial_outcome(40, "V", after)
    assert outcome is not None
    assert (outcome.after_average, outcome.result) == (90, "helped")
    assert not outcome.propose_revert


@pytest.mark.parametrize(
    ("after", "expected"),
    [
        ((70, 70), "helped"),  # +10
        ((70, 68), "neutral"),  # +9
        ((50, 52), "neutral"),  # -9
        ((50, 50), "worse"),  # -10
        ((60, 60), "neutral"),  # 0
    ],
)
def test_trial_thresholds(after, expected):
    outcome = trial_outcome(60, "A", [result(i, "A", p) for i, p in enumerate(after)])
    assert outcome is not None and outcome.result == expected
    assert outcome.propose_revert == (expected == "worse")


def test_trial_without_baseline():
    outcome = trial_outcome(None, "A", [result(1, "A", 80), result(2, "A", 90)])
    assert outcome is not None
    assert (outcome.after_average, outcome.result) == (85, "no_baseline")


def test_trial_waits_for_two_counted_results_in_the_new_form():
    assert trial_outcome(40, "A", []) is None
    assert trial_outcome(40, "A", [result(1, "A", 80)]) is None
    other_forms = [result(1, "A", 80), result(2, "V", 90), result(2, "A", 90, counted=False)]
    assert trial_outcome(40, "A", other_forms) is None
    assert trial_progress("A", other_forms) == 1


def test_trial_uses_the_first_two_results():
    outcome = trial_outcome(40, "A", [result(1, "A", 80), result(2, "A", 60), result(3, "A", 0)])
    assert outcome is not None and outcome.after_average == 70
    assert trial_progress("A", [result(i, "A", 80) for i in range(3)]) == 2


def test_trial_baseline_last_two_counted_in_the_previous_style():
    assert trial_baseline(KUBA, "V") == 40  # lessons 2 and 3 (40, 40); lesson 1 is older
    assert trial_baseline([result(1, "K", 40), result(1, "V", 80)], "K") == 40  # Marta
    assert trial_baseline([result(1, "V", 80)], "K") is None


# --- R7a. Style change during a trial ------------------------------------------------------------

A_TO_V = TrialInfo(id=7, from_style="A", to_style="V", before_average=100)


def test_style_change_without_trial_starts_one():
    assert trial_on_style_change(None, 0, "V", "A", 100) == TrialDecision("start", "A", 100)


def test_going_back_before_any_lesson_cancels_the_trial():
    # Patryk's path: A (2 x 100%) -> V -> A without a lesson in V
    assert trial_on_style_change(A_TO_V, 0, "A", "V", None) == TrialDecision("cancel", None, None)


def test_third_style_before_any_lesson_keeps_the_original_baseline():
    # A -> V -> K without a lesson in V: trial A -> K, baseline from A
    assert trial_on_style_change(A_TO_V, 0, "K", "V", None) == TrialDecision("replace", "A", 100)


@pytest.mark.parametrize("counted", [1, 2])
def test_after_counted_lessons_a_new_trial_starts_as_before(counted):
    for new_style in ("A", "K"):
        decision = trial_on_style_change(A_TO_V, counted, new_style, "V", 60)
        assert decision == TrialDecision("start", "V", 60)


def test_accepted_revert_starts_no_trial():
    assert trial_on_style_change(None, 0, "A", "V", 80, starts_trial=False) == TrialDecision(
        "none", None, None
    )
    running = trial_on_style_change(A_TO_V, 1, "A", "V", 80, starts_trial=False)
    assert running == TrialDecision("none", None, None)
    # Going back before any lesson is still an undo
    assert trial_on_style_change(A_TO_V, 0, "A", "V", 80, starts_trial=False).action == "cancel"


# --- R8. Course hint -----------------------------------------------------------------------------


def course_result(student: int, form: str, percent: int, counted: bool = True) -> CourseResult:
    return CourseResult(student_id=student, form=form, percent=percent, counted=counted)


def test_hint_best_average_with_at_least_two_students():
    results = [
        course_result(1, "A", 80),
        course_result(2, "A", 90),
        course_result(3, "A", 85),
        course_result(4, "V", 60),
        course_result(5, "V", 60),
        course_result(6, "K", 100),  # one student only
        course_result(2, "A", 20, counted=False),  # retries do not count
    ]
    assert course_hint(results, student_id=99) == Hint("A", 85, 3, 3)


def test_hint_tie_more_students_then_order():
    results = [
        course_result(1, "V", 80),
        course_result(2, "V", 80),
        course_result(3, "K", 80),
        course_result(4, "K", 80),
        course_result(5, "K", 80),
    ]
    assert course_hint(results, 99).form == "K"
    results = [
        course_result(1, "K", 80),
        course_result(2, "K", 80),
        course_result(3, "A", 80),
        course_result(4, "A", 80),
    ]
    assert course_hint(results, 99).form == "A"


def test_no_hint_for_a_student_with_results_or_without_data():
    results = [course_result(1, "A", 80), course_result(2, "A", 90)]
    assert course_hint(results, student_id=1) is None
    assert course_hint([course_result(1, "A", 80)], student_id=99) is None
    assert course_hint([], student_id=99) is None


# --- R12. A run of failures ----------------------------------------------------------------------


def test_attention_after_three_counted_failures():
    history = [result(1, "V", 80), result(2, "V", 60), result(3, "A", 40), result(4, "V", 0)]
    assert attention(history) == Attention(
        streak=3,
        results=(
            FormScore(2, "Lekcja 2", "V", 60),
            FormScore(3, "Lekcja 3", "A", 40),
            FormScore(4, "Lekcja 4", "V", 0),
        ),
    )
    assert ATTENTION_STREAK == 3


def test_no_attention_after_two_failures():
    assert attention([result(1, "V", 80), result(2, "V", 60), result(3, "V", 40)]) is None
    assert attention([result(1, "V", 60), result(2, "V", 40)]) is None
    assert attention([]) is None


def test_attention_streak_grows_and_keeps_the_last_three():
    history = [result(lesson, "V", 40) for lesson in range(1, 6)]
    found = attention(history)
    assert found is not None
    assert found.streak == 5
    assert [item.lesson_id for item in found.results] == [3, 4, 5]


def test_attention_skips_not_counted_results():
    history = [
        result(1, "V", 40),
        result(1, "V", 80, counted=False),  # a passed retry does not end the run
        result(2, "V", 20),
        result(2, "V", 0, counted=False),  # a failed retry does not extend it
        result(3, "A", 60),
    ]
    found = attention(history)
    assert found is not None
    assert found.streak == 3
    assert [(item.lesson_id, item.percent) for item in found.results] == [(1, 40), (2, 20), (3, 60)]
    assert attention(history[:4]) is None  # 2 counted failures only


def test_a_counted_pass_ends_the_attention():
    failures = [result(1, "V", 40), result(2, "V", 40), result(3, "V", 40)]
    assert attention(failures) is not None
    assert attention([*failures, result(4, "A", 80)]) is None
    assert attention([*failures, result(4, "A", 80), result(5, "A", 60)]) is None
