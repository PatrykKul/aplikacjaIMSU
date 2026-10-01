"""Scenariusze adaptacji na czystych funkcjach."""
import pytest

from app.services import adaptacja as a

WAGI = {"V": 12, "A": 5, "K": 3}


# --- pass threshold ---


@pytest.mark.parametrize("procent, zaliczony", [(100, True), (70, True), (69, False), (0, False)])
def test_prog_zaliczenia_70(procent, zaliczony):
    assert a.czy_zaliczony(procent) is zaliczony


# --- weights ---


def test_wagi_startowe_to_punkty_z_ankiety():
    assert a.wagi_startowe(12, 5, 3) == {"V": 12, "A": 5, "K": 3}


def test_sukces_dodaje_punkt_stylowi_w_ktorym_przerabiano_temat():
    assert a.aktualizuj_wagi(WAGI, "A", sukces=True) == {"V": 12, "A": 6, "K": 3}


def test_porazka_odejmuje_punkt():
    assert a.aktualizuj_wagi(WAGI, "V", sukces=False) == {"V": 11, "A": 5, "K": 3}


def test_styl_mieszany_aktualizuje_oba_style():
    assert a.aktualizuj_wagi(WAGI, "VA", sukces=True) == {"V": 13, "A": 6, "K": 3}


def test_wagi_nie_wychodza_poza_zakres():
    assert a.aktualizuj_wagi({"V": 0, "A": 0, "K": 0}, "V", sukces=False)["V"] == a.WAGA_MIN
    assert a.aktualizuj_wagi({"V": a.WAGA_MAX, "A": 0, "K": 0}, "V", sukces=True)["V"] == a.WAGA_MAX
    assert a.wagi_startowe(999, -5, 3) == {"V": a.WAGA_MAX, "A": a.WAGA_MIN, "K": 3}


def test_aktualizacja_nie_modyfikuje_wejscia_i_ignoruje_brak_stylu():
    wagi = dict(WAGI)
    assert a.aktualizuj_wagi(wagi, None, sukces=True) == WAGI
    a.aktualizuj_wagi(wagi, "V", sukces=True)
    assert wagi == WAGI


def test_waga_liczy_sie_tylko_przy_pierwszym_sukcesie_i_pierwszej_porazce():
    assert a.liczy_sie_do_wag([], sukces=True)
    assert a.liczy_sie_do_wag([], sukces=False)
    assert not a.liczy_sie_do_wag([True], sukces=True)
    assert not a.liczy_sie_do_wag([False, False], sukces=False)
    assert a.liczy_sie_do_wag([False], sukces=True)
    assert not a.liczy_sie_do_wag([False, True], sukces=False)


# --- retry in another style ---


def test_ranking_stylow_i_remisy():
    assert a.ranking_stylow(WAGI) == ["V", "A", "K"]
    assert a.ranking_stylow({"V": 1, "A": 7, "K": 7}) == ["A", "K", "V"]


def test_powtorka_w_drugim_najwyzszym_stylu():
    assert a.styl_do_powtorki(WAGI, "V") == "A"
    assert a.styl_do_powtorki(WAGI, "A") == "V"
    assert a.styl_do_powtorki({"V": 3, "A": 5, "K": 9}, "K") == "A"


def test_powtorka_pomija_style_juz_wyprobowane():
    assert a.styl_do_powtorki(WAGI, "A", wyprobowane={"V"}) == "K"
    assert a.styl_do_powtorki(WAGI, "K", wyprobowane={"V", "A"}) is None


def test_powtorka_dla_stylu_mieszanego():
    assert a.styl_do_powtorki({"V": 8, "A": 8, "K": 4}, "VA") == "K"


# --- style switch suggestion ---


def test_brak_propozycji_gdy_obecny_styl_prowadzi():
    assert a.propozycja_zmiany_stylu(WAGI, "V", "ankieta") is None


def test_propozycja_gdy_inny_styl_zaczyna_dominowac():
    assert a.propozycja_zmiany_stylu({"V": 6, "A": 8, "K": 3}, "V", "ankieta") == "A"
    assert a.propozycja_zmiany_stylu({"V": 6, "A": 8, "K": 3}, "V", "adaptacja") == "A"


def test_reczny_wybor_ma_pierwszenstwo():
    assert a.propozycja_zmiany_stylu({"V": 1, "A": 20, "K": 3}, "V", "reczny") is None


def test_remis_na_czele_nie_daje_propozycji():
    assert a.propozycja_zmiany_stylu({"V": 5, "A": 8, "K": 8}, "V", "ankieta") is None


def test_odrzucona_propozycja_nie_wraca():
    wagi = {"V": 6, "A": 8, "K": 3}
    assert a.propozycja_zmiany_stylu(wagi, "V", "ankieta", odrzucona="A") is None
    # A different leader is a new suggestion
    assert a.propozycja_zmiany_stylu({"V": 6, "A": 8, "K": 9}, "V", "ankieta", odrzucona="A") == "K"


def test_styl_mieszany_zawierajacy_lidera_nie_daje_propozycji():
    assert a.propozycja_zmiany_stylu({"V": 9, "A": 8, "K": 3}, "VA", "ankieta") is None
    assert a.propozycja_zmiany_stylu({"V": 8, "A": 8, "K": 11}, "VA", "ankieta") == "K"


def test_brak_stylu_brak_propozycji():
    assert a.propozycja_zmiany_stylu(WAGI, None, None) is None


def test_komunikat_propozycji():
    assert a.komunikat_propozycji("A") == "Lepiej Ci idzie z materiałami słuchowymi – przełączyć?"


# --- difficulty level ---


@pytest.mark.parametrize(
    "wyniki, poziom",
    [
        ([], 2),
        ([40], 2),
        ([40, 55], 1),
        ([90, 40, 60], 1),
        ([40, 80], 2),
        ([100, 95], 3),
        ([90, 90], 3),
        ([100, 89], 2),
        ([20, 30, 100, 100], 3),
        ([69, 69], 1),
        ([70, 70], 2),
    ],
)
def test_poziom_trudnosci_z_dwoch_ostatnich_quizow(wyniki, poziom):
    assert a.poziom_trudnosci(wyniki) == poziom


@pytest.mark.parametrize(
    "poziom_bloku, poziom_ucznia, widoczny",
    [
        (None, 1, True), (None, 2, True), (None, 3, True),
        (2, 1, True), (2, 3, True),
        (1, 1, True), (1, 2, False), (1, 3, False),
        (3, 3, True), (3, 2, False), (3, 1, False),
    ],
)
def test_blok_na_poziomie(poziom_bloku, poziom_ucznia, widoczny):
    assert a.blok_na_poziomie(poziom_bloku, poziom_ucznia) is widoczny


# --- recommendations with explanations ---


def _rek(procent, **kw):
    dane = dict(tytul_tematu="Pętla for", temat_id=7, styl_przerabiany="V", wagi=WAGI, nastepny_temat=(8, "Funkcje"))
    dane.update(kw)
    return a.rekomendacja_po_quizie(procent=procent, **dane)


def test_zaliczony_quiz_proponuje_nastepny_temat():
    rek = _rek(85)
    assert rek.typ == "nastepny"
    assert rek.temat_id == 8
    assert "Funkcje" in rek.tytul
    assert "bo quiz z tematu „Pętla for”: 85%" in rek.dlaczego


def test_zaliczony_ostatni_temat():
    rek = _rek(100, nastepny_temat=None)
    assert rek.typ == "koniec"
    assert rek.temat_id is None


def test_niezaliczony_quiz_proponuje_powtorke_w_innym_stylu():
    rek = _rek(45)
    assert rek.typ == "powtorka"
    assert rek.styl == "A"
    assert rek.temat_id == 7
    assert "słuchowiec" in rek.tytul
    assert "bo quiz z tematu „Pętla for”: 45%" in rek.dlaczego


def test_niezaliczony_po_wyprobowaniu_wszystkich_stylow():
    rek = _rek(30, styl_przerabiany="K", wyprobowane={"V", "A"})
    assert rek.typ == "powtorz"
    assert rek.styl is None


def test_granica_progu_w_rekomendacji():
    assert _rek(70).typ == "nastepny"
    assert _rek(69).typ == "powtorka"


# --- explanations ---


def test_uzasadnienie_stylu_z_ankiety():
    tekst = a.uzasadnienie_stylu("V", "V", "ankieta", {"V": 12, "A": 5, "K": 3})
    assert "wzrokowiec" in tekst and "V 12 / A 5 / K 3" in tekst


def test_uzasadnienie_stylu_recznego_adaptacji_i_powtorki():
    assert "ręcznie" in a.uzasadnienie_stylu("A", "A", "reczny", None)
    assert "propozycji" in a.uzasadnienie_stylu("A", "A", "adaptacja", None)
    assert "powtarzasz" in a.uzasadnienie_stylu("K", "V", "ankieta", {"V": 1, "A": 1, "K": 1})
    assert "wspólne" in a.uzasadnienie_stylu(None, None, None, None)
    assert "wzrokowiec + słuchowiec" in a.uzasadnienie_stylu("VA", "VA", "ankieta", {"V": 8, "A": 8, "K": 4})


def test_uzasadnienie_poziomu():
    assert "45%, 60%" in a.uzasadnienie_poziomu(1, [45, 60])
    assert "łatwiejsze" in a.uzasadnienie_poziomu(1, [45, 60])
    assert "rozszerzające" in a.uzasadnienie_poziomu(3, [100, 90])
    assert a.uzasadnienie_poziomu(2, [80, 60]) is None


# --- full scenario on pure functions ---


def test_scenariusz_wzrokowiec_ktoremu_lepiej_idzie_ze_sluchu():
    """V 8 / A 7 / K 5: porażka w V, sukces w A -> A wychodzi na prowadzenie -> propozycja przełączenia."""
    wagi = a.wagi_startowe(8, 7, 5)
    assert a.propozycja_zmiany_stylu(wagi, "V", "ankieta") is None

    wagi = a.aktualizuj_wagi(wagi, "V", sukces=False)  # quiz 40% in V
    assert wagi == {"V": 7, "A": 7, "K": 5}
    assert a.styl_do_powtorki(wagi, "V") == "A"
    assert a.propozycja_zmiany_stylu(wagi, "V", "ankieta") is None  # tie: no suggestion yet

    wagi = a.aktualizuj_wagi(wagi, "A", sukces=True)  # retry in A: 100%
    assert wagi == {"V": 7, "A": 8, "K": 5}
    assert a.propozycja_zmiany_stylu(wagi, "V", "ankieta") == "A"
    # After accepting, the suggestion disappears
    assert a.propozycja_zmiany_stylu(wagi, "A", "adaptacja") is None
