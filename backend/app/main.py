from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.health import router as health_router
from app.modules.content.router import files_router, lesson_blocks_router
from app.modules.curriculum.router import courses_router, lessons_router
from app.modules.identity.router import auth_router, users_router
from app.modules.learning_style.router import (
    personalized_router,
    profile_router,
    survey_router,
)


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="IMSU v2")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(courses_router)
    app.include_router(lessons_router)
    app.include_router(lesson_blocks_router)
    app.include_router(files_router)
    app.include_router(survey_router)
    app.include_router(profile_router)
    app.include_router(personalized_router)
    return app


app = create_app()
