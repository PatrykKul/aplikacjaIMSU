"""Ocenianie quizu — czysta funkcja."""
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class WynikQuizu:
    poprawne: int
    liczba_pytan: int
    procent: int  # 0–100, rounded
    trafienia: tuple[bool, ...]
    poprawne_odpowiedzi: tuple[int, ...]


def ocen_quiz(pytania: Sequence[dict[str, Any]], odpowiedzi: Sequence[int | None]) -> WynikQuizu:
    """Porównuje odpowiedzi ucznia (indeks lub None = brak) z kluczem quizu."""
    if not pytania:
        raise ValueError("Quiz nie ma pytań")
    if len(odpowiedzi) != len(pytania):
        raise ValueError("Liczba odpowiedzi musi być równa liczbie pytań")
    klucz = tuple(int(p["poprawna"]) for p in pytania)
    trafienia = tuple(o is not None and o == k for o, k in zip(odpowiedzi, klucz))
    poprawne = sum(trafienia)
    return WynikQuizu(
        poprawne=poprawne,
        liczba_pytan=len(pytania),
        procent=round(100 * poprawne / len(pytania)),
        trafienia=trafienia,
        poprawne_odpowiedzi=klucz,
    )
