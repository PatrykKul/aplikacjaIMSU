import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from app import models, schemas
from app.database import SessionLocal
from app.deps import ROLA_UCZEN, get_db, get_uczestnik, wymagaj_edytora
from app.media import (
    MAX_AUDIO_BYTES,
    MAX_OBRAZ_BYTES,
    ROZSZERZENIA_AUDIO,
    ROZSZERZENIA_OBRAZ,
    zapisz_upload,
)
from app.services import ai_generator
from app.services.personalizacja import filtruj_bloki, ukryj_klucz_quizu
from app.services.quiz import ocen_quiz

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/upload-image", dependencies=[Depends(wymagaj_edytora)])
async def upload_image(
    file: UploadFile = File(...),
    kurs_nazwa: str = Form(...),
    dzial_nazwa: str = Form(...),
    temat_nazwa: str = Form(...),
):
    url = await zapisz_upload(
        file, (kurs_nazwa, dzial_nazwa, temat_nazwa), ROZSZERZENIA_OBRAZ, MAX_OBRAZ_BYTES
    )
    return {"image_url": url}


@router.post("/upload-audio", dependencies=[Depends(wymagaj_edytora)])
async def upload_audio(
    file: UploadFile = File(...),
    kurs_nazwa: str = Form(...),
    dzial_nazwa: str = Form(...),
    temat_nazwa: str = Form(...),
):
    url = await zapisz_upload(
        file, (kurs_nazwa, dzial_nazwa, temat_nazwa), ROZSZERZENIA_AUDIO, MAX_AUDIO_BYTES
    )
    return {"media_url": url}


def _widok_tematu(
    temat: models.Temat, user: models.Uzytkownik, styl_parametr: str | None
) -> schemas.Temat:
    """Uczeń: bloki wspólne + jego stylu (bez klucza quizu). Edytor: wszystko albo podgląd `?styl=`."""
    wynik = schemas.Temat.model_validate(temat)
    if user.rola == ROLA_UCZEN:
        # `?styl=` lets a student retry the topic in another style ("spróbuj inaczej")
        styl_widoku = styl_parametr or user.styl_uczenia
        bloki = filtruj_bloki(wynik.bloki, styl_widoku)
        for blok in bloki:
            if blok.typ == "quiz":
                blok.dane = ukryj_klucz_quizu(blok.dane)
    elif styl_parametr:
        styl_widoku = styl_parametr
        bloki = filtruj_bloki(wynik.bloki, styl_widoku)
    else:
        styl_widoku = None
        bloki = sorted(wynik.bloki, key=lambda b: (b.kolejnosc, b.id))
    wynik.bloki = bloki
    wynik.styl_widoku = styl_widoku
    return wynik


def _tylko_opublikowane(user: models.Uzytkownik) -> bool:
    return user.rola == ROLA_UCZEN


def _sprawdz_widocznosc(kurs: models.Kurs | None, user: models.Uzytkownik, detail: str) -> None:
    # Students must not see unpublished courses (404 instead of 403: do not reveal existence)
    if kurs is None or (_tylko_opublikowane(user) and not kurs.is_published):
        raise HTTPException(status_code=404, detail=detail)


def _reload_temat(db: Session, temat_id: int) -> models.Temat:
    temat = (
        db.query(models.Temat)
        .options(joinedload(models.Temat.bloki))
        .filter(models.Temat.id == temat_id)
        .first()
    )
    if not temat:
        raise HTTPException(status_code=404, detail="Temat nie znaleziony")
    return temat


def _nastepna_kolejnosc(db: Session, temat_id: int) -> int:
    m = (
        db.query(func.max(models.Blok.kolejnosc))
        .filter(models.Blok.temat_id == temat_id)
        .scalar()
    )
    return (m if m is not None else -1) + 1


def _nastepna_kolejnosc_kurs(db: Session) -> int:
    m = db.query(func.max(models.Kurs.kolejnosc)).scalar()
    return (m if m is not None else -1) + 1


def _nastepna_kolejnosc_dzial(db: Session, kurs_id: int) -> int:
    m = (
        db.query(func.max(models.Dzial.kolejnosc))
        .filter(models.Dzial.kurs_id == kurs_id)
        .scalar()
    )
    return (m if m is not None else -1) + 1


def _nastepna_kolejnosc_temat(db: Session, dzial_id: int) -> int:
    m = (
        db.query(func.max(models.Temat.kolejnosc))
        .filter(models.Temat.dzial_id == dzial_id)
        .scalar()
    )
    return (m if m is not None else -1) + 1


# =========================================================
# SEKCYJA 1: KURSY
# =========================================================


@router.post("/kursy", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Kurs)
def utworz_kurs(kurs: schemas.KursCreate, db: Session = Depends(get_db)):
    data = kurs.model_dump()
    if "kolejnosc" not in data or data["kolejnosc"] == 0:
        data["kolejnosc"] = _nastepna_kolejnosc_kurs(db)
    nowy_kurs = models.Kurs(**data)
    db.add(nowy_kurs)
    db.commit()
    db.refresh(nowy_kurs)
    return nowy_kurs


@router.get("/kursy", response_model=List[schemas.Kurs])
def pobierz_kursy(
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    q = db.query(models.Kurs)
    if _tylko_opublikowane(user):
        q = q.filter(models.Kurs.is_published.is_(True))
    return q.order_by(models.Kurs.kolejnosc.asc(), models.Kurs.id.asc()).all()


# Must be declared before /kursy/{kurs_id}, otherwise "reorder" is parsed as an id
@router.put("/kursy/reorder", dependencies=[Depends(wymagaj_edytora)], response_model=List[schemas.Kurs])
def reorder_kursy(body: schemas.ItemReorder, db: Session = Depends(get_db)):
    kursy = db.query(models.Kurs).all()
    _validate_ids_exact(
        {k.id for k in kursy},
        body.ids,
        "Lista ID musi dokładnie odpowiadać wszystkim kursom",
    )
    pozycja = {kid: i for i, kid in enumerate(body.ids)}
    for k in kursy:
        k.kolejnosc = pozycja[k.id]
    db.commit()
    return db.query(models.Kurs).order_by(models.Kurs.kolejnosc.asc(), models.Kurs.id.asc()).all()


@router.get("/kursy/{kurs_id}", response_model=schemas.Kurs)
def pobierz_kurs(
    kurs_id: int,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    kurs = (
        db.query(models.Kurs)
        .options(joinedload(models.Kurs.dzialy))
        .filter(models.Kurs.id == kurs_id)
        .first()
    )
    _sprawdz_widocznosc(kurs, user, "Kurs nie znaleziony")
    return kurs


@router.get("/dzialy/{dzial_id}", response_model=schemas.Dzial)
def pobierz_dzial(
    dzial_id: int,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    dzial = (
        db.query(models.Dzial)
        .options(joinedload(models.Dzial.tematy))
        .filter(models.Dzial.id == dzial_id)
        .first()
    )
    if not dzial:
        raise HTTPException(status_code=404, detail="Dział nie znaleziony")
    _sprawdz_widocznosc(dzial.kurs, user, "Dział nie znaleziony")
    return dzial


@router.get("/tematy/{temat_id}", response_model=schemas.Temat)
def pobierz_temat(
    temat_id: int,
    styl: Optional[str] = Query(None, pattern="^[VAK]$"),
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    temat = _reload_temat(db, temat_id)
    _sprawdz_widocznosc(temat.dzial.kurs, user, "Temat nie znaleziony")
    return _widok_tematu(temat, user, styl)


@router.put("/kursy/{kurs_id}", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Kurs)
def edytuj_kurs(kurs_id: int, dane: schemas.KursUpdate, db: Session = Depends(get_db)):
    kurs = db.query(models.Kurs).filter(models.Kurs.id == kurs_id).first()
    if not kurs:
        raise HTTPException(status_code=404, detail="Kurs nie znaleziony")
    for klucz, wartosc in dane.model_dump(exclude_unset=True).items():
        setattr(kurs, klucz, wartosc)
    db.commit()
    db.refresh(kurs)
    return kurs


@router.delete("/kursy/{kurs_id}", dependencies=[Depends(wymagaj_edytora)])
def usun_kurs(kurs_id: int, db: Session = Depends(get_db)):
    kurs = db.query(models.Kurs).filter(models.Kurs.id == kurs_id).first()
    if not kurs:
        raise HTTPException(status_code=404, detail="Kurs nie znaleziony")
    db.delete(kurs)
    db.commit()
    return {"status": "success", "message": f"Kurs {kurs_id} i cała jego zawartość usunięta"}


# =========================================================
# SEKCYJA 2: DZIAŁY
# =========================================================


@router.post("/kursy/{kurs_id}/dzialy", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Dzial)
def utworz_dzial(kurs_id: int, dzial: schemas.DzialCreate, db: Session = Depends(get_db)):
    kurs = db.query(models.Kurs).filter(models.Kurs.id == kurs_id).first()
    if not kurs:
        raise HTTPException(status_code=404, detail="Kurs nie znaleziony")
    data = dzial.model_dump()
    if "kolejnosc" not in data or data["kolejnosc"] == 0:
        data["kolejnosc"] = _nastepna_kolejnosc_dzial(db, kurs_id)
    nowy_dzial = models.Dzial(**data, kurs_id=kurs_id)
    db.add(nowy_dzial)
    db.commit()
    db.refresh(nowy_dzial)
    return nowy_dzial


@router.put("/dzialy/{dzial_id}", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Dzial)
def edytuj_dzial(dzial_id: int, dane: schemas.DzialUpdate, db: Session = Depends(get_db)):
    dzial = db.query(models.Dzial).filter(models.Dzial.id == dzial_id).first()
    if not dzial:
        raise HTTPException(status_code=404, detail="Dział nie znaleziony")
    for klucz, wartosc in dane.model_dump(exclude_unset=True).items():
        setattr(dzial, klucz, wartosc)
    db.commit()
    db.refresh(dzial)
    return dzial


@router.delete("/dzialy/{dzial_id}", dependencies=[Depends(wymagaj_edytora)])
def usun_dzial(dzial_id: int, db: Session = Depends(get_db)):
    dzial = db.query(models.Dzial).filter(models.Dzial.id == dzial_id).first()
    if not dzial:
        raise HTTPException(status_code=404, detail="Dział nie znaleziony")
    db.delete(dzial)
    db.commit()
    return {"status": "success", "message": f"Dział {dzial_id} usunięty"}


# =========================================================
# SEKCYJA 3: TEMATY
# =========================================================


@router.post("/dzialy/{dzial_id}/tematy", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Temat)
def utworz_temat(dzial_id: int, temat: schemas.TematCreate, db: Session = Depends(get_db)):
    dzial = db.query(models.Dzial).filter(models.Dzial.id == dzial_id).first()
    if not dzial:
        raise HTTPException(status_code=404, detail="Dział nie znaleziony")
    data = temat.model_dump()
    if "kolejnosc" not in data or data["kolejnosc"] == 0:
        data["kolejnosc"] = _nastepna_kolejnosc_temat(db, dzial_id)
    nowy_temat = models.Temat(**data, dzial_id=dzial_id)
    db.add(nowy_temat)
    db.commit()
    db.refresh(nowy_temat)
    return _reload_temat(db, nowy_temat.id)


@router.put("/tematy/{temat_id}", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Temat)
def edytuj_temat(temat_id: int, dane: schemas.TematUpdate, db: Session = Depends(get_db)):
    temat = db.query(models.Temat).filter(models.Temat.id == temat_id).first()
    if not temat:
        raise HTTPException(status_code=404, detail="Temat nie znaleziony")
    for klucz, wartosc in dane.model_dump(exclude_unset=True).items():
        setattr(temat, klucz, wartosc)
    db.commit()
    return _reload_temat(db, temat_id)


@router.delete("/tematy/{temat_id}", dependencies=[Depends(wymagaj_edytora)])
def usun_temat(temat_id: int, db: Session = Depends(get_db)):
    temat = db.query(models.Temat).filter(models.Temat.id == temat_id).first()
    if not temat:
        raise HTTPException(status_code=404, detail="Temat nie znaleziony")
    db.delete(temat)
    db.commit()
    return {"status": "success", "message": f"Temat {temat_id} usunięty"}


def _naglowek_tematu(temat_id: int) -> tuple[str, str]:
    with SessionLocal() as db:
        temat = (
            db.query(models.Temat)
            .options(joinedload(models.Temat.dzial))
            .filter(models.Temat.id == temat_id)
            .first()
        )
        if not temat:
            raise HTTPException(status_code=404, detail="Temat nie znaleziony")
        return str(temat.tytul), str(temat.dzial.nazwa)


def _zapisz_bloki_ai(temat_id: int, dane_list: list[dict]) -> schemas.Temat:
    with SessionLocal() as db:
        db.query(models.Blok).filter(models.Blok.temat_id == temat_id).delete()
        for i, d in enumerate(dane_list):
            db.add(
                models.Blok(
                    temat_id=temat_id,
                    typ=d["typ"],
                    tresc=d["tresc"],
                    odpowiedz=d.get("odpowiedz"),
                    rozwiazanie=d.get("rozwiazanie"),
                    kolejnosc=i,
                )
            )
        db.commit()
        return schemas.Temat.model_validate(_reload_temat(db, temat_id))


@router.put("/tematy/{temat_id}/generuj-bloki", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Temat)
async def generuj_bloki_ai(temat_id: int):
    # No DB session is held while waiting for the model; blocking calls run in the threadpool
    tytul, dzial = await run_in_threadpool(_naglowek_tematu, temat_id)
    try:
        dane_list = await run_in_threadpool(ai_generator.generuj_materialy_ai, tytul, dzial)
    except ai_generator.AIConfigError:
        logger.exception("generuj_bloki_ai temat_id=%s", temat_id)
        raise HTTPException(status_code=503, detail="Generator AI nie jest skonfigurowany")
    except Exception:
        logger.exception("generuj_bloki_ai temat_id=%s", temat_id)
        raise HTTPException(
            status_code=502,
            detail="Nie udało się wygenerować materiałów. Spróbuj ponownie później.",
        )
    try:
        return await run_in_threadpool(_zapisz_bloki_ai, temat_id, dane_list)
    except HTTPException:
        raise
    except Exception:
        logger.exception("generuj_bloki_ai zapis temat_id=%s", temat_id)
        raise HTTPException(status_code=500, detail="Nie udało się zapisać wygenerowanych materiałów")


def _reorder_bloki_impl(
    temat_id: int, body: schemas.BlokReorder, db: Session
) -> models.Temat:
    temat = db.query(models.Temat).filter(models.Temat.id == temat_id).first()
    if not temat:
        raise HTTPException(status_code=404, detail="Temat nie znaleziony")
    bloki = (
        db.query(models.Blok).filter(models.Blok.temat_id == temat_id).all()
    )
    ids_w_bazie = {b.id for b in bloki}
    if set(body.ids) != ids_w_bazie:
        raise HTTPException(
            status_code=400,
            detail="Lista ID musi dokładnie odpowiadać blokom tego tematu",
        )
    pozycja = {bid: i for i, bid in enumerate(body.ids)}
    for b in bloki:
        b.kolejnosc = pozycja[b.id]
    db.commit()
    return _reload_temat(db, temat_id)


def _validate_ids_exact(ids_from_db: set[int], ids_from_body: list[int], detail: str) -> None:
    if set(ids_from_body) != ids_from_db:
        raise HTTPException(status_code=400, detail=detail)


@router.put("/tematy/{temat_id}/reorder", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Temat)
def reorder_temat_bloki(
    temat_id: int, body: schemas.BlokReorder, db: Session = Depends(get_db)
):
    return _reorder_bloki_impl(temat_id, body, db)


@router.put("/kursy/{kurs_id}/dzialy/reorder", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Kurs)
def reorder_dzialy_w_kursie(
    kurs_id: int, body: schemas.ItemReorder, db: Session = Depends(get_db)
):
    kurs = (
        db.query(models.Kurs)
        .options(joinedload(models.Kurs.dzialy))
        .filter(models.Kurs.id == kurs_id)
        .first()
    )
    if not kurs:
        raise HTTPException(status_code=404, detail="Kurs nie znaleziony")
    dzialy = db.query(models.Dzial).filter(models.Dzial.kurs_id == kurs_id).all()
    _validate_ids_exact(
        {d.id for d in dzialy},
        body.ids,
        "Lista ID musi dokładnie odpowiadać działom tego kursu",
    )
    pozycja = {did: i for i, did in enumerate(body.ids)}
    for d in dzialy:
        d.kolejnosc = pozycja[d.id]
    db.commit()
    return (
        db.query(models.Kurs)
        .options(joinedload(models.Kurs.dzialy))
        .filter(models.Kurs.id == kurs_id)
        .first()
    )


@router.put("/dzialy/{dzial_id}/tematy/reorder", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Dzial)
def reorder_tematy_w_dziale(
    dzial_id: int, body: schemas.ItemReorder, db: Session = Depends(get_db)
):
    dzial = (
        db.query(models.Dzial)
        .options(joinedload(models.Dzial.tematy))
        .filter(models.Dzial.id == dzial_id)
        .first()
    )
    if not dzial:
        raise HTTPException(status_code=404, detail="Dział nie znaleziony")
    tematy = db.query(models.Temat).filter(models.Temat.dzial_id == dzial_id).all()
    _validate_ids_exact(
        {t.id for t in tematy},
        body.ids,
        "Lista ID musi dokładnie odpowiadać tematom tego działu",
    )
    pozycja = {tid: i for i, tid in enumerate(body.ids)}
    for t in tematy:
        t.kolejnosc = pozycja[t.id]
    db.commit()
    return (
        db.query(models.Dzial)
        .options(joinedload(models.Dzial.tematy))
        .filter(models.Dzial.id == dzial_id)
        .first()
    )


# =========================================================
# SEKCYJA 4: BLOKI
# =========================================================


def _dane_bloku(typ: str, dane: dict | None) -> dict | None:
    try:
        return schemas.waliduj_dane_bloku(typ, dane)
    except ValueError as e:
        # pydantic ValidationError is a ValueError too; details are safe to show (teacher's own input)
        logger.info("Nieprawidłowe dane bloku typu %s: %s", typ, e)
        raise HTTPException(status_code=422, detail=f"Nieprawidłowe dane bloku typu „{typ}”")


@router.post("/tematy/{temat_id}/bloki", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Blok)
def utworz_blok(
    temat_id: int, body: schemas.BlokCreate, db: Session = Depends(get_db)
):
    temat = db.query(models.Temat).filter(models.Temat.id == temat_id).first()
    if not temat:
        raise HTTPException(status_code=404, detail="Temat nie znaleziony")
    k = (
        body.kolejnosc
        if body.kolejnosc is not None
        else _nastepna_kolejnosc(db, temat_id)
    )
    blok = models.Blok(
        temat_id=temat_id,
        typ=body.typ,
        tresc=body.tresc,
        odpowiedz=body.odpowiedz,
        rozwiazanie=body.rozwiazanie,
        kolejnosc=k,
        image_url=body.image_url,
        styl=body.styl,
        media_url=body.media_url,
    )
    blok.dane = _dane_bloku(body.typ, body.dane)
    db.add(blok)
    db.commit()
    db.refresh(blok)
    return blok


@router.put("/bloki/{blok_id}", dependencies=[Depends(wymagaj_edytora)], response_model=schemas.Blok)
def edytuj_blok(blok_id: int, dane: schemas.BlokUpdate, db: Session = Depends(get_db)):
    blok = db.query(models.Blok).filter(models.Blok.id == blok_id).first()
    if not blok:
        raise HTTPException(status_code=404, detail="Blok nie znaleziony")
    zmiany = dane.model_dump(exclude_unset=True)
    nowe_dane = zmiany.pop("dane", blok.dane)
    for klucz, wartosc in zmiany.items():
        setattr(blok, klucz, wartosc)
    # Re-validate structured data against the (possibly changed) type
    blok.dane = _dane_bloku(blok.typ, nowe_dane)
    db.commit()
    db.refresh(blok)
    return blok


@router.post("/bloki/{blok_id}/quiz", response_model=schemas.QuizWynikOut)
def sprawdz_quiz(
    blok_id: int,
    body: schemas.QuizOdpowiedziIn,
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    blok = db.query(models.Blok).filter(models.Blok.id == blok_id).first()
    if not blok or blok.typ != "quiz":
        raise HTTPException(status_code=404, detail="Quiz nie znaleziony")
    _sprawdz_widocznosc(blok.temat.dzial.kurs, user, "Quiz nie znaleziony")
    pytania = (blok.dane or {}).get("pytania", [])
    try:
        wynik = ocen_quiz(pytania, body.odpowiedzi)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return schemas.QuizWynikOut(
        poprawne=wynik.poprawne,
        liczba_pytan=wynik.liczba_pytan,
        procent=wynik.procent,
        trafienia=list(wynik.trafienia),
        poprawne_odpowiedzi=list(wynik.poprawne_odpowiedzi),
    )


@router.delete("/bloki/{blok_id}", dependencies=[Depends(wymagaj_edytora)])
def usun_blok(blok_id: int, db: Session = Depends(get_db)):
    blok = db.query(models.Blok).filter(models.Blok.id == blok_id).first()
    if not blok:
        raise HTTPException(status_code=404, detail="Blok nie znaleziony")
    db.delete(blok)
    db.commit()
    return {"status": "success", "message": f"Blok {blok_id} usunięty"}


# =========================================================
# SEKCYJA 5: WYSZUKIWARKA
# =========================================================


@router.get("/szukaj", response_model=schemas.GlobalSearchResponse)
def szukaj_wszystkiego(
    q: str = "",
    db: Session = Depends(get_db),
    user: models.Uzytkownik = Depends(get_uczestnik),
):
    query = q.strip()

    q_dzialy = db.query(models.Dzial).join(models.Kurs, models.Dzial.kurs_id == models.Kurs.id)
    q_tematy = (
        db.query(models.Temat)
        .join(models.Dzial, models.Temat.dzial_id == models.Dzial.id)
        .join(models.Kurs, models.Dzial.kurs_id == models.Kurs.id)
    )
    if _tylko_opublikowane(user):
        q_dzialy = q_dzialy.filter(models.Kurs.is_published.is_(True))
        q_tematy = q_tematy.filter(models.Kurs.is_published.is_(True))

    if query:
        q_dzialy = q_dzialy.filter(models.Dzial.nazwa.contains(query))
        q_tematy = q_tematy.filter(models.Temat.tytul.contains(query))

    wyniki_dzialy = q_dzialy.all()
    wyniki_tematy = q_tematy.all()
    return {"dzialy": wyniki_dzialy, "tematy": wyniki_tematy}
