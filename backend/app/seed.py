"""Seed danych startowych: `python -m app.seed` (po `alembic upgrade head`)."""
from sqlalchemy.orm import Session

from app.database import SessionLocal


def seed(db: Session) -> None:
    # Users (Etap 1)
    # VAK survey questions (Etap 2)
    # Demo course with V/A/K blocks (Etap 3)
    pass


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
        db.commit()
    finally:
        db.close()
    print("Seed zakończony (na razie brak danych do wstawienia).")


if __name__ == "__main__":
    main()
