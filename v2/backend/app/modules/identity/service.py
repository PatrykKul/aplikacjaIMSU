from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.identity.models import User, UserRole
from app.modules.identity.schemas import RegisterRequest, UserUpdateRequest
from app.modules.identity.security import hash_password, verify_password


def get_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def create_user(
    db: Session, *, email: str, pasword: str, display_name: str, role: UserRole
) -> User:
    if get_by_email(db, email) is not None:
        raise AppError(409, "EMAIL_TAKEN")
    user = User(
        email=email,
        password_hash=hash_password(pasword),
        display_name=display_name,
        role=role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "EMAIL_TAKEN") from None
    db.refresh(user)
    return user


def register(db: Session, data: RegisterRequest) -> User:
    return create_user(
        db,
        email=data.email,
        pasword=data.password,
        display_name=data.display_name,
        role=UserRole(data.role),
    )


def authenticate(db: Session, email: str, password: str) -> User:
    user = get_by_email(db, email)
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise AppError(401, "INVALID_CREDENTIALS")
    return user


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.id)))


def update_user(db: Session, *, user_id: int, data: UserUpdateRequest, acting_user: User) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise AppError(404, "USER_NOT_FOUND")
    if user.id == acting_user.id:
        raise AppError(400, "CANNOT_MODIFY_SELF")
    if data.role is not None:
        user.role = data.role
    if data.is_active is not None:
        user.is_active = data.is_active
    db.commit()
    db.refresh(user)
    return user
