import pytest

from app.services.vak import WynikVAK, policz_wynik, poprawny_styl, style_dominujace


def test_wyrazny_zwyciezca():
    wynik = policz_wynik(["V"] * 12 + ["A"] * 5 + ["K"] * 3)
    assert wynik == WynikVAK(punkty_v=12, punkty_a=5, punkty_k=3, styl_dominujacy="V")
    assert wynik.punkty == {"V": 12, "A": 5, "K": 3}


@pytest.mark.parametrize(
    "odpowiedzi, oczekiwany",
    [
        (["A"] * 11 + ["V"] * 4 + ["K"] * 5, "A"),
        (["K"] * 20, "K"),
        (["V"], "V"),
    ],
)
def test_styl_dominujacy(odpowiedzi, oczekiwany):
    assert policz_wynik(odpowiedzi).styl_dominujacy == oczekiwany


def test_remis_dwoch_stylow_daje_styl_mieszany():
    wynik = policz_wynik(["V"] * 8 + ["A"] * 8 + ["K"] * 4)
    assert wynik.styl_dominujacy == "VA"


def test_remis_niezalezny_od_kolejnosci_odpowiedzi():
    assert policz_wynik(["K", "A", "K", "A"]).styl_dominujacy == "AK"
    assert policz_wynik(["A", "K", "A", "K"]).styl_dominujacy == "AK"


def test_remis_trzech_stylow():
    assert policz_wynik(["V", "A", "K"]).styl_dominujacy == "VAK"


def test_suma_punktow_rowna_liczbie_odpowiedzi():
    odpowiedzi = ["V", "A", "K", "K", "V", "V", "A"]
    wynik = policz_wynik(odpowiedzi)
    assert wynik.punkty_v + wynik.punkty_a + wynik.punkty_k == len(odpowiedzi)


def test_przyjmuje_dowolny_iterable():
    assert policz_wynik(s for s in "VVA").styl_dominujacy == "V"


def test_nieznany_styl_to_blad():
    with pytest.raises(ValueError):
        policz_wynik(["V", "X"])


def test_brak_odpowiedzi_to_blad():
    with pytest.raises(ValueError):
        policz_wynik([])


def test_style_dominujace_z_brakujacymi_kluczami():
    assert style_dominujace({"A": 2}) == "A"


@pytest.mark.parametrize("styl", ["V", "A", "K", "VA", "VK", "AK", "VAK"])
def test_poprawny_styl(styl):
    assert poprawny_styl(styl)


@pytest.mark.parametrize("styl", [None, "", "X", "AV", "VV", "v", "VAKK"])
def test_niepoprawny_styl(styl):
    assert not poprawny_styl(styl)
