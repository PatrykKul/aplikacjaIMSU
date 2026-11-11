from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from app.core.config import get_settings
from app.core.db import DbSession
from app.modules.identity import service
from app.modules.identity.dependencies import AdminUser, CurrentUser, TeacherUser
from app.modules.identity.models import User, UserRole
from app.modules.identity.schemas import (
    EmailFragment,
    LoginRequest,
    ManagedRole,
    RegisterRequest,
    StudentResponse,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.identity.security import create_access_token

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])
students_router = APIRouter(prefix="/students", tags=["users"])


def _set_auth_cookie(response: Response, user: User) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=create_access_token(user.id),
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, response: Response, db: DbSession) -> UserResponse:
    user = service.create_account(db, data)
    _set_auth_cookie(response, user)
    return UserResponse.model_validate(user)


@auth_router.post("/login")
def login(data: LoginRequest, response: Response, db: DbSession) -> UserResponse:
    user = service.authenticate(db, data.email, data.password)
    _set_auth_cookie(response, user)
    return UserResponse.model_validate(user)


@auth_router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.auth_cookie_name,
        path="/",
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


@auth_router.get("/me")
def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@users_router.get("")
def list_users(role: ManagedRole, db: DbSession, _admin: AdminUser) -> list[UserResponse]:
    return [UserResponse.model_validate(user) for user in service.list_users(db, UserRole(role))]


@users_router.post("", status_code=status.HTTP_201_CREATED)
def create_user(data: UserCreateRequest, db: DbSession, _admin: AdminUser) -> UserResponse:
    return UserResponse.model_validate(service.create_account(db, data))


@users_router.patch("/{user_id}")
def update_user(
    user_id: int, data: UserUpdateRequest, db: DbSession, _admin: AdminUser
) -> UserResponse:
    return UserResponse.model_validate(service.update_user(db, user_id=user_id, data=data))


@students_router.get("")
def search_students(
    email: Annotated[EmailFragment, Query()], db: DbSession, _teacher: TeacherUser
) -> list[StudentResponse]:
    return [StudentResponse.model_validate(user) for user in service.search_students(db, email)]
