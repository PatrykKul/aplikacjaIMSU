from fastapi import APIRouter, Response, status

from app.core.config import get_settings
from app.core.db import DbSession
from app.modules.identity import service
from app.modules.identity.dependencies import AdminUser, CurrentUser
from app.modules.identity.models import User
from app.modules.identity.schemas import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.identity.security import create_access_token

auth_router = APIRouter(prefix="/auth", tags=["auth"])
users_router = APIRouter(prefix="/users", tags=["users"])


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
    user = service.register(db, data)
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
def list_users(db: DbSession, _admin: AdminUser) -> list[UserResponse]:
    return [UserResponse.model_validate(user) for user in service.list_users(db)]


@users_router.patch("/{user_id}")
def update_user(
    user_id: int, data: UserUpdateRequest, db: DbSession, admin: AdminUser
) -> UserResponse:
    user = service.update_user(db, user_id=user_id, data=data, acting_user=admin)
    return UserResponse.model_validate(user)
