"""Administrative commands for the identity module."""

import argparse
import getpass
import sys

from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.core.errors import AppError
from app.modules.identity import service
from app.modules.identity.models import User, UserRole
from app.modules.identity.schemas import DisplayName, Email, Password


def create_admin(db: Session, *, email: str, display_name: str, password: str) -> User:
    """Validates input with the same rules as registration and creates an admin."""
    return service.create_user(
        db,
        email=TypeAdapter(Email).validate_python(email),
        password=TypeAdapter(Password).validate_python(password),
        display_name=TypeAdapter(DisplayName).validate_python(display_name),
        role=UserRole.ADMIN,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.modules.identity.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    admin_parser = commands.add_parser("create-admin", help="Create an administrator account")
    admin_parser.add_argument("--email", required=True)
    admin_parser.add_argument("--name", required=True)
    args = parser.parse_args(argv)

    password = getpass.getpass("Password: ")
    if password != getpass.getpass("Repeat password: "):
        print("Passwords do not match.", file=sys.stderr)
        return 1

    with SessionLocal() as db:
        try:
            user = create_admin(db, email=args.email, display_name=args.name, password=password)
        except ValidationError as exc:
            print(f"Invalid data\n{exc}", file=sys.stderr)
            return 1
        except AppError as exc:
            print(f"Error: {exc.code}", file=sys.stderr)
            return 1

    print(f"Administrator created: {user.email} (id {user.id})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
