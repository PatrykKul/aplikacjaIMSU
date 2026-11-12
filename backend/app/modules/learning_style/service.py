"""Learning-style service: survey, profile, style changes, lesson forms, journal, statistics.

The decisions come from `rules.py` (pure functions); this module loads the data they need,
stores what they decide and writes every decision to the journal (`decision_events`).
Lesson and course titles are read by primary key through the `curriculum` models — the same
exception as in v2 (`03-architektura.md`): titles are part of the evidence the student sees.
"""

from collections.abc import Collection, Iterable, Sequence
from dataclasses import asdict
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.sql.functions import Function

from app.core.errors import AppError
from app.modules.content import service as content
from app.modules.curriculum import service as curriculum
from app.modules.curriculum.models import Course, Lesson
from app.modules.identity import service as identity
from app.modules.identity.models import User, UserRole
from app.modules.learning_style import rules, stats
from app.modules.learning_style.models import (
    DecisionEvent,
    LearningProfile,
    LessonForm,
    QuizResult,
    StyleHistory,
    StyleProposal,
    StyleTrial,
    SurveyQuestion,
    SurveyResult,
)
from app.modules.learning_style.schemas import (
    CourseHint,
    CourseProgressResponse,
    CourseStatsResponse,
    CourseStudentResponse,
    FormEffectResponse,
    FormStatsResponse,
    HistoryPointResponse,
    JournalEntry,
    LastResultResponse,
    LearningProfileResponse,
    LessonRefResponse,
    LessonResultResponse,
    OpenProposalBrief,
    ProgressResponse,
    Proposal,
    RefResponse,
    RetrySuggestion,
    StudentDetailResponse,
    StudentRefResponse,
    StudyResponse,
    SurveyChoice,
    SurveySummaryResponse,
    Trial,
)
from app.modules.learning_style.scoring import compute_score

SOURCE_SURVEY = "survey"
SOURCE_TIE_CHOICE = "tie_choice"
SOURCE_MANUAL = "manual"
SOURCE_PROPOSAL = "proposal"


def now() -> Function[Any]:
    """Wall-clock time of the statement: distinct even inside one transaction.

    Trials compare result times with their start, so rows written in one request (and in tests,
    which run in one transaction) must not share the transaction's `now()`.
    """
    return func.clock_timestamp()


# --- Access --------------------------------------------------------------------------------------


def get_profile(db: Session, user_id: int) -> LearningProfile | None:
    return db.get(LearningProfile, user_id)


def require_student(user: User) -> None:
    if user.role != UserRole.STUDENT:
        raise AppError(403, "FORBIDDEN")


def require_style(db: Session, user: User) -> LearningProfile:
    """A student with an active style; without the survey or with an unresolved tie -> 403."""
    require_student(user)
    profile = get_profile(db, user.id)
    if profile is None or profile.style is None:
        raise AppError(403, "SURVEY_REQUIRED")
    return profile


# --- Decision log and history --------------------------------------------------------------------


def log_event(
    db: Session,
    user_id: int,
    type_: str,
    data: dict[str, Any],
    *,
    course_id: int | None = None,
    lesson_id: int | None = None,
) -> DecisionEvent:
    """Write one decision with the data it came from (flushed, so it has an id)."""
    event = DecisionEvent(
        user_id=user_id,
        type=type_,
        course_id=course_id,
        lesson_id=lesson_id,
        data=data,
        created_at=now(),
    )
    db.add(event)
    db.flush()
    return event


def record_history(db: Session, profile: LearningProfile, event: DecisionEvent) -> None:
    """Profile after a change (survey, counted result, style change) — a point of the chart."""
    db.add(
        StyleHistory(
            user_id=profile.user_id,
            percent_v=profile.percent_v,
            percent_a=profile.percent_a,
            percent_k=profile.percent_k,
            style=profile.style,
            event_id=event.id,
            created_at=now(),
        )
    )


# --- Survey --------------------------------------------------------------------------------------


def active_questions(db: Session) -> list[SurveyQuestion]:
    return list(
        db.scalars(
            select(SurveyQuestion)
            .options(selectinload(SurveyQuestion.answers))
            .where(SurveyQuestion.is_active)
            .order_by(SurveyQuestion.position, SurveyQuestion.id)
        )
    )


def survey_result(db: Session, user_id: int) -> SurveyResult | None:
    return db.scalar(
        select(SurveyResult)
        .where(SurveyResult.user_id == user_id)
        .order_by(SurveyResult.id.desc())
        .limit(1)
    )


def _points(result: SurveyResult) -> dict[str, int]:
    return {"V": result.points_v, "A": result.points_a, "K": result.points_k}


def survey_percentages(db: Session, user_id: int) -> dict[str, int]:
    """Percentages straight from the survey (R1), e.g. for the retry suggestion."""
    result = survey_result(db, user_id)
    assert result is not None, "a student with a profile has a survey result"
    return rules.survey_percentages(_points(result))


def submit_survey(db: Session, user: User, choices: Sequence[SurveyChoice]) -> LearningProfile:
    """Score the survey (once): percentages (R1) and the style, or a tie to choose from."""
    require_student(user)
    if get_profile(db, user.id) is not None:
        raise AppError(409, "SURVEY_ALREADY_DONE")
    questions = active_questions(db)
    if not questions:
        raise AppError(409, "SURVEY_EMPTY")
    chosen = {choice.question_id: choice.answer_id for choice in choices}
    if len(chosen) != len(choices):
        raise AppError(400, "SURVEY_DUPLICATE_ANSWER")
    if chosen.keys() != {question.id for question in questions}:
        raise AppError(400, "SURVEY_INCOMPLETE")
    styles = []
    for question in questions:
        answer = next((a for a in question.answers if a.id == chosen[question.id]), None)
        if answer is None:
            raise AppError(400, "SURVEY_ANSWER_MISMATCH")
        styles.append(answer.style)

    points = compute_score(styles).points
    percentages = rules.survey_percentages(points)
    leaders = rules.survey_leaders(points)
    style = leaders[0] if len(leaders) == 1 else None
    db.add(
        SurveyResult(
            user_id=user.id,
            points_v=points["V"],
            points_a=points["A"],
            points_k=points["K"],
            dominant_style="".join(leaders),
        )
    )
    profile = LearningProfile(user_id=user.id, style=style, style_source=SOURCE_SURVEY)
    profile.percentages = percentages
    db.add(profile)
    event = log_event(
        db,
        user.id,
        "survey_completed",
        {
            "points": points,
            "percentages": percentages,
            "style": style,
            "tie_styles": leaders if style is None else [],
        },
    )
    record_history(db, profile, event)
    db.commit()
    return profile


def choose_tie_style(db: Session, user: User, style: str) -> LearningProfile:
    """After a survey tie the student picks one of the tied styles."""
    require_student(user)
    profile = get_profile(db, user.id)
    if profile is None:
        raise AppError(403, "SURVEY_REQUIRED")
    if profile.style is not None:
        raise AppError(409, "NO_TIE")
    result = survey_result(db, user.id)
    assert result is not None
    tie_styles = list(result.dominant_style)
    if style not in tie_styles:
        raise AppError(400, "STYLE_NOT_TIED")
    profile.style = style
    profile.style_source = SOURCE_TIE_CHOICE
    event = log_event(db, user.id, "tie_resolved", {"style": style, "tie_styles": tie_styles})
    record_history(db, profile, event)
    db.commit()
    return profile


# --- Results as rule inputs ----------------------------------------------------------------------


def user_results(db: Session, user_id: int) -> list[QuizResult]:
    """All results of the student, in the order they were recorded."""
    return list(
        db.scalars(select(QuizResult).where(QuizResult.user_id == user_id).order_by(QuizResult.id))
    )


def lesson_titles(db: Session, lesson_ids: Iterable[int]) -> dict[int, str]:
    ids = set(lesson_ids)
    if not ids:
        return {}
    query = select(Lesson.id, Lesson.title).where(Lesson.id.in_(ids))
    return {lesson_id: title for lesson_id, title in db.execute(query)}


def rule_results(db: Session, rows: Sequence[QuizResult]) -> list[rules.Result]:
    titles = lesson_titles(db, (row.lesson_id for row in rows))
    return [
        rules.Result(
            lesson_id=row.lesson_id,
            lesson_title=titles.get(row.lesson_id, ""),
            form=row.form,
            percent=row.percent,
            passed=row.passed,
            counted=row.counted,
        )
        for row in rows
    ]


# --- Proposals and trials ------------------------------------------------------------------------


def open_proposal(db: Session, user_id: int) -> StyleProposal | None:
    query = select(StyleProposal).where(
        StyleProposal.user_id == user_id, StyleProposal.status == "open"
    )
    return db.scalar(query)


def rejections(db: Session, user_id: int) -> list[rules.Rejection]:
    rows = db.scalars(
        select(StyleProposal).where(
            StyleProposal.user_id == user_id, StyleProposal.status == "rejected"
        )
    )
    return [rules.Rejection(row.to_style, row.counted_at_decision or 0) for row in rows]


def running_trial(db: Session, user_id: int) -> StyleTrial | None:
    return db.scalar(
        select(StyleTrial).where(StyleTrial.user_id == user_id, StyleTrial.finished_at.is_(None))
    )


def last_trial(db: Session, user_id: int) -> StyleTrial | None:
    return db.scalar(
        select(StyleTrial)
        .where(StyleTrial.user_id == user_id)
        .order_by(StyleTrial.id.desc())
        .limit(1)
    )


def trial_results(db: Session, trial: StyleTrial) -> list[rules.Result]:
    """Results recorded since the trial started (until it finished)."""
    query = select(QuizResult).where(
        QuizResult.user_id == trial.user_id, QuizResult.created_at >= trial.started_at
    )
    if trial.finished_at is not None:
        query = query.where(QuizResult.created_at <= trial.finished_at)
    return rule_results(db, list(db.scalars(query.order_by(QuizResult.id))))


def counted_total(db: Session, user_id: int) -> int:
    query = select(func.count()).where(QuizResult.user_id == user_id, QuizResult.counted)
    return db.scalar(query) or 0


def close_proposal(db: Session, proposal: StyleProposal, status: str) -> None:
    proposal.status = status
    proposal.decided_at = now()
    proposal.counted_at_decision = counted_total(db, proposal.user_id)
    db.flush()  # at most one open proposal: close before a new one is created


def proposal_data(proposal: StyleProposal) -> dict[str, Any]:
    return {
        "proposal_id": proposal.id,
        "kind": proposal.kind,
        "from": proposal.from_style,
        "to": proposal.to_style,
    }


def create_proposal(
    db: Session,
    user_id: int,
    draft: rules.ProposalDraft,
    *,
    course_id: int | None = None,
    lesson_id: int | None = None,
) -> StyleProposal:
    proposal = StyleProposal(
        user_id=user_id,
        kind=draft.kind,
        from_style=draft.from_style,
        to_style=draft.to_style,
        evidence=draft.evidence,
        status="open",
        created_at=now(),
    )
    db.add(proposal)
    db.flush()
    log_event(
        db,
        user_id,
        "proposal_created",
        {**proposal_data(proposal), "evidence": draft.evidence},
        course_id=course_id,
        lesson_id=lesson_id,
    )
    return proposal


def start_trial(db: Session, user_id: int, from_style: str, to_style: str, source: str) -> None:
    """Two lessons in the new style, compared with the last results in the previous one (R7)."""
    before = rules.trial_baseline(rule_results(db, user_results(db, user_id)), from_style)
    trial = StyleTrial(
        user_id=user_id,
        from_style=from_style,
        to_style=to_style,
        source=source,
        before_average=before,
        started_at=now(),
    )
    db.add(trial)
    db.flush()
    log_event(
        db,
        user_id,
        "trial_started",
        {
            "trial_id": trial.id,
            "from": from_style,
            "to": to_style,
            "source": source,
            "before_average": before,
        },
    )


def _stop_running_trial(db: Session, user_id: int) -> None:
    """A trial interrupted by another style change ends without a result."""
    trial = running_trial(db, user_id)
    if trial is not None:
        trial.finished_at = now()
        db.flush()


# --- Style changes -------------------------------------------------------------------------------


def _switch_style(
    db: Session, profile: LearningProfile, to_style: str, source: str
) -> list[dict[str, Any]]:
    """Set the active style and clear form choices in lessons not passed yet (R6)."""
    choices = list(db.scalars(select(LessonForm).where(LessonForm.user_id == profile.user_id)))
    chosen = {choice.lesson_id: choice.form for choice in choices}
    passed = curriculum.passed_lesson_ids(db, profile.user_id, list(chosen))
    to_clear = rules.forms_to_clear(chosen, passed)
    titles = lesson_titles(db, to_clear)
    cleared = [
        {"lesson_id": id_, "lesson_title": titles.get(id_, ""), "form": chosen[id_]}
        for id_ in to_clear
    ]
    for choice in choices:
        if choice.lesson_id in to_clear:
            db.delete(choice)
    profile.style = to_style
    profile.style_source = source
    return cleared


def change_style_manually(db: Session, user: User, style: str) -> LearningProfile:
    """Manual change: percentages stay, open proposal superseded, a new trial starts."""
    profile = require_style(db, user)
    previous = profile.style
    assert previous is not None
    if style == previous:
        raise AppError(409, "SAME_STYLE")
    proposal = open_proposal(db, user.id)
    if proposal is not None:
        close_proposal(db, proposal, "superseded")
    _stop_running_trial(db, user.id)
    cleared = _switch_style(db, profile, style, SOURCE_MANUAL)
    event = log_event(
        db,
        user.id,
        "manual_style_change",
        {
            "from": previous,
            "to": style,
            "cleared_lessons": cleared,
            "superseded_proposal_id": None if proposal is None else proposal.id,
        },
    )
    record_history(db, profile, event)
    start_trial(db, user.id, previous, style, SOURCE_MANUAL)
    db.commit()
    return profile


def _own_open_proposal(db: Session, user: User, proposal_id: int) -> StyleProposal:
    proposal = db.get(StyleProposal, proposal_id)
    if proposal is None or proposal.user_id != user.id:
        raise AppError(404, "PROPOSAL_NOT_FOUND")
    if proposal.status != "open":
        raise AppError(409, "PROPOSAL_NOT_OPEN")
    return proposal


def accept_proposal(db: Session, user: User, proposal_id: int) -> LearningProfile:
    """Switch to the proposed style; a `switch` starts a trial, a `revert` does not."""
    profile = require_style(db, user)
    proposal = _own_open_proposal(db, user, proposal_id)
    close_proposal(db, proposal, "accepted")
    _stop_running_trial(db, user.id)
    previous = profile.style
    assert previous is not None
    cleared = _switch_style(db, profile, proposal.to_style, SOURCE_PROPOSAL)
    event = log_event(
        db,
        user.id,
        "proposal_accepted",
        {**proposal_data(proposal), "cleared_lessons": cleared},
    )
    record_history(db, profile, event)
    if proposal.kind == "switch":
        start_trial(db, user.id, previous, proposal.to_style, SOURCE_PROPOSAL)
    db.commit()
    return profile


def reject_proposal(db: Session, user: User, proposal_id: int) -> LearningProfile:
    """The style stays; the same form may be proposed again after RENEW_AFTER counted results."""
    profile = require_style(db, user)
    proposal = _own_open_proposal(db, user, proposal_id)
    close_proposal(db, proposal, "rejected")
    log_event(db, user.id, "proposal_rejected", proposal_data(proposal))
    db.commit()
    return profile


# --- Responses: profile --------------------------------------------------------------------------


def proposal_response(proposal: StyleProposal) -> Proposal:
    return Proposal(
        id=proposal.id,
        kind=proposal.kind,
        from_=proposal.from_style,
        to=proposal.to_style,
        evidence=proposal.evidence,
        created_at=proposal.created_at,
    )


def trial_response(db: Session, trial: StyleTrial) -> Trial:
    return Trial(
        id=trial.id,
        from_=trial.from_style,
        to=trial.to_style,
        source=trial.source,
        before_average=trial.before_average,
        after_average=trial.after_average,
        result=trial.result,
        done=rules.trial_progress(trial.to_style, trial_results(db, trial)),
        needed=rules.TRIAL_LESSONS,
        started_at=trial.started_at,
        finished_at=trial.finished_at,
    )


def profile_response(db: Session, user: User) -> LearningProfileResponse:
    profile = get_profile(db, user.id) if user.role == UserRole.STUDENT else None
    if profile is None:
        return LearningProfileResponse(
            survey_completed=False,
            style=None,
            style_source=None,
            tie_styles=[],
            percentages=None,
            forms=None,
            survey=None,
            open_proposal=None,
            trial=None,
        )
    result = survey_result(db, user.id)
    assert result is not None
    form_stats = rules.form_stats(rule_results(db, user_results(db, user.id)))
    proposal = open_proposal(db, user.id)
    trial = last_trial(db, user.id)
    return LearningProfileResponse(
        survey_completed=True,
        style=profile.style,
        style_source=profile.style_source,
        tie_styles=list(result.dominant_style) if profile.style is None else [],
        percentages=profile.percentages,
        forms={form: FormStatsResponse(**asdict(item)) for form, item in form_stats.items()},
        survey=SurveySummaryResponse(
            points=_points(result),
            percentages=rules.survey_percentages(_points(result)),
            created_at=result.created_at,
        ),
        open_proposal=None if proposal is None else proposal_response(proposal),
        trial=None if trial is None else trial_response(db, trial),
    )


# --- Studying a lesson ---------------------------------------------------------------------------


def lesson_form(db: Session, user_id: int, lesson_id: int, style: str) -> tuple[str, str]:
    """(form, source): an explicit choice for the lesson, otherwise the active style."""
    choice = db.get(LessonForm, (user_id, lesson_id))
    if choice is None:
        return style, "style"
    return choice.form, "choice"


def _last_result_in_lesson(db: Session, user_id: int, lesson_id: int) -> QuizResult | None:
    return db.scalar(
        select(QuizResult)
        .where(QuizResult.user_id == user_id, QuizResult.lesson_id == lesson_id)
        .order_by(QuizResult.id.desc())
        .limit(1)
    )


def _study_suggestion(
    db: Session, user_id: int, lesson_id: int, last: QuizResult | None, form: str
) -> RetrySuggestion | None:
    """The suggestion of the last attempt while it failed and the student has not switched yet."""
    if last is None or last.passed:
        return None
    event = db.scalar(
        select(DecisionEvent)
        .where(
            DecisionEvent.user_id == user_id,
            DecisionEvent.lesson_id == lesson_id,
            DecisionEvent.type == "retry_suggestion",
        )
        .order_by(DecisionEvent.id.desc())
        .limit(1)
    )
    if event is None:
        return None
    suggestion = RetrySuggestion.model_validate(event.data)
    return None if suggestion.suggested.form == form else suggestion


def _study_response(
    db: Session, lesson: Lesson, user: User, profile: LearningProfile
) -> StudyResponse:
    style = profile.style
    assert style is not None
    form, source = lesson_form(db, user.id, lesson.id, style)
    last = _last_result_in_lesson(db, user.id, lesson.id)
    last_result = None
    if last is not None:
        last_result = LastResultResponse(percent=last.percent, passed=last.passed, form=last.form)
    return StudyResponse(
        lesson_id=lesson.id,
        form=form,
        form_source=source,
        style=style,
        blocks=content.get_version(db, lesson.id, form),
        other_forms=[other for other in rules.FORMS if other != form],
        suggestion=_study_suggestion(db, user.id, lesson.id, last, form),
        last_result=last_result,
    )


def study(db: Session, lesson_id: int, user: User) -> StudyResponse:
    """The lesson version in the student's form (lesson choice or active style)."""
    profile = require_style(db, user)
    lesson = curriculum.get_study_lesson(db, lesson_id, user)
    return _study_response(db, lesson, user, profile)


def set_lesson_form(
    db: Session, lesson_id: int, user: User, form: str, source: str
) -> StudyResponse:
    """Explicit form of one lesson ("redo this lesson in another form"), logged."""
    profile = require_style(db, user)
    lesson = curriculum.get_study_lesson(db, lesson_id, user)
    assert profile.style is not None
    current, _ = lesson_form(db, user.id, lesson.id, profile.style)
    if form != current:
        choice = db.get(LessonForm, (user.id, lesson.id))
        if choice is None:
            db.add(LessonForm(user_id=user.id, lesson_id=lesson.id, form=form))
        else:
            choice.form = form
        log_event(
            db,
            user.id,
            "lesson_form_changed",
            {"from": current, "to": form, "source": source},
            course_id=lesson.course_id,
            lesson_id=lesson.id,
        )
        db.commit()
    return _study_response(db, lesson, user, profile)


# --- Course hint ---------------------------------------------------------------------------------


def course_results(db: Session, course_id: int) -> list[QuizResult]:
    query = select(QuizResult).where(QuizResult.course_id == course_id).order_by(QuizResult.id)
    return list(db.scalars(query))


def as_course_results(rows: Iterable[QuizResult]) -> list[rules.CourseResult]:
    return [rules.CourseResult(r.user_id, r.form, r.percent, r.counted) for r in rows]


def course_hint(db: Session, course_id: int, user: User) -> CourseHint | None:
    """R8: the form that works best for others in this course (student without results)."""
    require_student(user)
    course = curriculum.get_visible_course(db, course_id, user)
    if not curriculum.is_accepted(db, course.id, user.id):
        raise AppError(403, "ENROLLMENT_REQUIRED")
    hint = rules.course_hint(as_course_results(course_results(db, course.id)), user.id)
    return None if hint is None else CourseHint(**asdict(hint))


# --- Progress and journal ------------------------------------------------------------------------


def history(db: Session, user_id: int) -> list[HistoryPointResponse]:
    rows = db.scalars(
        select(StyleHistory)
        .where(StyleHistory.user_id == user_id)
        .order_by(StyleHistory.created_at, StyleHistory.id)
    )
    return [
        HistoryPointResponse(
            at=row.created_at,
            percentages={"V": row.percent_v, "A": row.percent_a, "K": row.percent_k},
            style=row.style,
        )
        for row in rows
    ]


def lesson_ref(lesson: Lesson) -> LessonRefResponse:
    return LessonRefResponse(
        id=lesson.id, title=lesson.title, number=curriculum.lesson_number(lesson)
    )


def _next_lesson(db: Session, course: Course, user_id: int) -> LessonRefResponse | None:
    """The first published lesson not passed yet (it is always the available one, R10)."""
    lessons = curriculum.published_lessons(course)
    passed = curriculum.passed_lesson_ids(db, user_id, [lesson.id for lesson in lessons])
    lesson = next((lesson for lesson in lessons if lesson.id not in passed), None)
    return None if lesson is None else lesson_ref(lesson)


def lesson_results(
    db: Session, user_id: int, course_id: int | None = None
) -> list[LessonResultResponse]:
    """Every lesson the student attempted, with all attempts (optionally one course only)."""
    rows = user_results(db, user_id)
    if course_id is not None:
        rows = [row for row in rows if row.course_id == course_id]
    found = [db.get(Lesson, lesson_id) for lesson_id in dict.fromkeys(r.lesson_id for r in rows)]
    lessons = sorted(
        (lesson for lesson in found if lesson is not None),
        key=lambda lesson: (lesson.course_id, lesson.position, lesson.id),
    )
    infos = [
        stats.LessonInfo(
            course_id=lesson.course_id,
            course_title=lesson.course.title,
            lesson_id=lesson.id,
            lesson_title=lesson.title,
            number=curriculum.lesson_number(lesson),
        )
        for lesson in lessons
    ]
    attempts = [
        stats.Attempt(r.lesson_id, r.created_at, r.form, r.percent, r.passed, r.counted)
        for r in rows
    ]
    passed = curriculum.passed_lesson_ids(db, user_id, [info.lesson_id for info in infos])
    return [
        LessonResultResponse.model_validate(row)
        for row in stats.lesson_results(infos, attempts, passed)
    ]


def progress(db: Session, user: User) -> ProgressResponse:
    """ "My progress": percentages over time, courses and every attempted lesson."""
    require_student(user)
    courses = []
    for course in curriculum.list_courses(db, user):
        if not curriculum.is_accepted(db, course.id, user.id):
            continue
        passed, total = curriculum.course_progress(db, course, user.id)
        courses.append(
            CourseProgressResponse(
                id=course.id,
                title=course.title,
                passed=passed,
                total=total,
                next_lesson=_next_lesson(db, course, user.id),
            )
        )
    return ProgressResponse(
        history=history(db, user.id), courses=courses, lessons=lesson_results(db, user.id)
    )


def _journal_entries(db: Session, events: Sequence[DecisionEvent]) -> list[JournalEntry]:
    course_ids = {e.course_id for e in events if e.course_id is not None}
    courses: dict[int, str] = {}
    if course_ids:
        query = select(Course.id, Course.title).where(Course.id.in_(course_ids))
        courses = {course_id: title for course_id, title in db.execute(query)}
    lessons = lesson_titles(db, (e.lesson_id for e in events if e.lesson_id is not None))
    entries = []
    for event in events:
        course = lesson = None
        if event.course_id is not None:
            course = RefResponse(id=event.course_id, title=courses.get(event.course_id, ""))
        if event.lesson_id is not None:
            lesson = RefResponse(id=event.lesson_id, title=lessons.get(event.lesson_id, ""))
        entries.append(
            JournalEntry(
                id=event.id,
                type=event.type,
                at=event.created_at,
                course=course,
                lesson=lesson,
                data=event.data,
            )
        )
    return entries


def journal(db: Session, user: User) -> list[JournalEntry]:
    """The student's decision log, newest first."""
    require_student(user)
    events = db.scalars(
        select(DecisionEvent)
        .where(DecisionEvent.user_id == user.id)
        .order_by(DecisionEvent.created_at.desc(), DecisionEvent.id.desc())
    )
    return _journal_entries(db, list(events))


# --- Teacher: course statistics and student details ----------------------------------------------


def _pending_requests(db: Session, course_id: int) -> int:
    return curriculum.pending_request_count(db, course_id)


def _profiles(db: Session, user_ids: Collection[int]) -> dict[int, LearningProfile]:
    if not user_ids:
        return {}
    rows = db.scalars(select(LearningProfile).where(LearningProfile.user_id.in_(user_ids)))
    return {row.user_id: row for row in rows}


def _open_proposals(db: Session, user_ids: Collection[int]) -> dict[int, StyleProposal]:
    if not user_ids:
        return {}
    rows = db.scalars(
        select(StyleProposal).where(
            StyleProposal.user_id.in_(user_ids), StyleProposal.status == "open"
        )
    )
    return {row.user_id: row for row in rows}


def course_stats(db: Session, course_id: int, teacher: User) -> CourseStatsResponse:
    """Course panel: form effectiveness, styles of the students and a row per student."""
    course = curriculum.get_owned_course(db, course_id, teacher)
    results = course_results(db, course.id)
    student_ids = curriculum.accepted_student_ids(db, course.id)
    profiles = _profiles(db, student_ids)
    proposals = _open_proposals(db, student_ids)
    students = []
    for student in identity.get_users(db, student_ids):
        own = [r for r in results if r.user_id == student.id]
        profile = profiles.get(student.id)
        proposal = proposals.get(student.id)
        passed, total = curriculum.course_progress(db, course, student.id)
        students.append(
            CourseStudentResponse(
                id=student.id,
                display_name=student.display_name,
                email=student.email,
                style=None if profile is None else profile.style,
                percentages=None if profile is None else profile.percentages,
                passed=passed,
                total=total,
                average=stats.counted_average(as_course_results(own)),
                last_activity=max((r.created_at for r in own), default=None),
                open_proposal=None
                if proposal is None
                else OpenProposalBrief(to=proposal.to_style, kind=proposal.kind),
            )
        )
    effects = stats.form_effectiveness(as_course_results(results))
    styles = [None if (p := profiles.get(sid)) is None else p.style for sid in student_ids]
    return CourseStatsResponse(
        forms={form: FormEffectResponse(**asdict(effect)) for form, effect in effects.items()},
        styles=stats.style_distribution(styles),
        students=students,
        pending_requests=_pending_requests(db, course.id),
    )


def student_detail(
    db: Session, course_id: int, student_id: int, teacher: User
) -> StudentDetailResponse:
    """One student of the course: profile, chart, lessons of this course and the journal.

    The journal shows the events of this course and the global ones (survey, style changes).
    """
    course = curriculum.get_owned_course(db, course_id, teacher)
    if student_id not in curriculum.accepted_student_ids(db, course.id):
        raise AppError(404, "STUDENT_NOT_FOUND")
    student = identity.get_users(db, [student_id])[0]
    events = db.scalars(
        select(DecisionEvent)
        .where(
            DecisionEvent.user_id == student.id,
            or_(DecisionEvent.course_id == course.id, DecisionEvent.course_id.is_(None)),
        )
        .order_by(DecisionEvent.created_at.desc(), DecisionEvent.id.desc())
    )
    return StudentDetailResponse(
        student=StudentRefResponse(
            id=student.id, display_name=student.display_name, email=student.email
        ),
        profile=profile_response(db, student),
        history=history(db, student.id),
        lessons=lesson_results(db, student.id, course.id),
        journal=_journal_entries(db, list(events)),
    )
