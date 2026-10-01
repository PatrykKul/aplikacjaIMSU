"""Hasła (bcrypt) i tokeny JWT."""
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

JWT_SECRET = os.getenv("JWT_SECRET", "").strip()
if not JWT_SECRET:
    # Safe fallback: random secret per process (tokens stop working after a restart)
    JWT_SECRET = secrets.token_urlsafe(48)
    logger.warning("Brak JWT_SECRET w .env — użyto losowego sekretu (tokeny wygasną po restarcie serwera).")


def hash_haslo(haslo: str) -> str:
    return bcrypt.hashpw(haslo.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def sprawdz_haslo(haslo: str, haslo_hash: str) -> bool:
    try:
        return bcrypt.checkpw(haslo.encode("utf-8"), haslo_hash.encode("utf-8"))
    except ValueError:
        return False


def utworz_token(user_id: int, rola: str) -> str:
    teraz = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "rola": rola,
        "iat": teraz,
        "exp": teraz + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def dekoduj_token(token: str) -> dict | None:
    """Zwraca payload albo None, gdy token jest nieprawidłowy lub wygasł."""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None
