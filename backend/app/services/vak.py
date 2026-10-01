"""Liczenie wyniku ankiety VAK — czyste funkcje, bez bazy i bez FastAPI."""
from dataclasses import dataclass
from typing import Iterable

STYLE = ("V", "A", "K")


@dataclass(frozen=True)
class WynikVAK:
    punkty_v: int
    punkty_a: int
    punkty_k: int
    # One letter for a clear winner, several (in V-A-K order) for a tie, e.g. "VA" or "VAK"
    styl_dominujacy: str

    @property
    def punkty(self) -> dict[str, int]:
        return {"V": self.punkty_v, "A": self.punkty_a, "K": self.punkty_k}


def style_dominujace(punkty: dict[str, int]) -> str:
    """Zwraca style z najwyższą liczbą punktów (remis → kilka liter w kolejności V, A, K)."""
    najwiecej = max(punkty.get(s, 0) for s in STYLE)
    return "".join(s for s in STYLE if punkty.get(s, 0) == najwiecej)


def policz_wynik(style_odpowiedzi: Iterable[str]) -> WynikVAK:
    """Każda odpowiedź daje 1 punkt stylowi, do którego jest przypisana."""
    punkty = {s: 0 for s in STYLE}
    for styl in style_odpowiedzi:
        if styl not in punkty:
            raise ValueError(f"Nieznany styl odpowiedzi: {styl!r}")
        punkty[styl] += 1
    if sum(punkty.values()) == 0:
        raise ValueError("Brak odpowiedzi — nie można policzyć wyniku")
    return WynikVAK(
        punkty_v=punkty["V"],
        punkty_a=punkty["A"],
        punkty_k=punkty["K"],
        styl_dominujacy=style_dominujace(punkty),
    )


def poprawny_styl(styl: str | None) -> bool:
    """Styl użytkownika: niepusty zestaw liter V/A/K bez powtórzeń, w kolejności V, A, K."""
    if not styl:
        return False
    return styl == "".join(s for s in STYLE if s in styl) and all(c in STYLE for c in styl)
