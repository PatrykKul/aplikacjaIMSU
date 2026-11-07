from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.identity.models import User, UserRole
from app.modules.identity.schemas import RegisterRequest, UserUpdateRequest
from app.modules.identity.security import hash_password, verify_password

MANAGED_ROLES = frozenset({UserRole.STUDENT, UserRole.TEACHER})
"""Roles whose accounts the admin manages through the API."""


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def _commit_with_unique_email(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "EMAIL_TAKEN") from None


def create_user(
    db: Session, *, email: str, password: str, display_name: str, role: UserRole
) -> User:
    if get_by_email(db, email) is not None:
        raise AppError(409, "EMAIL_TAKEN")
    user = User(
        email=email,
        password_hash=hash_password(password),
        display_name=display_name,
        role=role,
    )
    db.add(user)
    _commit_with_unique_email(db)
    db.refresh(user)
    return user


def create_account(db: Session, data: RegisterRequest) -> User:
    """Create a student or teacher account (self-registration or by an admin)."""
    return create_user(
        db,
        email=data.email,
        password=data.password,
        display_name=data.display_name,
        role=UserRole(data.role),
    )


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_by_email(db, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS")
    return user


def list_users(db: Session, role: UserRole) -> list[User]:
    return list(db.scalars(select(User).where(User.role == role).order_by(User.email)))


def _get_managed_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None or user.role not in MANAGED_ROLES:
        raise AppError(404, "USER_NOT_FOUND")
    return user


def update_user(db: Session, *, user_id: int, data: UserUpdateRequest) -> User:
    user = _get_managed_user(db, user_id)
    if data.email is not None and data.email != user.email:
        if get_by_email(db, data.email) is not None:
            raise AppError(409, "EMAIL_TAKEN")
        user.email = data.email
    if data.display_name is not None:
        user.display_name = data.display_name
    if data.password is not None:
        user.password_hash = hash_password(data.password)
    if data.is_active is not None:
        user.is_active = data.is_active
    _commit_with_unique_email(db)
    db.refresh(user)
    return user
