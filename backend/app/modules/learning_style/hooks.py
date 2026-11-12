"""Contact point for the quiz module: one call after every graded attempt.

`assessment` scores the drawn questions on the server and calls `record_quiz_result`; the
score always comes from the server — no endpoint lets the browser report its own result.
The steps follow docs/08 ("Kolejność w hooks.record_quiz_result"); everything is committed
once at the end.
"""

from dataclasses import asdict

from sqlalchemy.orm import Session

from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Lesson
from app.modules.identity.models import User
from app.modules.learning_style import rules, service
from app.modules.learning_style.models import QuizResult, StyleProposal, StyleTrial
from app.modules.learning_style.schemas import (
    LessonRefResponse,
    PraiseResponse,
    QuizFeedback,
    RetrySuggestion,
)


def record_quiz_result(
    db: Session, *, user: User, lesson: Lesson, draw_id: int | None, percent: int
) -> QuizFeedback:
    """Store the result in the student model and apply rules R2-R7 (one commit)."""
    profile = service.require_style(db, user)
    style = profile.style
    assert style is not None
    where = {"course_id": lesson.course_id, "lesson_id": lesson.id}

    # 1. Form of the lesson at the moment of sending
    form, _ = service.lesson_form(db, user.id, lesson.id, style)

    # 2. Counted only as the first attempt in this form in this lesson (R2)
    earlier = service.user_results(db, user.id)
    counted = rules.is_counted({r.form for r in earlier if r.lesson_id == lesson.id}, form)
    passed = rules.is_passed(percent)
    row = QuizResult(
        user_id=user.id,
        draw_id=draw_id,
        form=form,
        percent=percent,
        passed=passed,
        counted=counted,
        created_at=service.now(),
        **where,
    )
    db.add(row)
    db.flush()
    before = profile.percentages
    after = rules.apply_result(before, form, passed) if counted else dict(before)
    profile.percentages = after
    results = service.rule_results(db, [*earlier, row])
    form_stats = rules.form_stats(results)

    # 3. Passed: unlock the next lesson, praise a run
    unlocked = None
    course_completed = False
    praise = None
    if passed:
        passed_before, total = curriculum.course_progress(db, lesson.course, user.id)
        unlocked = curriculum.mark_lesson_passed(db, user.id, lesson.id)
        passed_after, _ = curriculum.course_progress(db, lesson.course, user.id)
        course_completed = passed_before < total and passed_after == total
        praise = rules.praise(results)
    unlocked_data = None if unlocked is None else asdict(unlocked)
    attempt_event = service.log_event(
        db,
        user.id,
        "quiz_attempt",
        {
            "draw_id": draw_id,
            "form": form,
            "percent": percent,
            "passed": passed,
            "counted": counted,
            "percentages_before": before,
            "percentages_after": after,
            "unlocked_lesson": unlocked_data,
        },
        **where,
    )
    if counted:
        service.record_history(db, profile, attempt_event)
    if praise is not None:
        service.log_event(db, user.id, "praise", asdict(praise), **where)

    # 4. Failed: suggest another form for this lesson (R5)
    suggestion = None
    if not passed:
        survey = service.survey_percentages(db, user.id)
        suggestion = rules.retry_suggestion(results[-1], after, form_stats, survey, results)
        service.log_event(db, user.id, "retry_suggestion", asdict(suggestion), **where)

    # 5. Trial period: finish after 2 results in the new style, maybe propose going back (R7)
    trial = service.running_trial(db, user.id)
    if trial is not None:
        _update_trial(db, trial, style, after, form_stats, where)

    # 6. Proposal to switch for good (R6): expire an outdated one, create a new one
    _update_switch_proposal(db, user.id, style, after, form_stats, where)

    # 7. One commit for the result, the profile and all decisions
    db.commit()
    proposal = service.open_proposal(db, user.id)
    shown_trial = service.running_trial(db, user.id) or (
        trial if trial is not None and trial.finished_at is not None else None
    )
    return QuizFeedback(
        form=form,
        counted=counted,
        percentages_before=before,
        percentages_after=after,
        passed=passed,
        unlocked_lesson=None if unlocked is None else LessonRefResponse(**unlocked_data),
        course_completed=course_completed,
        praise=None if praise is None else PraiseResponse(**asdict(praise)),
        suggestion=None if suggestion is None else RetrySuggestion(**asdict(suggestion)),
        proposal=None if proposal is None else service.proposal_response(proposal),
        trial=None if shown_trial is None else service.trial_response(db, shown_trial),
    )


def _update_trial(
    db: Session,
    trial: StyleTrial,
    style: str,
    percentages: dict[str, int],
    form_stats: dict[str, rules.FormStats],
    where: dict[str, int],
) -> None:
    outcome = rules.trial_outcome(
        trial.before_average, trial.to_style, service.trial_results(db, trial)
    )
    if outcome is None:
        return
    trial.after_average = outcome.after_average
    trial.result = outcome.result
    trial.finished_at = service.now()
    db.flush()
    service.log_event(
        db,
        trial.user_id,
        "trial_finished",
        {
            "trial_id": trial.id,
            "from": trial.from_style,
            "to": trial.to_style,
            "before_average": trial.before_average,
            "after_average": outcome.after_average,
            "result": outcome.result,
        },
        **where,
    )
    if outcome.propose_revert:
        current = service.open_proposal(db, trial.user_id)
        if current is not None:
            _expire(db, current, where)
        evidence = {
            "from": rules.form_evidence(style, percentages, form_stats),
            "to": rules.form_evidence(trial.from_style, percentages, form_stats),
            "before_average": trial.before_average,
            "after_average": outcome.after_average,
        }
        draft = rules.ProposalDraft("revert", style, trial.from_style, evidence)
        service.create_proposal(db, trial.user_id, draft, **where)


def _update_switch_proposal(
    db: Session,
    user_id: int,
    style: str,
    percentages: dict[str, int],
    form_stats: dict[str, rules.FormStats],
    where: dict[str, int],
) -> None:
    current = service.open_proposal(db, user_id)
    if current is not None and current.kind == "revert":
        return  # waits for the student's decision; not replaced by a switch proposal
    draft = rules.switch_proposal(
        style,
        percentages,
        form_stats,
        service.rejections(db, user_id),
        trial_active=service.running_trial(db, user_id) is not None,
    )
    if current is not None and (draft is None or draft.to_style != current.to_style):
        _expire(db, current, where)
        current = None
    if draft is not None and current is None:
        service.create_proposal(db, user_id, draft, **where)


def _expire(db: Session, proposal: StyleProposal, where: dict[str, int]) -> None:
    service.close_proposal(db, proposal, "expired")
    service.log_event(
        db, proposal.user_id, "proposal_expired", service.proposal_data(proposal), **where
    )
