from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import get_settings
from app.modules.identity.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_is_hashed_and_verified() -> None:
    password_hash = hash_password("tajne-haslo")
    assert password_hash != "tajne-haslo"
    assert verify_password("tajne-haslo", password_hash)
    assert not verify_password("inne-haslo", password_hash)


def test_verify_password_with_corrupted_hash_returns_false() -> None:
    assert verify_password("cokolwiek", "not-a-hash") is False


def test_token_round_trip() -> None:
    assert decode_access_token(create_access_token(42)) == 42


def test_decode_rejects_garbage() -> None:
    assert decode_access_token("not.a.token") is None


def test_decode_rejects_token_without_expiration() -> None:
    settings = get_settings()
    token = jwt.encode({"sub": "1"}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    assert decode_access_token(token) is None


def test_decode_rejects_expired_token() -> None:
    settings = get_settings()
    past = datetime.now(UTC) - timedelta(minutes=1)
    token = jwt.encode(
        {"sub": "1", "exp": past}, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    assert decode_access_token(token) is None
