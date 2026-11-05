"""Pliki wgrywane przez nauczyciela (obrazki, nagrania) — zapis na dysku, serwowane pod /media."""
import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.slugify import slugify

MEDIA_URL_PREFIX = "/media"

ROZSZERZENIA_OBRAZ = frozenset({".png", ".jpg", ".jpeg", ".gif", ".webp"})
ROZSZERZENIA_AUDIO = frozenset({".mp3", ".ogg", ".wav", ".m4a"})

MAX_OBRAZ_BYTES = 10 * 1024 * 1024
MAX_AUDIO_BYTES = 25 * 1024 * 1024


def get_media_root() -> Path:
    env = os.environ.get("MEDIA_ROOT")
    if env:
        return Path(env).resolve()
    # backend/app/media.py -> parents[1] = backend
    return (Path(__file__).resolve().parents[1] / "uploads").resolve()


async def zapisz_upload(
    file: UploadFile,
    czesci_sciezki: tuple[str, ...],
    dozwolone_rozszerzenia: frozenset[str],
    max_bytes: int,
) -> str:
    """Zapisuje plik pod losową nazwą i zwraca jego URL (`/media/...`)."""
    # Whitelist by extension: the file is later served with a type guessed from it
    rozszerzenie = Path(file.filename or "").suffix.lower()
    if rozszerzenie not in dozwolone_rozszerzenia:
        raise HTTPException(
            status_code=400,
            detail=f"Niedozwolony typ pliku. Dozwolone: {', '.join(sorted(dozwolone_rozszerzenia))}",
        )
    tresc = await file.read(max_bytes + 1)
    if len(tresc) > max_bytes:
        raise HTTPException(status_code=413, detail="Plik jest za duży")
    if not tresc:
        raise HTTPException(status_code=400, detail="Plik jest pusty")

    slugi = tuple(slugify(c) or "bez-nazwy" for c in czesci_sciezki)
    katalog = get_media_root().joinpath(*slugi)
    katalog.mkdir(parents=True, exist_ok=True)
    nazwa = f"{uuid.uuid4().hex}{rozszerzenie}"
    (katalog / nazwa).write_bytes(tresc)
    return "/".join((MEDIA_URL_PREFIX, *slugi, nazwa))
