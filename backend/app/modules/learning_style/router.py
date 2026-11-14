from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.db import DbSession
from app.modules.identity.dependencies import CurrentUser, TeacherUser, require_role
from app.modules.identity.models import User, UserRole
from app.modules.learning_style import service
from app.modules.learning_style.schemas import (
    CourseHint,
    CourseStatsResponse,
    JournalEntry,
    LearningProfileResponse,
    LessonFormRequest,
    LessonStudyStateResponse,
    ProgressResponse,
    StudentDetailResponse,
    StudentStatsResponse,
    StudyResponse,
    StyleRequest,
    SurveyQuestionResponse,
    SurveySubmitRequest,
)

StudentUser = Annotated[User, Depends(require_role(UserRole.STUDENT))]

survey_router = APIRouter(prefix="/survey", tags=["learning-style"])
profile_router = APIRouter(prefix="/profile/learning-style", tags=["learning-style"])
study_router = APIRouter(prefix="/lessons", tags=["learning-style"])
course_insights_router = APIRouter(prefix="/courses", tags=["learning-style"])
me_router = APIRouter(prefix="/me", tags=["learning-style"])


# --- Survey --------------------------------------------------------------------------------------


@survey_router.get("/questions")
def get_questions(db: DbSession, _user: CurrentUser) -> list[SurveyQuestionResponse]:
    # The response schema has no `style`, so the answer key is never sent
    return [SurveyQuestionResponse.model_validate(q) for q in service.active_questions(db)]


@survey_router.post("/answers")
def submit_answers(
    data: SurveySubmitRequest, db: DbSession, user: StudentUser
) -> LearningProfileResponse:
    service.submit_survey(db, user, data.answers)
    return service.profile_response(db, user)


# --- Profile, style changes, proposals -----------------------------------------------------------


@profile_router.get("")
def get_profile(db: DbSession, user: CurrentUser) -> LearningProfileResponse:
    return service.profile_response(db, user)


@profile_router.post("/tie-choice")
def choose_tie_style(
    data: StyleRequest, db: DbSession, user: StudentUser
) -> LearningProfileResponse:
    service.choose_tie_style(db, user, data.style)
    return service.profile_response(db, user)


@profile_router.put("")
def change_style(data: StyleRequest, db: DbSession, user: StudentUser) -> LearningProfileResponse:
    service.change_style_manually(db, user, data.style)
    return service.profile_response(db, user)


@profile_router.post("/proposals/{proposal_id}/accept")
def accept_proposal(proposal_id: int, db: DbSession, user: StudentUser) -> LearningProfileResponse:
    service.accept_proposal(db, user, proposal_id)
    return service.profile_response(db, user)


@profile_router.post("/proposals/{proposal_id}/reject")
def reject_proposal(proposal_id: int, db: DbSession, user: StudentUser) -> LearningProfileResponse:
    service.reject_proposal(db, user, proposal_id)
    return service.profile_response(db, user)


# --- Studying a lesson ---------------------------------------------------------------------------


@study_router.get("/{lesson_id}/study")
def get_study(lesson_id: int, db: DbSession, user: StudentUser) -> StudyResponse:
    return service.study(db, lesson_id, user)


@study_router.put("/{lesson_id}/study/form")
def set_lesson_form(
    lesson_id: int, data: LessonFormRequest, db: DbSession, user: StudentUser
) -> StudyResponse:
    return service.set_lesson_form(db, lesson_id, user, data.form, data.source)


# --- Course: hint for the student, statistics for the author -------------------------------------


@course_insights_router.get("/{course_id}/study-states")
def get_study_states(
    course_id: int, db: DbSession, user: StudentUser
) -> list[LessonStudyStateResponse]:
    return service.study_states(db, course_id, user)


@course_insights_router.get("/{course_id}/hint")
def get_course_hint(course_id: int, db: DbSession, user: StudentUser) -> CourseHint | None:
    return service.course_hint(db, course_id, user)


@course_insights_router.get("/{course_id}/stats")
def get_course_stats(course_id: int, db: DbSession, user: TeacherUser) -> CourseStatsResponse:
    return service.course_stats(db, course_id, user)


@course_insights_router.get("/{course_id}/students/{student_id}")
def get_student_detail(
    course_id: int, student_id: int, db: DbSession, user: TeacherUser
) -> StudentDetailResponse:
    return service.student_detail(db, course_id, student_id, user)


# --- Student: progress and journal ---------------------------------------------------------------


@me_router.get("/progress")
def get_progress(db: DbSession, user: StudentUser) -> ProgressResponse:
    return service.progress(db, user)


@me_router.get("/journal")
def get_journal(db: DbSession, user: StudentUser) -> list[JournalEntry]:
    return service.journal(db, user)


@me_router.get("/stats")
def get_stats(db: DbSession, user: StudentUser) -> StudentStatsResponse:
    return service.student_stats(db, user)
