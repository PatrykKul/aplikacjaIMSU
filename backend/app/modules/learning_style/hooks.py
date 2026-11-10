"""Contact point for the quiz module.

The quiz endpoint scores the answers on the server and then calls `record_quiz_result`.
The returned `QuizFeedback` can be added to the quiz response (e.g. as an `adaptation` field)
and shown with the frontend component `AdaptationFeedback`.

The score always comes from the server: there is deliberately no endpoint where the browser
could report its own result.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.curriculum.models import Lesson
from app.modules.identity.models import User
from app.modules.learning_style import adaptation
from app.modules.learning_style.models import QuizAttempt
from app.modules.learning_style.schemas import QuizFeedback
from app.modules.learning_style.service import get_profile, lesson_style, proposal_response


def record_quiz_result(
    db: Session, *, user: User, lesson_id: int, block_id: str, percent: int
) -> QuizFeedback | None:
    """Save the attempt and update the style weights; commits the session.

    Returns None for teachers / admins and for students without a profile (no survey yet).
    """
    if not 0 <= percent <= 100:
        raise ValueError("percent must be between 0 and 100")
    profile = get_profile(db, user)
    if profile is None:
        return None
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise ValueError(f"lesson {lesson_id} does not exist")

    success = adaptation.is_passed(percent)
    # Letters of the style the student learned in: own style + forms of opened materials
    style = lesson_style(db, profile, lesson_id)
    previous = db.scalars(
        select(QuizAttempt.percent).where(
            QuizAttempt.user_id == user.id,
            QuizAttempt.lesson_id == lesson_id,
            QuizAttempt.style == style,
        )
    )
    counted = adaptation.counts_for_weights(
        (adaptation.is_passed(value) for value in previous), success
    )
    if counted:
        profile.weights = adaptation.update_weights(profile.weights, style, success)
    db.add(
        QuizAttempt(
            user_id=user.id,
            lesson_id=lesson_id,
            block_id=block_id,
            percent=percent,
            style=style,
            counted_for_weights=counted,
        )
    )
    db.commit()
    return QuizFeedback(
        passed=success,
        percent=percent,
        weights=profile.weights,
        weights_changed=counted,
        why=adaptation.quiz_why(lesson.title, percent),
        proposal=proposal_response(profile),
    )
