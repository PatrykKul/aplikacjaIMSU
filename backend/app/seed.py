"""Seed danych startowych: `python -m app.seed` (po `alembic upgrade head`). Idempotentny."""
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.security import hash_haslo
from app.seed_ankieta import PYTANIA_VAK, STYLE_W_KOLEJNOSCI

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


def seed_ankieta(db: Session) -> int:
    # Seeded only into an empty survey, so teacher edits are never overwritten
    if db.query(models.PytanieAnkiety).count() > 0:
        return 0
    for i, (tresc, *odpowiedzi) in enumerate(PYTANIA_VAK):
        pytanie = models.PytanieAnkiety(tresc=tresc, kolejnosc=i)
        pary = list(zip(STYLE_W_KOLEJNOSCI, odpowiedzi))
        # Rotate answer order so the same style is not always listed first
        przesuniecie = i % len(pary)
        for j, (styl, tresc_odp) in enumerate(pary[przesuniecie:] + pary[:przesuniecie]):
            pytanie.odpowiedzi.append(models.OdpowiedzAnkiety(tresc=tresc_odp, styl=styl, kolejnosc=j))
        db.add(pytanie)
    return len(PYTANIA_VAK)


def seed(db: Session) -> dict[str, int]:
    wynik = {"uzytkownicy": seed_uzytkownicy(db), "pytania_ankiety": seed_ankieta(db)}
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
