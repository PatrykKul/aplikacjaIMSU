"""Wspólne zależności FastAPI: sesja bazy, zalogowany użytkownik, role."""
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.security import dekoduj_token

ROLA_ADMIN = "admin"
ROLA_NAUCZYCIEL = "nauczyciel"
ROLA_UCZEN = "uczen"
ROLE = (ROLA_ADMIN, ROLA_NAUCZYCIEL, ROLA_UCZEN)

_bearer = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> models.Uzytkownik:
    blad = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Wymagane logowanie",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if creds is None:
        raise blad
    payload = dekoduj_token(creds.credentials)
    if not payload:
        raise blad
    try:
        user_id = int(payload.get("sub", ""))
    except ValueError:
        raise blad
    user = db.get(models.Uzytkownik, user_id)
    if user is None or not user.aktywny:
        raise blad
    return user


def wymagaj_roli(*role: str) -> Callable[..., models.Uzytkownik]:
    """Dependency: wpuszcza tylko użytkowników o jednej z podanych ról (rola czytana z bazy)."""

    def _sprawdz(user: models.Uzytkownik = Depends(get_current_user)) -> models.Uzytkownik:
        if user.rola not in role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień")
        return user

    return _sprawdz


wymagaj_edytora = wymagaj_roli(ROLA_NAUCZYCIEL, ROLA_ADMIN)
wymagaj_admina = wymagaj_roli(ROLA_ADMIN)
