from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import get_settings
from app.core.db import DbSession
from app.core.errors import AppError
from app.modules.identity.models import User, UserRole
from app.modules.identity.security import decode_access_token


def get_current_user(request: Request, db: DbSession) -> User:
    token = request.cookies.get(get_settings().auth_cookie_name)
    user_id = decode_access_token(token) if token else None
    user = db.get(User, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise AppError(401, "NOT_AUTHENTICATED")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: UserRole) -> Callable[[User], User]:
    def dependency(user: CurrentUser) -> User:
        if user.role not in roles:
            raise AppError(403, "FORBIDDEN")
        return user

    return dependency


AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
