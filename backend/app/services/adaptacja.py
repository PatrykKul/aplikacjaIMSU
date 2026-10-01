"""Adaptacja w czasie — czyste funkcje (bez bazy, bez FastAPI, bez LLM).

Reguły:
- start: wagi V/A/K = punkty z ankiety,
- quiz >= 70% -> temat zaliczony, proponujemy następny; < 70% -> powtórka w innym stylu,
- po quizie styl, w którym uczeń przerabiał temat, dostaje +1 (sukces) / -1 (porażka),
- gdy inny styl zaczyna dominować -> propozycja przełączenia (decyduje uczeń; ręczny wybór ma pierwszeństwo),
- dwa słabe quizy z rzędu -> łatwiejsze przykłady, dwa bardzo dobre -> rozszerzenia.
"""
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from app.services.vak import STYLE

PROG_ZALICZENIA = 70
PROG_ROZSZERZEN = 90
WAGA_MIN = 0
WAGA_MAX = 30

POZIOM_LATWY = 1
POZIOM_STANDARD = 2
POZIOM_ROZSZERZONY = 3

ZRODLO_ANKIETA = "ankieta"
ZRODLO_RECZNY = "reczny"
ZRODLO_ADAPTACJA = "adaptacja"

NAZWA_STYLU = {"V": "wzrokowiec", "A": "słuchowiec", "K": "kinestetyk"}
MATERIALY_STYLU = {"V": "wzrokowymi", "A": "słuchowymi", "K": "praktycznymi"}

Wagi = dict[str, int]


def czy_zaliczony(procent: int) -> bool:
    return procent >= PROG_ZALICZENIA


def _ogranicz(wartosc: int) -> int:
    return max(WAGA_MIN, min(WAGA_MAX, wartosc))


def wagi_startowe(punkty_v: int, punkty_a: int, punkty_k: int) -> Wagi:
    """Wagi początkowe = punkty z ankiety (przycięte do dozwolonego zakresu)."""
    return {"V": _ogranicz(punkty_v), "A": _ogranicz(punkty_a), "K": _ogranicz(punkty_k)}


def aktualizuj_wagi(wagi: Mapping[str, int], styl: str | None, sukces: bool) -> Wagi:
    """+1 / -1 dla każdego stylu, w którym uczeń przerabiał temat (np. 'A' albo 'VA')."""
    nowe = {s: int(wagi.get(s, 0)) for s in STYLE}
    for s in STYLE:
        if s in (styl or ""):
            nowe[s] = _ogranicz(nowe[s] + (1 if sukces else -1))
    return nowe


def ranking_stylow(wagi: Mapping[str, int]) -> list[str]:
    """Style od najwyższej wagi; remisy w kolejności V, A, K."""
    return sorted(STYLE, key=lambda s: (-int(wagi.get(s, 0)), STYLE.index(s)))


def styl_do_powtorki(wagi: Mapping[str, int], styl_przerabiany: str | None, wyprobowane: Iterable[str] = ()) -> str | None:
    """Najwyżej oceniany styl inny niż ten, w którym uczeń właśnie nie zaliczył.

    Najpierw style jeszcze niewypróbowane w tym temacie; gdy wszystkie były już użyte — None.
    """
    uzyte = set(styl_przerabiany or "") | set(wyprobowane)
    for s in ranking_stylow(wagi):
        if s not in uzyte:
            return s
    return None


def propozycja_zmiany_stylu(
    wagi: Mapping[str, int],
    styl_aktualny: str | None,
    styl_zrodlo: str | None,
    odrzucona: str | None = None,
) -> str | None:
    """Styl, na który warto zaproponować przełączenie, albo None.

    Proponujemy tylko samodzielnego lidera wag, którego nie ma w obecnym stylu.
    Ręczny wybór ucznia ma pierwszeństwo; raz odrzuconej propozycji nie powtarzamy.
    """
    if styl_zrodlo == ZRODLO_RECZNY or not styl_aktualny:
        return None
    kolejnosc = ranking_stylow(wagi)
    lider, drugi = kolejnosc[0], kolejnosc[1]
    if int(wagi.get(lider, 0)) == int(wagi.get(drugi, 0)):
        return None
    if lider in styl_aktualny or lider == odrzucona:
        return None
    return lider


def poziom_trudnosci(wyniki_quizow: Sequence[int]) -> int:
    """Poziom na podstawie dwóch ostatnich quizów (lista od najstarszego do najnowszego)."""
    ostatnie = list(wyniki_quizow)[-2:]
    if len(ostatnie) < 2:
        return POZIOM_STANDARD
    if all(w < PROG_ZALICZENIA for w in ostatnie):
        return POZIOM_LATWY
    if all(w >= PROG_ROZSZERZEN for w in ostatnie):
        return POZIOM_ROZSZERZONY
    return POZIOM_STANDARD


def blok_na_poziomie(poziom_bloku: int | None, poziom_ucznia: int) -> bool:
    """Bloki bez poziomu i standardowe widzi każdy; łatwiejsze i rozszerzone tylko uczeń na tym poziomie."""
    if poziom_bloku is None or poziom_bloku == POZIOM_STANDARD:
        return True
    return poziom_bloku == poziom_ucznia


def liczy_sie_do_wag(poprzednie_wyniki_w_stylu: Iterable[bool], sukces: bool) -> bool:
    """Waga zmienia się tylko przy pierwszym sukcesie / pierwszej porażce w danym temacie i stylu.

    Dzięki temu wielokrotne klikanie tego samego quizu nie „nabija" wag.
    """
    return sukces not in set(poprzednie_wyniki_w_stylu)


# ---------------------------------------------------------------------------
# Recommendations with explanations ("dlaczego to widzisz")
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Rekomendacja:
    typ: str  # "nastepny" | "powtorka" | "koniec" | "powtorz"
    tytul: str
    dlaczego: str
    styl: str | None = None
    temat_id: int | None = None


def rekomendacja_po_quizie(
    *,
    procent: int,
    tytul_tematu: str,
    temat_id: int,
    styl_przerabiany: str | None,
    wagi: Mapping[str, int],
    wyprobowane: Iterable[str] = (),
    nastepny_temat: tuple[int, str] | None = None,
) -> Rekomendacja:
    powod = f"bo quiz z tematu „{tytul_tematu}”: {procent}%"
    if czy_zaliczony(procent):
        if nastepny_temat is None:
            return Rekomendacja(
                typ="koniec",
                tytul="Temat zaliczony — to był ostatni temat w kursie.",
                dlaczego=f"{powod} (próg zaliczenia to {PROG_ZALICZENIA}%).",
            )
        return Rekomendacja(
            typ="nastepny",
            tytul=f"Temat zaliczony! Następny: „{nastepny_temat[1]}”.",
            dlaczego=f"{powod} (próg zaliczenia to {PROG_ZALICZENIA}%).",
            temat_id=nastepny_temat[0],
        )
    inny = styl_do_powtorki(wagi, styl_przerabiany, wyprobowane)
    if inny is None:
        return Rekomendacja(
            typ="powtorz",
            tytul="Spróbuj jeszcze raz — przejrzyj materiał i podejdź do quizu ponownie.",
            dlaczego=f"{powod}, a ten temat był już przerabiany we wszystkich stylach.",
            temat_id=temat_id,
        )
    return Rekomendacja(
        typ="powtorka",
        tytul=f"Spróbuj inaczej: ten sam temat w wersji dla stylu „{NAZWA_STYLU[inny]}”.",
        dlaczego=f"{powod} — poniżej progu {PROG_ZALICZENIA}%, więc proponujemy inny sposób podania materiału.",
        styl=inny,
        temat_id=temat_id,
    )


def komunikat_propozycji(styl: str) -> str:
    return f"Lepiej Ci idzie z materiałami {MATERIALY_STYLU[styl]} – przełączyć?"


def _opis_stylu(styl: str) -> str:
    return " + ".join(NAZWA_STYLU[s] for s in STYLE if s in styl)


def uzasadnienie_stylu(
    styl_widoku: str | None, styl_ucznia: str | None, styl_zrodlo: str | None, punkty: Mapping[str, int] | None
) -> str:
    if not styl_widoku:
        return "Widzisz tylko materiały wspólne, bo nie masz jeszcze określonego stylu uczenia."
    opis = _opis_stylu(styl_widoku)
    if styl_widoku != styl_ucznia:
        return f"Widzisz materiały dla stylu: {opis}, bo powtarzasz temat w innym stylu niż zwykle."
    if styl_zrodlo == ZRODLO_RECZNY:
        return f"Widzisz materiały dla stylu: {opis}, bo wybrałeś ten styl ręcznie w profilu."
    if styl_zrodlo == ZRODLO_ADAPTACJA:
        return f"Widzisz materiały dla stylu: {opis}, bo przełączyłeś się na niego po propozycji opartej na wynikach quizów."
    if punkty:
        return (
            f"Widzisz materiały dla stylu: {opis}, bo tak wyszło w ankiecie "
            f"(V {punkty.get('V', 0)} / A {punkty.get('A', 0)} / K {punkty.get('K', 0)})."
        )
    return f"Widzisz materiały dla stylu: {opis}."


def uzasadnienie_poziomu(poziom: int, wyniki_quizow: Sequence[int]) -> str | None:
    ostatnie = ", ".join(f"{w}%" for w in list(wyniki_quizow)[-2:])
    if poziom == POZIOM_LATWY:
        return f"Widzisz dodatkowe, łatwiejsze przykłady, bo dwa ostatnie quizy poszły słabiej ({ostatnie})."
    if poziom == POZIOM_ROZSZERZONY:
        return f"Widzisz materiały rozszerzające, bo dwa ostatnie quizy poszły bardzo dobrze ({ostatnie})."
    return None
