from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from app import models, schemas
from app.deps import ROLA_UCZEN, get_db, get_uczestnik
from app.routers.ankieta import ostatni_wynik
from app.services import adaptacja, nauka

router = APIRouter(tags=["nauka"])


def _propozycja(user: models.Uzytkownik) -> schemas.PropozycjaStyluOut | None:
    styl = adaptacja.propozycja_zmiany_stylu(
        nauka.wagi_ucznia(user), user.styl_uczenia, user.styl_zrodlo, user.odrzucona_propozycja
    )
    if styl is None:
        return None
    wagi = nauka.wagi_ucznia(user)
    return schemas.PropozycjaStyluOut(
        styl=styl,
        komunikat=adaptacja.komunikat_propozycji(styl),
        dlaczego=(
            f"bo po quizach Twoje wagi to V {wagi['V']} / A {wagi['A']} / K {wagi['K']} "
            f"— najwyżej jest styl „{adaptacja.NAZWA_STYLU[styl]}”."
        ),
    )


def _wymagaj_ucznia(user: models.Uzytkownik) -> None:
    if user.rola != ROLA_UCZEN:
        raise HTTPException(status_code=403, detail="Tylko dla ucznia")


@router.post("/nauka/zdarzenia", status_code=201)
def zapisz_zdarzenie(
    dane: schemas.ZdarzenieIn,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    # Learning events are collected for students only
    if user.rola != ROLA_UCZEN:
        return {"status": "pominieto"}
    temat = db.get(models.Temat, dane.temat_id)
    if not temat or not temat.dzial.kurs.is_published:
        raise HTTPException(status_code=404, detail="Temat nie znaleziony")
    if dane.blok_id is not None:
        blok = db.get(models.Blok, dane.blok_id)
        if not blok or blok.temat_id != temat.id:
            raise HTTPException(status_code=400, detail="Blok nie należy do tematu")
    db.add(
        models.ZdarzenieNauki(
            user_id=user.id,
            temat_id=temat.id,
            blok_id=dane.blok_id,
            typ=dane.typ,
            styl=dane.styl,
            czas_s=dane.czas_s,
        )
    )
    db.commit()
    return {"status": "success"}


@router.post("/tematy/{temat_id}/ukoncz", response_model=schemas.PostepOut)
def oznacz_ukonczenie(
    temat_id: int,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    """Ręczne oznaczenie postępu — tylko dla tematów bez quizu (z quizem decyduje wynik)."""
    _wymagaj_ucznia(user)
    temat = db.get(models.Temat, temat_id)
    if not temat or not temat.dzial.kurs.is_published:
        raise HTTPException(status_code=404, detail="Temat nie znaleziony")
    if any(b.typ == "quiz" for b in temat.bloki):
        raise HTTPException(status_code=400, detail="Ten temat zalicza się quizem")
    p = nauka.postep_lub_nowy(db, user.id, temat_id)
    p.zaliczony = True
    db.add(models.ZdarzenieNauki(user_id=user.id, temat_id=temat_id, typ=nauka.TYP_UKONCZENIE))
    db.commit()
    db.refresh(p)
    return p


def zbuduj_sciezke(db: Session, user: models.Uzytkownik) -> schemas.SciezkaOut:
    """Ścieżka ucznia: kursy z postępem, wagi, poziom i następny krok z uzasadnieniem."""
    kursy = (
        db.query(models.Kurs)
        .options(selectinload(models.Kurs.dzialy).selectinload(models.Dzial.tematy))
        .filter(models.Kurs.is_published.is_(True))
        .order_by(models.Kurs.kolejnosc.asc(), models.Kurs.id.asc())
        .all()
    )
    postepy = {
        p.temat_id: p for p in db.query(models.PostepTematu).filter(models.PostepTematu.user_id == user.id)
    }
    poziom, wyniki = nauka.poziom_ucznia(db, user.id)

    kursy_out: list[schemas.SciezkaKursOut] = []
    nastepny: schemas.NastepnyKrokOut | None = None
    for kurs in kursy:
        tematy_out = []
        for dzial in kurs.dzialy:
            for temat in dzial.tematy:
                p = postepy.get(temat.id)
                tematy_out.append(
                    schemas.SciezkaTematOut(
                        id=temat.id,
                        tytul=temat.tytul,
                        dzial=dzial.nazwa,
                        zaliczony=bool(p and p.zaliczony),
                        najlepszy_wynik=p.najlepszy_wynik if p else None,
                        ostatni_wynik=p.ostatni_wynik if p else None,
                        liczba_prob=p.liczba_prob if p else 0,
                    )
                )
        if not tematy_out:
            continue
        kursy_out.append(
            schemas.SciezkaKursOut(
                id=kurs.id,
                nazwa=kurs.nazwa,
                tematy=tematy_out,
                zaliczone=sum(t.zaliczony for t in tematy_out),
            )
        )
        if nastepny is None:
            # First topic that is not passed yet, in learning order
            kandydat = next((t for t in tematy_out if not t.zaliczony), None)
            if kandydat is not None:
                if kandydat.liczba_prob > 0:
                    dlaczego = f"bo quiz z tematu „{kandydat.tytul}”: {kandydat.ostatni_wynik}% — poniżej progu {adaptacja.PROG_ZALICZENIA}%."
                elif any(t.zaliczony for t in tematy_out):
                    dlaczego = "bo to kolejny temat po tych, które masz już zaliczone."
                else:
                    dlaczego = "bo to pierwszy temat w kursie."
                nastepny = schemas.NastepnyKrokOut(
                    temat_id=kandydat.id, tytul=kandydat.tytul, kurs=kurs.nazwa, dlaczego=dlaczego
                )

    wynik = ostatni_wynik(db, user.id)
    return schemas.SciezkaOut(
        styl_uczenia=user.styl_uczenia,
        styl_zrodlo=user.styl_zrodlo,
        styl_ankiety=wynik.styl_dominujacy if wynik else None,
        wagi=nauka.wagi_ucznia(user),
        poziom=poziom,
        poziom_dlaczego=adaptacja.uzasadnienie_poziomu(poziom, wyniki),
        kursy=kursy_out,
        nastepny_krok=nastepny,
        propozycja_stylu=_propozycja(user),
    )


@router.get("/nauka/sciezka", response_model=schemas.SciezkaOut)
def sciezka(db: Session = Depends(get_db), user: models.Uzytkownik = Depends(get_uczestnik)):
    _wymagaj_ucznia(user)
    return zbuduj_sciezke(db, user)


@router.post("/nauka/propozycja-stylu", response_model=schemas.ProfilOut)
def odpowiedz_na_propozycje(
    dane: schemas.DecyzjaPropozycjiIn,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    """Uczeń decyduje: przyjmuje propozycję przełączenia stylu albo ją odrzuca."""
    _wymagaj_ucznia(user)
    propozycja = _propozycja(user)
    if propozycja is None or propozycja.styl != dane.styl:
        raise HTTPException(status_code=409, detail="Ta propozycja jest już nieaktualna")
    if dane.akceptuj:
        user.styl_uczenia = dane.styl
        user.styl_zrodlo = adaptacja.ZRODLO_ADAPTACJA
        user.odrzucona_propozycja = None
    else:
        user.odrzucona_propozycja = dane.styl
    db.commit()
    db.refresh(user)
    wynik = ostatni_wynik(db, user.id)
    return schemas.ProfilOut(
        uzytkownik=schemas.UzytkownikOut.model_validate(user),
        wynik_ankiety=schemas.WynikAnkietyOut.model_validate(wynik) if wynik else None,
    )
