"""Dobór bloków do stylu uczenia — czyste funkcje, bez bazy i bez FastAPI."""
import copy
from typing import Any, Iterable, Protocol, TypeVar

from app.services.vak import STYLE


class _BlokLike(Protocol):
    id: int
    styl: str | None
    kolejnosc: int


B = TypeVar("B", bound=_BlokLike)


def style_ucznia(styl: str | None) -> frozenset[str]:
    """'VA' -> {'V', 'A'}; None / '' -> pusty zbiór (uczeń widzi wtedy tylko bloki wspólne)."""
    return frozenset(s for s in (styl or "") if s in STYLE)


def blok_widoczny(styl_bloku: str | None, styl_ucznia: str | None) -> bool:
    """Blok wspólny (styl = None) widzi każdy; blok stylowy — tylko uczeń o tym stylu."""
    if styl_bloku is None:
        return True
    return styl_bloku in style_ucznia(styl_ucznia)


def filtruj_bloki(bloki: Iterable[B], styl_ucznia: str | None) -> list[B]:
    """Bloki wspólne + bloki stylu ucznia, w kolejności `kolejnosc` (remisy wg id)."""
    widoczne = [b for b in bloki if blok_widoczny(b.styl, styl_ucznia)]
    return sorted(widoczne, key=lambda b: (b.kolejnosc, b.id))


def ukryj_klucz_quizu(dane: dict[str, Any] | None) -> dict[str, Any] | None:
    """Kopia danych quizu bez indeksów poprawnych odpowiedzi (wersja dla ucznia)."""
    if not dane or "pytania" not in dane:
        return dane
    kopia = copy.deepcopy(dane)
    for pytanie in kopia["pytania"]:
        pytanie.pop("poprawna", None)
    return kopia
