"""Seed danych startowych: `python -m app.seed` (po `alembic upgrade head`). Idempotentny."""
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.security import hash_haslo
from app.seed_ankieta import PYTANIA_VAK, STYLE_W_KOLEJNOSCI
from app.media import get_media_root
from app.seed_kurs import KURS_DEMO
from app.seed_matematyka import KATALOG_WYKRESOW, KURS_MATEMATYKA, WSZYSTKIE_WYKRESY
from app.services.adaptacja import wagi_startowe
from app.services.vak import policz_wynik
from app.wykresy import wykres_svg

# Demo accounts (documented in README) — for presentation only
KONTA_TESTOWE = [
    {"email": "admin@stylnauki.pl", "imie": "Admin", "haslo": "Admin123!", "rola": "admin"},
    {"email": "nauczyciel@stylnauki.pl", "imie": "Nauczyciel", "haslo": "Nauczyciel123!", "rola": "nauczyciel"},
    {"email": "uczen@stylnauki.pl", "imie": "Uczeń", "haslo": "Uczen123!", "rola": "uczen"},
]

# Students with a finished survey — one per learning style, for a quick demo of personalisation
UCZNIOWIE_DEMO = [
    {"email": "wzrokowiec@stylnauki.pl", "imie": "Wiktor (wzrokowiec)", "punkty": (12, 5, 3)},
    {"email": "sluchowiec@stylnauki.pl", "imie": "Ala (słuchowiec)", "punkty": (4, 12, 4)},
    {"email": "kinestetyk@stylnauki.pl", "imie": "Kuba (kinestetyk)", "punkty": (3, 5, 12)},
]
HASLO_UCZNIA_DEMO = "Uczen123!"


def seed_uczniowie_demo(db: Session) -> int:
    dodano = 0
    for konto in UCZNIOWIE_DEMO:
        if db.query(models.Uzytkownik).filter(models.Uzytkownik.email == konto["email"]).first():
            continue
        v, a, k = konto["punkty"]
        wynik = policz_wynik(["V"] * v + ["A"] * a + ["K"] * k)
        wagi = wagi_startowe(v, a, k)
        user = models.Uzytkownik(
            email=konto["email"],
            imie=konto["imie"],
            haslo_hash=hash_haslo(HASLO_UCZNIA_DEMO),
            rola="uczen",
            ankieta_wypelniona=True,
            styl_uczenia=wynik.styl_dominujacy,
            styl_zrodlo="ankieta",
            waga_v=wagi["V"],
            waga_a=wagi["A"],
            waga_k=wagi["K"],
        )
        db.add(user)
        db.flush()
        db.add(
            models.WynikAnkiety(
                user_id=user.id, punkty_v=v, punkty_a=a, punkty_k=k, styl_dominujacy=wynik.styl_dominujacy
            )
        )
        dodano += 1
    return dodano


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


def _dodaj_kurs(db: Session, dane: dict) -> int:
    """Dodaje opublikowany kurs z danych seeda; istniejącego kursu (po nazwie) nie rusza."""
    if db.query(models.Kurs).filter(models.Kurs.nazwa == dane["nazwa"]).first():
        return 0
    ostatni = db.query(models.Kurs).count()
    kurs = models.Kurs(nazwa=dane["nazwa"], opis=dane["opis"], is_published=True, kolejnosc=ostatni)
    for i, dzial_dane in enumerate(dane["dzialy"]):
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
                    poziom=b.get("poziom"),
                    kolejnosc=k,
                )
                blok.dane = b.get("dane")
                temat.bloki.append(blok)
            dzial.tematy.append(temat)
        kurs.dzialy.append(dzial)
    db.add(kurs)
    return 1


def seed_kurs_demo(db: Session) -> int:
    """Kurs, w którym każdy temat ma bloki wspólne oraz dla stylu V, A i K."""
    return _dodaj_kurs(db, KURS_DEMO)


def zapisz_wykresy_matematyki() -> int:
    """Generuje wykresy SVG do katalogu media (nadpisuje — są w pełni wyliczane z danych kursu)."""
    katalog = get_media_root().joinpath(*KATALOG_WYKRESOW)
    katalog.mkdir(parents=True, exist_ok=True)
    for wykres in WSZYSTKIE_WYKRESY:
        (katalog / wykres.plik).write_text(wykres_svg(wykres), encoding="utf-8", newline="\n")
    return len(WSZYSTKIE_WYKRESY)


def seed_kurs_matematyka(db: Session) -> int:
    """Drugi kurs demonstracyjny: funkcja liniowa. Wykresy odtwarzamy przy każdym uruchomieniu seeda."""
    zapisz_wykresy_matematyki()
    return _dodaj_kurs(db, KURS_MATEMATYKA)


def seed(db: Session) -> dict[str, int]:
    return {
        "uzytkownicy": seed_uzytkownicy(db),
        "uczniowie_demo": seed_uczniowie_demo(db),
        "pytania_ankiety": seed_ankieta(db),
        "kurs_demo": seed_kurs_demo(db),
        "kurs_matematyka": seed_kurs_matematyka(db),
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
