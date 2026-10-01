"""Seed danych startowych: `python -m app.seed` (po `alembic upgrade head`). Idempotentny."""
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.security import hash_haslo

# Demo accounts (documented in README) — for presentation only
KONTA_TESTOWE = [
    {"email": "admin@stylnauki.pl", "imie": "Admin", "haslo": "Admin123!", "rola": "admin"},
    {"email": "nauczyciel@stylnauki.pl", "imie": "Nauczyciel", "haslo": "Nauczyciel123!", "rola": "nauczyciel"},
    {"email": "uczen@stylnauki.pl", "imie": "Uczeń", "haslo": "Uczen123!", "rola": "uczen"},
]


def seed_uzytkownicy(db: Session) -> int:
    dodano = 0
    for konto in KONTA_TESTOWE:
        if db.query(models.Uzytkownik).filter(models.Uzytkownik.email == konto["email"]).first():
            continue
        db.add(
            models.Uzytkownik(
                email=konto["email"],
                imie=konto["imie"],
                haslo_hash=hash_haslo(konto["haslo"]),
                rola=konto["rola"],
            )
        )
        dodano += 1
    return dodano


def seed(db: Session) -> dict[str, int]:
    wynik = {"uzytkownicy": seed_uzytkownicy(db)}
    # VAK survey questions (Etap 2)
    # Demo course with V/A/K blocks (Etap 3)
    return wynik


def main() -> None:
    db = SessionLocal()
    try:
        wynik = seed(db)
        db.commit()
    finally:
        db.close()
    print("Seed OK:", ", ".join(f"{k}: +{v}" for k, v in wynik.items()))


if __name__ == "__main__":
    main()
