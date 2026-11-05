from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.deps import get_current_user, get_db, wymagaj_edytora
from app.services.adaptacja import wagi_startowe
from app.services.vak import policz_wynik

router = APIRouter(tags=["ankieta"])

ZRODLO_ANKIETA = "ankieta"
ZRODLO_RECZNY = "reczny"


def _aktywne_pytania(db: Session) -> list[models.PytanieAnkiety]:
    return (
        db.query(models.PytanieAnkiety)
        .options(selectinload(models.PytanieAnkiety.odpowiedzi))
        .filter(models.PytanieAnkiety.aktywne.is_(True))
        .order_by(models.PytanieAnkiety.kolejnosc.asc(), models.PytanieAnkiety.id.asc())
        .all()
    )


def ostatni_wynik(db: Session, user_id: int) -> models.WynikAnkiety | None:
    return (
        db.query(models.WynikAnkiety)
        .filter(models.WynikAnkiety.user_id == user_id)
        .order_by(models.WynikAnkiety.data.desc(), models.WynikAnkiety.id.desc())
        .first()
    )


def _profil(db: Session, user: models.Uzytkownik) -> schemas.ProfilOut:
    wynik = ostatni_wynik(db, user.id)
    return schemas.ProfilOut(
        uzytkownik=schemas.UzytkownikOut.model_validate(user),
        wynik_ankiety=schemas.WynikAnkietyOut.model_validate(wynik) if wynik else None,
    )


# =========================================================
# Survey for the logged-in user
# =========================================================


@router.get("/ankieta/pytania", response_model=List[schemas.PytanieAnkietyOut])
def pytania(db: Session = Depends(get_db), _user: models.Uzytkownik = Depends(get_current_user)):
    # Response schema has no `styl` field, so the answer key is never sent to the client
    return _aktywne_pytania(db)


@router.post("/ankieta/odpowiedzi", response_model=schemas.ProfilOut)
def wyslij_odpowiedzi(
    dane: schemas.AnkietaOdpowiedziIn,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_current_user),
):
    pytania_aktywne = _aktywne_pytania(db)
    if not pytania_aktywne:
        raise HTTPException(status_code=409, detail="Ankieta nie ma jeszcze pytań")

    wybory = {o.pytanie_id: o.odpowiedz_id for o in dane.odpowiedzi}
    if len(wybory) != len(dane.odpowiedzi):
        raise HTTPException(status_code=400, detail="Na każde pytanie można odpowiedzieć tylko raz")
    if set(wybory) != {p.id for p in pytania_aktywne}:
        raise HTTPException(status_code=400, detail="Odpowiedz na wszystkie pytania ankiety")

    style: list[str] = []
    for pytanie in pytania_aktywne:
        odpowiedz = next((o for o in pytanie.odpowiedzi if o.id == wybory[pytanie.id]), None)
        if odpowiedz is None:
            raise HTTPException(status_code=400, detail="Odpowiedź nie należy do pytania")
        style.append(odpowiedz.styl)

    wynik = policz_wynik(style)
    db.add(
        models.WynikAnkiety(
            user_id=user.id,
            punkty_v=wynik.punkty_v,
            punkty_a=wynik.punkty_a,
            punkty_k=wynik.punkty_k,
            styl_dominujacy=wynik.styl_dominujacy,
        )
    )
    # A new survey result always overrides the current style (history is kept)
    user.ankieta_wypelniona = True
    user.styl_uczenia = wynik.styl_dominujacy
    user.styl_zrodlo = ZRODLO_ANKIETA
    # Adaptation starts from the survey points
    wagi = wagi_startowe(wynik.punkty_v, wynik.punkty_a, wynik.punkty_k)
    user.waga_v, user.waga_a, user.waga_k = wagi["V"], wagi["A"], wagi["K"]
    user.odrzucona_propozycja = None
    db.commit()
    db.refresh(user)
    return _profil(db, user)


@router.get("/ankieta/wynik", response_model=schemas.WynikAnkietyOut)
def wynik(db: Session = Depends(get_db), user: models.Uzytkownik = Depends(get_current_user)):
    ostatni = ostatni_wynik(db, user.id)
    if not ostatni:
        raise HTTPException(status_code=404, detail="Brak wyniku ankiety")
    return ostatni


@router.get("/ankieta/historia", response_model=List[schemas.WynikAnkietyOut])
def historia(db: Session = Depends(get_db), user: models.Uzytkownik = Depends(get_current_user)):
    return (
        db.query(models.WynikAnkiety)
        .filter(models.WynikAnkiety.user_id == user.id)
        .order_by(models.WynikAnkiety.data.desc(), models.WynikAnkiety.id.desc())
        .all()
    )


# =========================================================
# Profile: learning style
# =========================================================


@router.get("/profil", response_model=schemas.ProfilOut)
def profil(db: Session = Depends(get_db), user: models.Uzytkownik = Depends(get_current_user)):
    return _profil(db, user)


@router.put("/profil/styl", response_model=schemas.ProfilOut)
def ustaw_styl_recznie(
    dane: schemas.StylRecznyIn,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_current_user),
):
    if not user.ankieta_wypelniona:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=schemas.ANKIETA_WYMAGANA_DETAIL)
    # Manual choice never deletes survey results
    user.styl_uczenia = dane.styl
    user.styl_zrodlo = ZRODLO_RECZNY
    db.commit()
    db.refresh(user)
    return _profil(db, user)


@router.delete("/profil/styl", response_model=schemas.ProfilOut)
def przywroc_styl_z_ankiety(
    db: Session = Depends(get_db), user: models.Uzytkownik = Depends(get_current_user)
):
    ostatni = ostatni_wynik(db, user.id)
    if not ostatni:
        raise HTTPException(status_code=404, detail="Brak wyniku ankiety")
    user.styl_uczenia = ostatni.styl_dominujacy
    user.styl_zrodlo = ZRODLO_ANKIETA
    db.commit()
    db.refresh(user)
    return _profil(db, user)


# =========================================================
# Survey editor (teacher / admin)
# =========================================================


def _pytanie_lub_404(db: Session, pytanie_id: int) -> models.PytanieAnkiety:
    pytanie = db.get(models.PytanieAnkiety, pytanie_id)
    if not pytanie:
        raise HTTPException(status_code=404, detail="Pytanie nie znalezione")
    return pytanie


def _ustaw_odpowiedzi(pytanie: models.PytanieAnkiety, odpowiedzi: list[schemas.OdpowiedzAnkietyIn]) -> None:
    pytanie.odpowiedzi.clear()
    for i, o in enumerate(odpowiedzi):
        pytanie.odpowiedzi.append(models.OdpowiedzAnkiety(tresc=o.tresc, styl=o.styl, kolejnosc=i))


@router.get(
    "/ankieta/edycja/pytania",
    response_model=List[schemas.PytanieAnkietyEdycjaOut],
    dependencies=[Depends(wymagaj_edytora)],
)
def pytania_do_edycji(db: Session = Depends(get_db)):
    return (
        db.query(models.PytanieAnkiety)
        .options(selectinload(models.PytanieAnkiety.odpowiedzi))
        .order_by(models.PytanieAnkiety.kolejnosc.asc(), models.PytanieAnkiety.id.asc())
        .all()
    )


@router.post(
    "/ankieta/edycja/pytania",
    response_model=schemas.PytanieAnkietyEdycjaOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(wymagaj_edytora)],
)
def dodaj_pytanie(dane: schemas.PytanieAnkietyIn, db: Session = Depends(get_db)):
    ostatnia = db.query(func.max(models.PytanieAnkiety.kolejnosc)).scalar()
    pytanie = models.PytanieAnkiety(
        tresc=dane.tresc,
        aktywne=dane.aktywne,
        kolejnosc=(ostatnia if ostatnia is not None else -1) + 1,
    )
    _ustaw_odpowiedzi(pytanie, dane.odpowiedzi)
    db.add(pytanie)
    db.commit()
    db.refresh(pytanie)
    return pytanie


@router.put(
    "/ankieta/edycja/pytania/{pytanie_id}",
    response_model=schemas.PytanieAnkietyEdycjaOut,
    dependencies=[Depends(wymagaj_edytora)],
)
def edytuj_pytanie(pytanie_id: int, dane: schemas.PytanieAnkietyIn, db: Session = Depends(get_db)):
    pytanie = _pytanie_lub_404(db, pytanie_id)
    pytanie.tresc = dane.tresc
    pytanie.aktywne = dane.aktywne
    _ustaw_odpowiedzi(pytanie, dane.odpowiedzi)
    db.commit()
    db.refresh(pytanie)
    return pytanie


@router.delete("/ankieta/edycja/pytania/{pytanie_id}", dependencies=[Depends(wymagaj_edytora)])
def usun_pytanie(pytanie_id: int, db: Session = Depends(get_db)):
    db.delete(_pytanie_lub_404(db, pytanie_id))
    db.commit()
    return {"status": "success"}
