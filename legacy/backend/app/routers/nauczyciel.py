from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import ROLA_UCZEN, get_db, wymagaj_edytora
from app.routers.nauka import zbuduj_sciezke
from app.services import nauka

router = APIRouter(prefix="/nauczyciel", tags=["nauczyciel"], dependencies=[Depends(wymagaj_edytora)])


def _ostatnie_wyniki(db: Session) -> dict[int, models.WynikAnkiety]:
    """Ostatni wynik ankiety każdego użytkownika."""
    wyniki: dict[int, models.WynikAnkiety] = {}
    for w in db.query(models.WynikAnkiety).order_by(models.WynikAnkiety.id.asc()):
        wyniki[w.user_id] = w
    return wyniki


def _uczen_out(
    u: models.Uzytkownik,
    wynik: models.WynikAnkiety | None,
    zaliczone: int,
    proby: int,
    ostatnia_aktywnosc,
) -> schemas.UczenOut:
    return schemas.UczenOut(
        id=u.id,
        imie=u.imie,
        email=u.email,
        aktywny=u.aktywny,
        ankieta_wypelniona=u.ankieta_wypelniona,
        styl_uczenia=u.styl_uczenia,
        styl_zrodlo=u.styl_zrodlo,
        styl_ankiety=wynik.styl_dominujacy if wynik else None,
        punkty_ankiety={"V": wynik.punkty_v, "A": wynik.punkty_a, "K": wynik.punkty_k} if wynik else None,
        wagi=nauka.wagi_ucznia(u),
        zaliczone_tematy=zaliczone,
        liczba_prob=proby,
        ostatnia_aktywnosc=ostatnia_aktywnosc,
    )


@router.get("/uczniowie", response_model=List[schemas.UczenOut])
def lista_uczniow(db: Session = Depends(get_db)):
    # TODO(decyzja): there is no class / enrolment model yet, so a teacher sees every student
    uczniowie = (
        db.query(models.Uzytkownik)
        .filter(models.Uzytkownik.rola == ROLA_UCZEN)
        .order_by(models.Uzytkownik.imie.asc(), models.Uzytkownik.id.asc())
        .all()
    )
    wyniki = _ostatnie_wyniki(db)
    zaliczone = dict(
        db.query(models.PostepTematu.user_id, func.count(models.PostepTematu.id))
        .filter(models.PostepTematu.zaliczony.is_(True))
        .group_by(models.PostepTematu.user_id)
        .all()
    )
    proby = dict(
        db.query(models.PostepTematu.user_id, func.coalesce(func.sum(models.PostepTematu.liczba_prob), 0))
        .group_by(models.PostepTematu.user_id)
        .all()
    )
    aktywnosc = dict(
        db.query(models.ZdarzenieNauki.user_id, func.max(models.ZdarzenieNauki.data))
        .group_by(models.ZdarzenieNauki.user_id)
        .all()
    )
    return [
        _uczen_out(u, wyniki.get(u.id), zaliczone.get(u.id, 0), int(proby.get(u.id, 0)), aktywnosc.get(u.id))
        for u in uczniowie
    ]


@router.get("/uczniowie/{user_id}", response_model=schemas.UczenSzczegolyOut)
def szczegoly_ucznia(user_id: int, db: Session = Depends(get_db)):
    u = db.get(models.Uzytkownik, user_id)
    if not u or u.rola != ROLA_UCZEN:
        raise HTTPException(status_code=404, detail="Uczeń nie znaleziony")
    historia = (
        db.query(models.WynikAnkiety)
        .filter(models.WynikAnkiety.user_id == u.id)
        .order_by(models.WynikAnkiety.id.desc())
        .all()
    )
    zdarzenia = (
        db.query(models.ZdarzenieNauki, models.Temat.tytul)
        .join(models.Temat, models.Temat.id == models.ZdarzenieNauki.temat_id)
        .filter(models.ZdarzenieNauki.user_id == u.id)
        .order_by(models.ZdarzenieNauki.id.desc())
        .limit(30)
        .all()
    )
    sciezka = zbuduj_sciezke(db, u)
    zaliczone = sum(k.zaliczone for k in sciezka.kursy)
    proby = sum(t.liczba_prob for k in sciezka.kursy for t in k.tematy)
    return schemas.UczenSzczegolyOut(
        uczen=_uczen_out(
            u, historia[0] if historia else None, zaliczone, proby, zdarzenia[0][0].data if zdarzenia else None
        ),
        sciezka=sciezka,
        historia_ankiet=[schemas.WynikAnkietyOut.model_validate(w) for w in historia],
        zdarzenia=[
            schemas.ZdarzenieOut(
                typ=z.typ, temat=tytul, styl=z.styl, wartosc=z.wartosc, czas_s=z.czas_s, data=z.data
            )
            for z, tytul in zdarzenia
        ],
    )
