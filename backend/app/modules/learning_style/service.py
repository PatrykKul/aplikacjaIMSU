from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import AppError
from app.modules.content import service as content
from app.modules.identity.models import User, UserRole
from app.modules.learning_style import adaptation
from app.modules.learning_style.models import (
    LearningProfile,
    SurveyQuestion,
    SurveyResult,
)
from app.modules.learning_style.personalization import (
    SOURCE_ADAPTATION,
    SOURCE_MANUAL,
    SOURCE_SURVEY,
    TEACHER_PREVIEW,
    personalize,
    style_explanation,
)
from app.modules.learning_style.schemas import (
    LearningProfileResponse,
    PersonalizedBlocksResponse,
    StyleProposalResponse,
    SurveyChoice,
    SurveyResultResponse,
)
from app.modules.learning_style.scoring import compute_score

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


def _points(result: SurveyResult) -> dict[str, int]:
    return {"V": result.points_v, "A": result.points_a, "K": result.points_k}


def result_response(result: SurveyResult) -> SurveyResultResponse:
    return SurveyResultResponse(
        points=_points(result), dominant_style=result.dominant_style, created_at=result.created_at
    )


def last_result(db: Session, user_id: int) -> SurveyResult | None:
    return db.scalar(
        select(SurveyResult)
        .where(SurveyResult.user_id == user_id)
        .order_by(SurveyResult.created_at.desc(), SurveyResult.id.desc())
        .limit(1)
    )


def results_history(db: Session, user_id: int) -> list[SurveyResult]:
    return list(
        db.scalars(
            select(SurveyResult)
            .where(SurveyResult.user_id == user_id)
            .order_by(SurveyResult.created_at.desc(), SurveyResult.id.desc())
        )
    )


def submit_survey(db: Session, user: User, choices: list[SurveyChoice]) -> LearningProfile:
    """Score the survey; a new result always replaces the current style (history is kept)."""
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

    score = compute_score(styles)
    db.add(
        SurveyResult(
            user_id=user.id,
            points_v=score.points["V"],
            points_a=score.points["A"],
            points_k=score.points["K"],
            dominant_style=score.dominant_style,
        )
    )
    profile = db.get(LearningProfile, user.id)
    if profile is None:
        profile = LearningProfile(user_id=user.id)
        db.add(profile)
    profile.style = score.dominant_style
    profile.style_source = SOURCE_SURVEY
    profile.weights = adaptation.initial_weights(score.points)
    profile.rejected_proposal = None
    db.commit()
    return profile


# --- Profile -------------------------------------------------------------------------------------


def get_profile(db: Session, user: User) -> LearningProfile | None:
    if user.role != UserRole.STUDENT:
        return None
    return db.get(LearningProfile, user.id)


def require_profile(db: Session, user: User) -> LearningProfile:
    """Students only; others never fill in the survey."""
    if user.role != UserRole.STUDENT:
        raise AppError(403, "FORBIDDEN")
    profile = db.get(LearningProfile, user.id)
    if profile is None:
        raise AppError(403, "SURVEY_REQUIRED")
    return profile


def current_proposal(profile: LearningProfile) -> str | None:
    return adaptation.proposed_style(
        profile.weights, profile.style, profile.style_source, profile.rejected_proposal
    )


def proposal_response(profile: LearningProfile) -> StyleProposalResponse | None:
    style = current_proposal(profile)
    if style is None:
        return None
    return StyleProposalResponse(
        style=style,
        message=adaptation.proposal_message(style),
        why=adaptation.proposal_why(profile.weights, style),
    )


def _explanation(db: Session, profile: LearningProfile) -> str:
    result = last_result(db, profile.user_id)
    return style_explanation(
        profile.style, profile.style_source, _points(result) if result else None
    )


def profile_response(db: Session, user: User) -> LearningProfileResponse:
    profile = get_profile(db, user)
    if profile is None:
        return LearningProfileResponse(survey_completed=False)
    result = last_result(db, user.id)
    return LearningProfileResponse(
        survey_completed=True,
        style=profile.style,
        style_source=profile.style_source,
        weights=profile.weights,
        last_result=result_response(result) if result else None,
        explanation=_explanation(db, profile),
        proposal=proposal_response(profile),
    )


def set_manual_style(db: Session, user: User, style: str) -> None:
    """A manual choice never deletes survey results and turns proposals off."""
    profile = require_profile(db, user)
    profile.style = style
    profile.style_source = SOURCE_MANUAL
    db.commit()


def restore_survey_style(db: Session, user: User) -> None:
    profile = require_profile(db, user)
    result = last_result(db, user.id)
    if result is None:  # a profile is created only together with a result
        raise AppError(403, "SURVEY_REQUIRED")
    profile.style = result.dominant_style
    profile.style_source = SOURCE_SURVEY
    db.commit()


def accept_proposal(db: Session, user: User) -> None:
    profile = require_profile(db, user)
    style = current_proposal(profile)
    if style is None:
        raise AppError(409, "NO_PROPOSAL")
    profile.style = style
    profile.style_source = SOURCE_ADAPTATION
    profile.rejected_proposal = None
    db.commit()


def reject_proposal(db: Session, user: User) -> None:
    profile = require_profile(db, user)
    style = current_proposal(profile)
    if style is None:
        raise AppError(409, "NO_PROPOSAL")
    profile.rejected_proposal = style
    db.commit()


# --- Lessons -------------------------------------------------------------------------------------


def personalized_blocks(db: Session, lesson_id: int, user: User) -> PersonalizedBlocksResponse:
    """Blocks from the content module (same access rules), filtered for a student's style."""
    if user.role != UserRole.STUDENT:
        blocks = content.get_blocks(db, lesson_id, user)
        return PersonalizedBlocksResponse(
            blocks=blocks, style=None, hidden_count=0, explanation=TEACHER_PREVIEW
        )
    profile = require_profile(db, user)
    blocks = content.get_blocks(db, lesson_id, user)
    visible, hidden = personalize(blocks, profile.style)
    return PersonalizedBlocksResponse(
        blocks=visible,
        style=profile.style,
        hidden_count=hidden,
        explanation=_explanation(db, profile),
    )
