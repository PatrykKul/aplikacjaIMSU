import pytest
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.identity.cli import create_admin
from app.modules.identity.models import UserRole
from app.modules.identity.security import verify_password


def test_create_admin(db: Session) -> None:
    user = create_admin(db, email=" Admin@Imsu.pl ", display_name="Admin", password="BardzoTajne1")
    assert user.role == UserRole.ADMIN
    assert user.email == "admin@imsu.pl"
    assert verify_password("BardzoTajne1", user.password_hash)


def test_create_admin_refuses_taken_email(db: Session) -> None:
    create_admin(db, email="admin@imsu.pl", display_name="Admin", password="BardzoTajne1")
    with pytest.raises(AppError) as error:
        create_admin(db, email="admin@imsu.pl", display_name="Inny", password="BardzoTajne1")
    assert error.value.code == "EMAIL_TAKEN"


def test_create_admin_validates_input(db: Session) -> None:
    with pytest.raises(ValidationError):
        create_admin(db, email="bez-malpy", display_name="Admin", password="BardzoTajne1")
