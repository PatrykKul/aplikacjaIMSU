"""Poprawność merytoryczna kursu „Matematyka: funkcja liniowa".

Każda liczba z przykładów, zadań i kluczy quizów jest tu przeliczana od nowa na ułamkach
(`fractions.Fraction`) i porównywana z tym, co jest zapisane w treści kursu.
"""
import re
import xml.etree.ElementTree as ET
from fractions import Fraction as F

import pytest

from app import models
from app.media import get_media_root
from app.schemas import BlokCreate, waliduj_dane_bloku
from app.seed import seed, seed_kurs_matematyka
from app.seed_matematyka import (
    KATALOG_WYKRESOW,
    KURS_MATEMATYKA,
    WSZYSTKIE_WYKRESY,
    punkt_tex,
    tex,
    wzor_tex,
)
from app.wykresy import JEDNOSTKA, MARGINES, ZNAK_TYTULU_PX, liczba_tekst, linie_tytulu, wykres_svg, wzor_tekst

TEMATY = [t for d in KURS_MATEMATYKA["dzialy"] for t in d["tematy"]]
BLOKI = [(t["tytul"], i, b) for t in TEMATY for i, b in enumerate(t["bloki"])]
POLA_SEEDA = {"sprawdzenia", "sprawdzenia_quizu"}


def _tekst(blok: dict) -> str:
    """Cała treść bloku widoczna dla ucznia."""
    czesci = [blok["tresc"], blok.get("odpowiedz") or "", blok.get("rozwiazanie") or ""]
    for krok in (blok.get("dane") or {}).get("kroki", []):
        czesci += [krok["polecenie"], krok["podpowiedz"] or ""]
    return "\n".join(czesci)


# ---------------------------------------------------------------------------
# Independent calculations
# ---------------------------------------------------------------------------


def f(a, b, x) -> F:
    return F(a) * F(x) + F(b)


def zero(a, b) -> F:
    return -F(b) / F(a)


def prosta_przez(p1, p2) -> tuple[F, F]:
    (x1, y1), (x2, y2) = p1, p2
    a = (F(y2) - F(y1)) / (F(x2) - F(x1))
    return a, F(y1) - a * F(x1)


def monotonicznosc(a) -> str:
    return "rosnąca" if F(a) > 0 else "malejąca" if F(a) < 0 else "stała"


def oblicz(typ: str, p: dict) -> str:
    """Oczekiwany zapis (taki, jaki ma stać w treści) wyliczony z danych."""
    if typ == "wartosc":
        return f"f({tex(p['x'])}) = {tex(f(p['a'], p['b'], p['x']))}"
    if typ == "punkt":
        return punkt_tex(p["x"], f(p["a"], p["b"], p["x"]))
    if typ == "zero":
        return f"x_0 = {tex(zero(p['a'], p['b']))}"
    if typ == "ox":
        return punkt_tex(zero(p["a"], p["b"]), 0)
    if typ == "oy":
        return punkt_tex(0, f(p["a"], p["b"], 0))
    if typ == "wzor":
        return wzor_tex(p["a"], p["b"])
    if typ == "monotonicznosc":
        return monotonicznosc(p["a"])
    if typ == "a_z_punktow":
        return f"a = {tex(prosta_przez(p['p1'], p['p2'])[0])}"
    if typ == "b_z_punktow":
        return f"b = {tex(prosta_przez(p['p1'], p['p2'])[1])}"
    if typ == "wzor_z_punktow":
        return wzor_tex(*prosta_przez(p["p1"], p["p2"]))
    if typ == "koszt":
        return f"{tex(f(p['a'], p['b'], p['x']))} zł"
    if typ == "argument":
        return f"{tex((F(p['y']) - F(p['b'])) / F(p['a']))} km"
    if typ == "pole":
        # Right triangle cut off by the axes
        return f"P = {tex(abs(zero(p['a'], p['b'])) * abs(F(p['b'])) / 2)}"
    if typ == "prog":
        # Coefficient p*m + q changes sign at m = -q/p
        return tex(-F(p["q"]) / F(p["p"]))
    raise AssertionError(f"Nieznany typ sprawdzenia: {typ}")


# ---------------------------------------------------------------------------
# Formatting helpers themselves
# ---------------------------------------------------------------------------


def test_formatowanie_tex():
    assert tex(3) == "3"
    assert tex(F(-6, 2)) == "-3"
    assert tex(F(3, 2)) == r"\tfrac{3}{2}"
    assert tex(F(-3, 2)) == r"-\tfrac{3}{2}"
    assert punkt_tex(F(5, 2), 0) == r"(\tfrac{5}{2}, 0)"
    assert wzor_tex(2, 3) == "y = 2x + 3"
    assert wzor_tex(-1, 4) == "y = -x + 4"
    assert wzor_tex(1, -1) == "y = x - 1"
    assert wzor_tex(2, 0) == "y = 2x"
    assert wzor_tex(0, 5) == "y = 5"
    assert wzor_tex(F(3, 4), F(11, 4)) == r"y = \tfrac{3}{4}x + \tfrac{11}{4}"
    assert wzor_tekst(-2, 3) == "y = −2x + 3"
    assert wzor_tekst(0, 1) == "y = 1"
    assert liczba_tekst(F(-3, 2)) == "−3/2"


# ---------------------------------------------------------------------------
# Structure of the course
# ---------------------------------------------------------------------------


def test_struktura_kursu():
    assert KURS_MATEMATYKA["nazwa"] == "Matematyka: funkcja liniowa"
    assert [d["nazwa"] for d in KURS_MATEMATYKA["dzialy"]] == ["Podstawy", "Zastosowania"]
    assert [len(d["tematy"]) for d in KURS_MATEMATYKA["dzialy"]] == [2, 2]


@pytest.mark.parametrize("temat", TEMATY, ids=lambda t: t["tytul"])
def test_kazdy_temat_ma_ten_sam_uklad(temat):
    bloki = temat["bloki"]
    typy = [b["typ"] for b in bloki]
    assert typy[0] == "teoria" and bloki[0].get("styl") is None
    assert "$$" in bloki[0]["tresc"], "ściąga ma wzór w KaTeX"

    v = [b for b in bloki if b.get("styl") == "V"]
    assert [b["typ"] for b in v] == ["diagram", "obraz"]
    assert all(b["image_url"].startswith("/media/demo/matematyka/") and b["image_url"].endswith(".svg") for b in v)
    assert [b["typ"] for b in bloki if b.get("styl") == "A"] == ["audio"]
    assert [b["typ"] for b in bloki if b.get("styl") == "K"] == ["cwiczenie"]

    przyklady = [b for b in bloki if b["typ"] == "przyklad"]
    assert [b["poziom"] for b in przyklady] == [1, 2, 3]
    assert all(b.get("styl") is None for b in przyklady)

    assert typy.count("uwaga") == 1 and "Typowy błąd" in next(b for b in bloki if b["typ"] == "uwaga")["tresc"]
    zadanie = next(b for b in bloki if b["typ"] == "zadanie")
    assert zadanie["odpowiedz"] and zadanie["rozwiazanie"] and zadanie.get("styl") is None

    assert typy[-1] == "quiz" and bloki[-1].get("styl") is None
    assert 4 <= len(bloki[-1]["dane"]["pytania"]) <= 5


@pytest.mark.parametrize("tytul, i, blok", BLOKI, ids=lambda v: v if isinstance(v, (str, int)) else v["typ"])
def test_bloki_przechodza_walidacje_api(tytul, i, blok):
    dane = {k: v for k, v in blok.items() if k not in POLA_SEEDA}
    BlokCreate(**dane)
    waliduj_dane_bloku(blok["typ"], blok.get("dane"))


@pytest.mark.parametrize("temat", TEMATY, ids=lambda t: t["tytul"])
def test_audio_jest_napisane_slownie(temat):
    """Tekst dla lektora: bez LaTeX-a, symboli i cyfr."""
    audio = next(b for b in temat["bloki"] if b["typ"] == "audio")["tresc"]
    assert not re.search(r"[$\\=+<>^_{}/*0-9]", audio), re.findall(r"[$\\=+<>^_{}/*0-9]", audio)
    assert "igrek" in audio and "iks" in audio
    assert max(len(z.split()) for z in re.split(r"[.?!]", audio)) <= 30, "krótkie zdania"


# ---------------------------------------------------------------------------
# Every number in examples, tasks, theory and exercises
# ---------------------------------------------------------------------------

SPRAWDZENIA = [
    (tytul, i, blok, s) for tytul, i, blok in BLOKI for s in blok.get("sprawdzenia", [])
]


def test_kazdy_blok_z_liczbami_ma_sprawdzenia():
    for tytul, i, blok in BLOKI:
        if blok["typ"] in ("teoria", "przyklad", "uwaga", "zadanie", "cwiczenie", "diagram", "obraz"):
            assert blok.get("sprawdzenia"), f"{tytul} / blok {i} ({blok['typ']})"


@pytest.mark.parametrize(
    "tytul, i, blok, sprawdzenie",
    SPRAWDZENIA,
    ids=[f"{t[:14]}-{i}-{s[0]}-{n}" for n, (t, i, _, s) in enumerate(SPRAWDZENIA)],
)
def test_liczby_w_tresci_zgadzaja_sie_z_obliczeniami(tytul, i, blok, sprawdzenie):
    typ, parametry, zapis_w_tresci = sprawdzenie
    assert oblicz(typ, parametry) == zapis_w_tresci
    assert zapis_w_tresci in _tekst(blok), f"„{zapis_w_tresci}” nie występuje w treści bloku"


def test_odpowiedz_zadania_zgadza_sie_z_rozwiazaniem():
    """Wszystko, co sprawdzamy w zadaniu, musi być w rozwiązaniu, a wynik końcowy — także w odpowiedzi."""
    for tytul, _, blok in BLOKI:
        if blok["typ"] != "zadanie":
            continue
        for typ, parametry, zapis in blok["sprawdzenia"]:
            assert zapis in blok["rozwiazanie"], (tytul, zapis)
        koncowe = blok["sprawdzenia"][-1][2]
        assert koncowe in blok["odpowiedz"], (tytul, koncowe)


# ---------------------------------------------------------------------------
# Quiz keys
# ---------------------------------------------------------------------------

PYTANIA = [
    (t["tytul"], n, pytanie, spr)
    for t in TEMATY
    for n, (pytanie, spr) in enumerate(zip(t["bloki"][-1]["dane"]["pytania"], t["bloki"][-1]["sprawdzenia_quizu"]))
]


def _punkt_z_tekstu(tekst: str) -> tuple[F, F]:
    x, y = re.fullmatch(r"\$\((-?\d+), (-?\d+)\)\$", tekst).groups()
    return F(x), F(y)


def poprawna_odpowiedz(pytanie: dict, s: dict) -> list[bool]:
    """Dla każdej odpowiedzi: czy jest poprawna wg niezależnych obliczeń."""
    odp = pytanie["odpowiedzi"]
    typ = s["typ"]
    if typ == "a":
        return [o == f"${tex(s['a'])}$" for o in odp]
    if typ == "b":
        return [o == f"${tex(s['b'])}$" for o in odp]
    if typ == "wartosc":
        return [o == f"${tex(f(s['a'], s['b'], s['x']))}$" for o in odp]
    if typ == "oy":
        return [o == f"${punkt_tex(0, f(s['a'], s['b'], 0))}$" for o in odp]
    if typ == "zmiana":
        a = F(s["a"])
        oczekiwana = f"{'wzrośnie' if a > 0 else 'zmaleje'} o ${tex(abs(a))}$"
        return [o == oczekiwana for o in odp]
    if typ == "monotonicznosc":
        return [o.split(",")[0] == monotonicznosc(s["a"]) for o in odp]
    if typ == "pozioma":
        assert F(s["a"]) == 0
        return ["pozioma" in o for o in odp]
    if typ == "punkt_na_wykresie":
        assert [_punkt_z_tekstu(o) for o in odp] == [(F(x), F(y)) for x, y in s["punkty"]]
        return [f(s["a"], s["b"], x) == y for x, y in s["punkty"]]
    if typ == "parametr_rosnaca":
        # (p*m + q) > 0 with p > 0  <=>  m > -q/p
        assert F(s["p"]) > 0
        return [o == f"$m > {tex(-F(s['q']) / F(s['p']))}$" for o in odp]
    if typ == "zero":
        return [o == f"${tex(zero(s['a'], s['b']))}$" for o in odp]
    if typ == "brak_zera":
        assert F(s["a"]) == 0 and F(s["b"]) != 0
        return [o.startswith("nie ma") for o in odp]
    if typ == "a_z_punktow":
        return [o == f"${tex(prosta_przez(s['p1'], s['p2'])[0])}$" for o in odp]
    if typ == "b_z_a_i_punktu":
        x, y = s["p"]
        return [o == f"${tex(F(y) - F(s['a']) * F(x))}$" for o in odp]
    if typ == "wzor_z_punktow":
        # Each option is a line; the right one passes through both points
        assert [f"${wzor_tex(a, b)}$" for a, b in s["opcje_ab"]] == odp
        return [all(f(a, b, x) == y for x, y in (s["p1"], s["p2"])) for a, b in s["opcje_ab"]]
    raise AssertionError(f"Nieznany typ pytania: {typ}")


@pytest.mark.parametrize("tytul, n, pytanie, spr", PYTANIA, ids=[f"{t[:14]}-pyt{n + 1}" for t, n, _, _ in PYTANIA])
def test_klucz_quizu_zgadza_sie_z_obliczeniami(tytul, n, pytanie, spr):
    trafione = poprawna_odpowiedz(pytanie, spr)
    assert trafione.count(True) == 1, f"dokładnie jedna odpowiedź ma być poprawna: {trafione}"
    assert trafione.index(True) == pytanie["poprawna"]
    assert len(set(pytanie["odpowiedzi"])) == len(pytanie["odpowiedzi"])


def test_poprawna_odpowiedz_nie_stoi_zawsze_na_tym_samym_miejscu():
    for temat in TEMATY:
        pozycje = {p["poprawna"] for p in temat["bloki"][-1]["dane"]["pytania"]}
        assert len(pozycje) >= 2, temat["tytul"]


# ---------------------------------------------------------------------------
# Charts: generated from the same data as the text
# ---------------------------------------------------------------------------

SVG = "{http://www.w3.org/2000/svg}"


@pytest.mark.parametrize("wykres", WSZYSTKIE_WYKRESY, ids=lambda w: w.plik)
def test_punkty_wykresu_leza_na_prostych(wykres):
    for p in wykres.punkty:
        assert any(pr.wartosc(p.x) == F(p.y) for pr in wykres.proste), (wykres.plik, p)
        if p.rola == "miejsce_zerowe":
            glowna = wykres.proste[0]
            assert F(p.y) == 0 and F(p.x) == zero(glowna.a, glowna.b)
        if p.rola == "przeciecie_oy":
            assert F(p.x) == 0 and any(F(pr.b) == F(p.y) for pr in wykres.proste)
        # Everything fits in the drawing area
        assert wykres.x_min <= p.x <= wykres.x_max and wykres.y_min <= p.y <= wykres.y_max
    if wykres.schodek:
        s, glowna = wykres.schodek, wykres.proste[0]
        assert glowna.wartosc(s.x1) == F(s.y1) and glowna.wartosc(s.x2) == F(s.y2)
        assert (F(s.y2) - F(s.y1)) / (F(s.x2) - F(s.x1)) == F(glowna.a)


@pytest.mark.parametrize("wykres", WSZYSTKIE_WYKRESY, ids=lambda w: w.plik)
def test_svg_zawiera_te_same_dane(wykres):
    root = ET.fromstring(wykres_svg(wykres))
    proste = [(F(e.get("data-a")), F(e.get("data-b"))) for e in root.iter(f"{SVG}line") if e.get("class") == "prosta"]
    assert proste == [(F(p.a), F(p.b)) for p in wykres.proste]
    punkty = [(e.get("data-rola"), F(e.get("data-x")), F(e.get("data-y"))) for e in root.iter(f"{SVG}circle")]
    assert punkty == [(p.rola, F(p.x), F(p.y)) for p in wykres.punkty]
    opisy = " ".join(e.text or "" for e in root.iter(f"{SVG}text"))
    for p in wykres.proste:
        if not wykres.etykiety_prostych:
            assert wzor_tekst(p.a, p.b) in opisy
    # Axes have a scale with numbers
    assert liczba_tekst(wykres.x_max) in opisy and liczba_tekst(wykres.y_min) in opisy


@pytest.mark.parametrize("wykres", WSZYSTKIE_WYKRESY, ids=lambda w: w.plik)
def test_tytul_wykresu_miesci_sie_w_obrazku(wykres):
    szer = 2 * MARGINES + (wykres.x_max - wykres.x_min) * JEDNOSTKA
    linie = linie_tytulu(wykres.tytul, szer)
    assert len(linie) <= 2
    assert all(len(linia) * ZNAK_TYTULU_PX <= szer - 20 for linia in linie), linie
    root = ET.fromstring(wykres_svg(wykres))
    assert [e.text for e in root.iter(f"{SVG}text") if e.get("class") == "tytul"] == linie


def test_wzory_wyroznione_sa_w_osobnych_liniach():
    """`$$` musi stać w osobnej linii — inaczej wzór renderuje się jak zwykły wzór w tekście."""
    for tytul, i, blok in BLOKI:
        for linia in _tekst(blok).splitlines():
            assert "$$" not in linia or linia.strip() == "$$", (tytul, i, linia)


@pytest.mark.parametrize("temat", TEMATY, ids=lambda t: t["tytul"])
def test_punkty_z_wykresow_zgadzaja_sie_z_trescia(temat):
    """Miejsce zerowe i przecięcie z OY zaznaczone na wykresie są tymi samymi punktami, o których mówi tekst."""
    bloki_v = [b for b in temat["bloki"] if b.get("styl") == "V"]
    assert [b["image_url"].rsplit("/", 1)[1] for b in bloki_v] == [w.plik for w in temat["wykresy"]]
    for wykres, blok in zip(temat["wykresy"], bloki_v):
        for p in wykres.punkty:
            if p.rola in ("miejsce_zerowe", "przeciecie_oy"):
                assert punkt_tex(p.x, p.y) in blok["tresc"], (wykres.plik, p)
        glowna = wykres.proste[0]
        # The formula or its coefficient appears in the caption
        assert wzor_tex(glowna.a, glowna.b) in blok["tresc"] or f"a = {tex(glowna.a)}" in blok["tresc"] or "a > 0" in blok["tresc"]


# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def test_seed_kursu_matematyki_jest_idempotentny_i_nie_rusza_pythona(db):
    seed(db)
    db.commit()
    kursy_po_pierwszym = {k.nazwa: k.id for k in db.query(models.Kurs)}
    bloki_po_pierwszym = db.query(models.Blok).count()
    assert set(kursy_po_pierwszym) == {"Podstawy programowania w Pythonie", "Matematyka: funkcja liniowa"}

    wynik = seed(db)
    db.commit()
    assert wynik["kurs_matematyka"] == 0 and wynik["kurs_demo"] == 0
    assert {k.nazwa: k.id for k in db.query(models.Kurs)} == kursy_po_pierwszym
    assert db.query(models.Blok).count() == bloki_po_pierwszym

    kurs = db.query(models.Kurs).filter_by(nazwa="Matematyka: funkcja liniowa").one()
    assert kurs.is_published
    assert [t.tytul for d in kurs.dzialy for t in d.tematy] == [t["tytul"] for t in TEMATY]


def test_seed_zapisuje_wykresy_i_sa_serwowane(client, db):
    katalog = get_media_root().joinpath(*KATALOG_WYKRESOW)
    assert seed_kurs_matematyka(db) == 1
    db.commit()
    for wykres in WSZYSTKIE_WYKRESY:
        plik = katalog / wykres.plik
        assert plik.read_text(encoding="utf-8") == wykres_svg(wykres)
        r = client.get(f"/media/demo/matematyka/{wykres.plik}")
        assert r.status_code == 200 and r.headers["content-type"].startswith("image/svg+xml")

    # A deleted file is restored by the next seed run even though the course already exists
    (katalog / WSZYSTKIE_WYKRESY[0].plik).unlink()
    assert seed_kurs_matematyka(db) == 0
    assert (katalog / WSZYSTKIE_WYKRESY[0].plik).exists()


@pytest.mark.parametrize("styl, typy", [("V", {"diagram", "obraz"}), ("A", {"audio"}), ("K", {"cwiczenie"})])
def test_uczen_widzi_temat_matematyki_w_swoim_stylu(client, db, utworz_uzytkownika, styl, typy):
    seed_kurs_matematyka(db)
    db.commit()
    temat = db.query(models.Temat).filter_by(tytul="Miejsce zerowe i punkty przecięcia z osiami").one()
    _, h = utworz_uzytkownika("uczen", ankieta_wypelniona=True, styl_uczenia=styl, styl_zrodlo="ankieta")
    bloki = client.get(f"/tematy/{temat.id}", headers=h).json()["bloki"]
    stylowe = {b["typ"] for b in bloki if b["styl"] is not None}
    assert stylowe == typy
    assert {b["styl"] for b in bloki} == {None, styl}
    # Standard level: only the level-2 example
    assert [b["poziom"] for b in bloki if b["typ"] == "przyklad"] == [2]
    assert "poprawna" not in str(bloki[-1]["dane"])
