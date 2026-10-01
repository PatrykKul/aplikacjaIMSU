from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.deps import get_db, wymagaj_admina

router = APIRouter(prefix="/uzytkownicy", tags=["uzytkownicy"])


@router.get("", response_model=List[schemas.UzytkownikOut])
def lista_uzytkownikow(
    db: Session = Depends(get_db),
    _admin: models.Uzytkownik = Depends(wymagaj_admina),
):
    return db.query(models.Uzytkownik).order_by(models.Uzytkownik.id.asc()).all()


@router.put("/{user_id}/rola", response_model=schemas.UzytkownikOut)
def zmien_role(
    user_id: int,
    dane: schemas.ZmianaRoliIn,
    db: Session = Depends(get_db),
    admin: models.Uzytkownik = Depends(wymagaj_admina),
):
    user = db.get(models.Uzytkownik, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Użytkownik nie znaleziony")
    # Prevents locking the system out of its last admin
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Nie można zmienić własnej roli")
    user.rola = dane.rola
    db.commit()
    db.refresh(user)
    return user
