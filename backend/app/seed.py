"""Seed danych startowych: `python -m app.seed` (po `alembic upgrade head`). Idempotentny."""
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.security import hash_haslo
from app.seed_ankieta import PYTANIA_VAK, STYLE_W_KOLEJNOSCI
from app.seed_kurs import KURS_DEMO

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


def seed_kurs_demo(db: Session) -> int:
    """Kurs, w którym każdy temat ma bloki wspólne oraz dla stylu V, A i K."""
    if db.query(models.Kurs).filter(models.Kurs.nazwa == KURS_DEMO["nazwa"]).first():
        return 0
    ostatni = db.query(models.Kurs).count()
    kurs = models.Kurs(nazwa=KURS_DEMO["nazwa"], opis=KURS_DEMO["opis"], is_published=True, kolejnosc=ostatni)
    for i, dzial_dane in enumerate(KURS_DEMO["dzialy"]):
        dzial = models.Dzial(nazwa=dzial_dane["nazwa"], kolejnosc=i)
        for j, temat_dane in enumerate(dzial_dane["tematy"]):
            temat = models.Temat(tytul=temat_dane["tytul"], kolejnosc=j)
            for k, b in enumerate(temat_dane["bloki"]):
                blok = models.Blok(
                    typ=b["typ"],
                    tresc=b["tresc"],
                    styl=b.get("styl"),
                    odpowiedz=b.get("odpowiedz"),
                    rozwiazanie=b.get("rozwiazanie"),
                    image_url=b.get("image_url"),
                    media_url=b.get("media_url"),
                    kolejnosc=k,
                )
                blok.dane = b.get("dane")
                temat.bloki.append(blok)
            dzial.tematy.append(temat)
        kurs.dzialy.append(dzial)
    db.add(kurs)
    return 1


def seed(db: Session) -> dict[str, int]:
    return {
        "uzytkownicy": seed_uzytkownicy(db),
        "pytania_ankiety": seed_ankieta(db),
        "kurs_demo": seed_kurs_demo(db),
    }


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
