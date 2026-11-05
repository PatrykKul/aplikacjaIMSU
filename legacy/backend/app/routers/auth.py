from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import ROLA_UCZEN, get_current_user, get_db
from app.security import hash_haslo, sprawdz_haslo, utworz_token

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_out(user: models.Uzytkownik) -> schemas.TokenOut:
    return schemas.TokenOut(
        access_token=utworz_token(user.id, user.rola),
        uzytkownik=schemas.UzytkownikOut.model_validate(user),
    )


@router.post("/rejestracja", response_model=schemas.TokenOut, status_code=status.HTTP_201_CREATED)
def rejestracja(dane: schemas.RejestracjaIn, db: Session = Depends(get_db)):
    if db.query(models.Uzytkownik).filter(models.Uzytkownik.email == dane.email).first():
        raise HTTPException(status_code=409, detail="Konto z tym adresem e-mail już istnieje")
    # Self-registration always creates a student; roles are changed by an admin
    user = models.Uzytkownik(
        email=dane.email,
        imie=dane.imie,
        haslo_hash=hash_haslo(dane.haslo),
        rola=ROLA_UCZEN,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _token_out(user)


@router.post("/logowanie", response_model=schemas.TokenOut)
def logowanie(dane: schemas.LogowanieIn, db: Session = Depends(get_db)):
    user = db.query(models.Uzytkownik).filter(models.Uzytkownik.email == dane.email).first()
    if not user or not user.aktywny or not sprawdz_haslo(dane.haslo, user.haslo_hash):
        raise HTTPException(status_code=401, detail="Nieprawidłowy e-mail lub hasło")
    return _token_out(user)


@router.get("/me", response_model=schemas.UzytkownikOut)
def me(user: models.Uzytkownik = Depends(get_current_user)):
    return user
