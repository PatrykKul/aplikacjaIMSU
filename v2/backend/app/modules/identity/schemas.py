from datetime import datetime
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    BeforeValidator,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
)

from app.modules.identity.models import UserRole


def _normalize_email(value: object) -> str:
    return value.strip().lower() if isinstance(value, str) else value


def _check_bcrypt_limit(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("password longer than 72 bytes")
    return value


Email = Annotated[EmailStr, BeforeValidator(_normalize_email)]
Password = Annotated[str, Field(min_length=8), AfterValidator(_check_bcrypt_limit)]
DisplayName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]


class RegisterRequest(BaseModel):
    email: Email
    password: Password
    display_name: DisplayName
    role: Literal["student", "teacher"]


class LoginRequest(BaseModel):
    email: Email
    password: str = Field(min_length=1)


class UserUpdateRequest(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
