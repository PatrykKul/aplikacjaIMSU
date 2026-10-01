"""Operacje nauki na bazie: zdarzenia, postęp, wagi. Reguły siedzą w `adaptacja.py`."""
from sqlalchemy.orm import Session

from app import models
from app.services import adaptacja

TYP_OTWARCIE = "otwarcie_tematu"
TYP_WIDEO = "odtworzenie_wideo"
TYP_AUDIO = "odtworzenie_audio"
TYP_CWICZENIE = "ukonczenie_cwiczenia"
TYP_CZAS = "czas_w_temacie"
TYP_QUIZ = "wynik_quizu"
TYP_UKONCZENIE = "ukonczenie_tematu"

# Events a client may report itself; quiz results are recorded only by the server
TYPY_OD_KLIENTA = (TYP_OTWARCIE, TYP_WIDEO, TYP_AUDIO, TYP_CWICZENIE, TYP_CZAS)


def wagi_ucznia(user: models.Uzytkownik) -> dict[str, int]:
    return {"V": user.waga_v, "A": user.waga_a, "K": user.waga_k}


def ustaw_wagi(user: models.Uzytkownik, wagi: dict[str, int]) -> None:
    user.waga_v, user.waga_a, user.waga_k = wagi["V"], wagi["A"], wagi["K"]


def wyniki_quizow(db: Session, user_id: int, limit: int = 2) -> list[int]:
    """Ostatnie wyniki quizów ucznia, od najstarszego do najnowszego."""
    zdarzenia = (
        db.query(models.ZdarzenieNauki)
        .filter(models.ZdarzenieNauki.user_id == user_id, models.ZdarzenieNauki.typ == TYP_QUIZ)
        .order_by(models.ZdarzenieNauki.id.desc())
        .limit(limit)
        .all()
    )
    return [z.wartosc or 0 for z in reversed(zdarzenia)]


def poziom_ucznia(db: Session, user_id: int) -> tuple[int, list[int]]:
    wyniki = wyniki_quizow(db, user_id)
    return adaptacja.poziom_trudnosci(wyniki), wyniki


def proby_w_temacie(db: Session, user_id: int, temat_id: int) -> list[models.ZdarzenieNauki]:
    return (
        db.query(models.ZdarzenieNauki)
        .filter(
            models.ZdarzenieNauki.user_id == user_id,
            models.ZdarzenieNauki.temat_id == temat_id,
            models.ZdarzenieNauki.typ == TYP_QUIZ,
        )
        .order_by(models.ZdarzenieNauki.id.asc())
        .all()
    )


def postep(db: Session, user_id: int, temat_id: int) -> models.PostepTematu | None:
    return (
        db.query(models.PostepTematu)
        .filter(models.PostepTematu.user_id == user_id, models.PostepTematu.temat_id == temat_id)
        .first()
    )


def postep_lub_nowy(db: Session, user_id: int, temat_id: int) -> models.PostepTematu:
    p = postep(db, user_id, temat_id)
    if p is None:
        p = models.PostepTematu(user_id=user_id, temat_id=temat_id)
        db.add(p)
    return p


def tematy_kursu(kurs: models.Kurs) -> list[models.Temat]:
    """Tematy kursu w kolejności nauki (działy, potem tematy)."""
    return [t for d in kurs.dzialy for t in d.tematy]


def nastepny_temat(db: Session, user_id: int, temat: models.Temat) -> models.Temat | None:
    """Pierwszy niezaliczony temat kursu po bieżącym (albo wcześniejszy, jeśli dalej nic nie ma)."""
    tematy = tematy_kursu(temat.dzial.kurs)
    zaliczone = {
        p.temat_id
        for p in db.query(models.PostepTematu).filter(
            models.PostepTematu.user_id == user_id, models.PostepTematu.zaliczony.is_(True)
        )
    }
    indeks = next(i for i, t in enumerate(tematy) if t.id == temat.id)
    for kandydat in tematy[indeks + 1 :] + tematy[:indeks]:
        if kandydat.id not in zaliczone:
            return kandydat
    return None
