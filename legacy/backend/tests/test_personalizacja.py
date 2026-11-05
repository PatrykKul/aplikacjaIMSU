from dataclasses import dataclass

import pytest

from app import models
from app.seed import seed_kurs_demo
from app.seed_kurs import KURS_DEMO
from app.services.personalizacja import blok_widoczny, filtruj_bloki, style_ucznia, ukryj_klucz_quizu
from app.services.quiz import ocen_quiz

QUIZ = {
    "pytania": [
        {"tresc": "2 + 2?", "odpowiedzi": ["3", "4"], "poprawna": 1},
        {"tresc": "Stolica Polski?", "odpowiedzi": ["Warszawa", "Kraków", "Gdańsk"], "poprawna": 0},
    ]
}
CWICZENIE = {"kroki": [{"polecenie": "Krok 1", "podpowiedz": "Wskazówka"}, {"polecenie": "Krok 2", "podpowiedz": None}]}


@dataclass
class B:
    id: int
    styl: str | None
    kolejnosc: int


# =========================================================
# Pure functions
# =========================================================


def test_style_ucznia():
    assert style_ucznia("V") == {"V"}
    assert style_ucznia("VA") == {"V", "A"}
    assert style_ucznia(None) == frozenset()
    assert style_ucznia("X") == frozenset()


@pytest.mark.parametrize(
    "styl_bloku, styl_ucznia_, widoczny",
    [
        (None, "V", True),
        (None, None, True),
        ("V", "V", True),
        ("A", "V", False),
        ("A", "VA", True),
        ("K", "VA", False),
        ("K", None, False),
        ("K", "VAK", True),
    ],
)
def test_blok_widoczny(styl_bloku, styl_ucznia_, widoczny):
    assert blok_widoczny(styl_bloku, styl_ucznia_) is widoczny


def test_filtruj_bloki_wspolne_plus_styl_ucznia_w_kolejnosci():
    bloki = [B(1, "A", 3), B(2, None, 0), B(3, "V", 1), B(4, "K", 2), B(5, None, 4), B(6, "V", 1)]
    assert [b.id for b in filtruj_bloki(bloki, "V")] == [2, 3, 6, 5]
    assert [b.id for b in filtruj_bloki(bloki, "A")] == [2, 1, 5]
    assert [b.id for b in filtruj_bloki(bloki, "K")] == [2, 4, 5]


def test_filtruj_bloki_styl_mieszany_i_brak_stylu():
    bloki = [B(1, "V", 0), B(2, "A", 1), B(3, "K", 2), B(4, None, 3)]
    assert [b.id for b in filtruj_bloki(bloki, "VA")] == [1, 2, 4]
    assert [b.id for b in filtruj_bloki(bloki, None)] == [4]


def test_ukryj_klucz_quizu_nie_modyfikuje_oryginalu():
    bez_klucza = ukryj_klucz_quizu(QUIZ)
    assert all("poprawna" not in p for p in bez_klucza["pytania"])
    assert all("poprawna" in p for p in QUIZ["pytania"])
    assert ukryj_klucz_quizu(None) is None
    assert ukryj_klucz_quizu({"kroki": []}) == {"kroki": []}


def test_ocen_quiz():
    wynik = ocen_quiz(QUIZ["pytania"], [1, 2])
    assert (wynik.poprawne, wynik.liczba_pytan, wynik.procent) == (1, 2, 50)
    assert wynik.trafienia == (True, False)
    assert wynik.poprawne_odpowiedzi == (1, 0)
    assert ocen_quiz(QUIZ["pytania"], [1, 0]).procent == 100
    assert ocen_quiz(QUIZ["pytania"], [None, None]).procent == 0


def test_ocen_quiz_zaokragla_procent():
    pytania = [{"poprawna": 0}] * 3
    assert ocen_quiz(pytania, [0, 0, 1]).procent == 67


def test_ocen_quiz_bledne_dane():
    with pytest.raises(ValueError):
        ocen_quiz(QUIZ["pytania"], [1])
    with pytest.raises(ValueError):
        ocen_quiz([], [])


# =========================================================
# API
# =========================================================


@pytest.fixture
def temat(client, nauczyciel):
    """Published topic with shared, V, A, K blocks and a quiz. Returns the topic id."""
    h = nauczyciel
    kurs = client.post("/kursy", json={"nazwa": "K", "opis": "", "is_published": True}, headers=h).json()
    dzial = client.post(f"/kursy/{kurs['id']}/dzialy", json={"nazwa": "D"}, headers=h).json()
    temat_id = client.post(f"/dzialy/{dzial['id']}/tematy", json={"tytul": "T"}, headers=h).json()["id"]
    bloki = [
        {"typ": "teoria", "tresc": "wspolny-1"},
        {"typ": "diagram", "tresc": "dla-V", "styl": "V"},
        {"typ": "audio", "tresc": "dla-A", "styl": "A"},
        {"typ": "cwiczenie", "tresc": "dla-K", "styl": "K", "dane": CWICZENIE},
        {"typ": "quiz", "tresc": "quiz", "dane": QUIZ},
    ]
    for b in bloki:
        r = client.post(f"/tematy/{temat_id}/bloki", json=b, headers=h)
        assert r.status_code == 200, r.text
    return temat_id


def _tresci(temat_json):
    return [b["tresc"] for b in temat_json["bloki"]]


@pytest.mark.parametrize(
    "styl, oczekiwane",
    [
        ("V", ["wspolny-1", "dla-V", "quiz"]),
        ("A", ["wspolny-1", "dla-A", "quiz"]),
        ("K", ["wspolny-1", "dla-K", "quiz"]),
        ("VA", ["wspolny-1", "dla-V", "dla-A", "quiz"]),
    ],
)
def test_uczen_widzi_bloki_wspolne_i_swojego_stylu(client, temat, utworz_uzytkownika, styl, oczekiwane):
    _, h = utworz_uzytkownika("uczen", ankieta_wypelniona=True, styl_uczenia=styl, styl_zrodlo="ankieta")
    r = client.get(f"/tematy/{temat}", headers=h)
    assert r.status_code == 200
    assert _tresci(r.json()) == oczekiwane
    assert r.json()["styl_widoku"] == styl


def test_reczna_zmiana_stylu_zmienia_widoczne_bloki(client, temat, utworz_uzytkownika):
    _, h = utworz_uzytkownika("uczen", ankieta_wypelniona=True, styl_uczenia="V", styl_zrodlo="ankieta")
    assert "dla-V" in _tresci(client.get(f"/tematy/{temat}", headers=h).json())
    client.put("/profil/styl", json={"styl": "K"}, headers=h)
    tresci = _tresci(client.get(f"/tematy/{temat}", headers=h).json())
    assert "dla-K" in tresci and "dla-V" not in tresci


def test_uczen_moze_obejrzec_temat_w_innym_stylu(client, temat, uczen):
    r = client.get(f"/tematy/{temat}?styl=A", headers=uczen)
    assert _tresci(r.json()) == ["wspolny-1", "dla-A", "quiz"]
    assert r.json()["styl_widoku"] == "A"
    assert client.get(f"/tematy/{temat}?styl=X", headers=uczen).status_code == 422


def test_uczen_nie_dostaje_klucza_quizu(client, temat, uczen):
    quiz = client.get(f"/tematy/{temat}", headers=uczen).json()["bloki"][-1]
    assert quiz["typ"] == "quiz"
    assert len(quiz["dane"]["pytania"]) == 2
    assert all("poprawna" not in p for p in quiz["dane"]["pytania"])
    assert "poprawna" not in client.get(f"/tematy/{temat}?styl=K", headers=uczen).text


def test_nauczyciel_widzi_wszystko_i_podglad_stylu(client, temat, nauczyciel):
    wszystko = client.get(f"/tematy/{temat}", headers=nauczyciel).json()
    assert _tresci(wszystko) == ["wspolny-1", "dla-V", "dla-A", "dla-K", "quiz"]
    assert wszystko["styl_widoku"] is None
    assert wszystko["bloki"][-1]["dane"]["pytania"][0]["poprawna"] == 1

    podglad = client.get(f"/tematy/{temat}?styl=K", headers=nauczyciel).json()
    assert _tresci(podglad) == ["wspolny-1", "dla-K", "quiz"]
    assert podglad["styl_widoku"] == "K"


def test_zmiana_stylu_bloku(client, temat, nauczyciel, uczen):
    blok = client.get(f"/tematy/{temat}", headers=nauczyciel).json()["bloki"][1]
    assert blok["styl"] == "V"
    # Explicit null turns the block into a shared one
    r = client.put(f"/bloki/{blok['id']}", json={"styl": None}, headers=nauczyciel)
    assert r.json()["styl"] is None
    assert "dla-V" in _tresci(client.get(f"/tematy/{temat}?styl=A", headers=uczen).json())
    # Update without `styl` leaves it untouched
    client.put(f"/bloki/{blok['id']}", json={"styl": "K"}, headers=nauczyciel)
    assert client.put(f"/bloki/{blok['id']}", json={"tresc": "x"}, headers=nauczyciel).json()["styl"] == "K"
    assert client.put(f"/bloki/{blok['id']}", json={"styl": "Z"}, headers=nauczyciel).status_code == 422


@pytest.mark.parametrize("typ", ["obraz", "diagram", "wideo", "audio"])
def test_nowe_typy_multimedialne(client, temat, nauczyciel, typ):
    r = client.post(
        f"/tematy/{temat}/bloki",
        json={"typ": typ, "tresc": "x", "styl": "V", "media_url": "/media/a.mp3", "image_url": "/demo/a.svg"},
        headers=nauczyciel,
    )
    assert r.status_code == 200
    assert r.json()["typ"] == typ
    assert r.json()["dane"] is None


def test_nieznany_typ_bloku(client, temat, nauczyciel):
    assert client.post(f"/tematy/{temat}/bloki", json={"typ": "hologram", "tresc": "x"}, headers=nauczyciel).status_code == 422


@pytest.mark.parametrize(
    "typ, dane",
    [
        ("quiz", None),
        ("quiz", {"pytania": []}),
        ("quiz", {"pytania": [{"tresc": "?", "odpowiedzi": ["a", "b"], "poprawna": 2}]}),
        ("quiz", {"pytania": [{"tresc": "?", "odpowiedzi": ["a"], "poprawna": 0}]}),
        ("quiz", {"pytania": [{"tresc": "?", "odpowiedzi": ["a", " "], "poprawna": 0}]}),
        ("cwiczenie", None),
        ("cwiczenie", {"kroki": []}),
        ("cwiczenie", {"kroki": [{"polecenie": ""}]}),
    ],
)
def test_walidacja_danych_quizu_i_cwiczenia(client, temat, nauczyciel, typ, dane):
    r = client.post(f"/tematy/{temat}/bloki", json={"typ": typ, "tresc": "x", "dane": dane}, headers=nauczyciel)
    assert r.status_code == 422


def test_edycja_quizu_i_zmiana_typu(client, temat, nauczyciel):
    quiz = client.get(f"/tematy/{temat}", headers=nauczyciel).json()["bloki"][-1]
    nowe = {"pytania": [{"tresc": "Nowe?", "odpowiedzi": ["tak", "nie"], "poprawna": 0}]}
    r = client.put(f"/bloki/{quiz['id']}", json={"dane": nowe}, headers=nauczyciel)
    assert r.status_code == 200
    assert r.json()["dane"]["pytania"][0]["tresc"] == "Nowe?"
    # Broken data is rejected and nothing changes
    assert client.put(f"/bloki/{quiz['id']}", json={"dane": {"pytania": []}}, headers=nauczyciel).status_code == 422
    # Changing only the text keeps the structured data
    assert client.put(f"/bloki/{quiz['id']}", json={"tresc": "t"}, headers=nauczyciel).json()["dane"] == r.json()["dane"]
    # Plain types do not keep structured data
    assert client.put(f"/bloki/{quiz['id']}", json={"typ": "teoria"}, headers=nauczyciel).json()["dane"] is None


# --- quiz checking ---


def test_sprawdzenie_quizu(client, temat, uczen, nauczyciel):
    quiz_id = client.get(f"/tematy/{temat}", headers=uczen).json()["bloki"][-1]["id"]
    r = client.post(f"/bloki/{quiz_id}/quiz", json={"odpowiedzi": [1, 2]}, headers=uczen)
    assert r.status_code == 200
    wynik = r.json()
    assert (wynik["poprawne"], wynik["liczba_pytan"], wynik["procent"]) == (1, 2, 50)
    assert wynik["trafienia"] == [True, False]
    assert wynik["poprawne_odpowiedzi"] == [1, 0]
    assert client.post(f"/bloki/{quiz_id}/quiz", json={"odpowiedzi": [1, None]}, headers=uczen).json()["procent"] == 50
    assert client.post(f"/bloki/{quiz_id}/quiz", json={"odpowiedzi": [1]}, headers=uczen).status_code == 400
    assert client.post(f"/bloki/{quiz_id}/quiz", json={"odpowiedzi": [1, 0]}).status_code == 401

    teoria_id = client.get(f"/tematy/{temat}", headers=nauczyciel).json()["bloki"][0]["id"]
    assert client.post(f"/bloki/{teoria_id}/quiz", json={"odpowiedzi": [0]}, headers=uczen).status_code == 404


def test_quiz_z_nieopublikowanego_kursu_niedostepny_dla_ucznia(client, nauczyciel, uczen):
    kurs = client.post("/kursy", json={"nazwa": "Ukryty", "opis": ""}, headers=nauczyciel).json()
    dzial = client.post(f"/kursy/{kurs['id']}/dzialy", json={"nazwa": "D"}, headers=nauczyciel).json()
    temat_id = client.post(f"/dzialy/{dzial['id']}/tematy", json={"tytul": "T"}, headers=nauczyciel).json()["id"]
    quiz = client.post(f"/tematy/{temat_id}/bloki", json={"typ": "quiz", "tresc": "q", "dane": QUIZ}, headers=nauczyciel).json()
    assert client.post(f"/bloki/{quiz['id']}/quiz", json={"odpowiedzi": [1, 0]}, headers=uczen).status_code == 404
    assert client.post(f"/bloki/{quiz['id']}/quiz", json={"odpowiedzi": [1, 0]}, headers=nauczyciel).status_code == 200


# --- uploads ---

FORM = {"kurs_nazwa": "Kurs Ą", "dzial_nazwa": "Dział", "temat_nazwa": "Temat"}
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 32


def test_upload_obrazka_i_serwowanie(client, nauczyciel):
    r = client.post("/upload-image", data=FORM, files={"file": ("rys.PNG", PNG, "image/png")}, headers=nauczyciel)
    assert r.status_code == 200
    url = r.json()["image_url"]
    assert url.startswith("/media/kurs-a/dzial/temat/") and url.endswith(".png")
    pobrany = client.get(url)
    assert pobrany.status_code == 200
    assert pobrany.content == PNG


def test_upload_audio(client, nauczyciel):
    r = client.post("/upload-audio", data=FORM, files={"file": ("lekcja.mp3", b"ID3" + b"0" * 16, "audio/mpeg")}, headers=nauczyciel)
    assert r.status_code == 200
    assert r.json()["media_url"].endswith(".mp3")


@pytest.mark.parametrize("nazwa", ["strona.html", "skrypt.js", "obraz.svg", "bez_rozszerzenia", "plik.png.exe"])
def test_upload_odrzuca_niedozwolone_typy(client, nauczyciel, nazwa):
    r = client.post("/upload-image", data=FORM, files={"file": (nazwa, b"<script>alert(1)</script>", "image/png")}, headers=nauczyciel)
    assert r.status_code == 400


def test_upload_audio_nie_przyjmuje_obrazkow_i_pustych_plikow(client, nauczyciel):
    assert client.post("/upload-audio", data=FORM, files={"file": ("a.png", PNG, "image/png")}, headers=nauczyciel).status_code == 400
    assert client.post("/upload-audio", data=FORM, files={"file": ("a.mp3", b"", "audio/mpeg")}, headers=nauczyciel).status_code == 400


def test_upload_za_duzy_plik(client, nauczyciel, monkeypatch):
    from app.routers import kursy

    monkeypatch.setattr(kursy, "MAX_OBRAZ_BYTES", 10)
    r = client.post("/upload-image", data=FORM, files={"file": ("a.png", PNG, "image/png")}, headers=nauczyciel)
    assert r.status_code == 413


def test_upload_tylko_dla_edytorow(client, uczen):
    assert client.post("/upload-image", data=FORM, files={"file": ("a.png", PNG, "image/png")}, headers=uczen).status_code == 403
    assert client.post("/upload-audio", data=FORM, files={"file": ("a.mp3", b"x", "audio/mpeg")}).status_code == 401


# --- demo course seed ---


def test_seed_kursu_demo_kazdy_temat_ma_bloki_v_a_k(client, db, utworz_uzytkownika):
    assert seed_kurs_demo(db) == 1
    db.commit()
    assert seed_kurs_demo(db) == 0  # idempotent

    kurs = db.query(models.Kurs).filter_by(nazwa=KURS_DEMO["nazwa"]).one()
    assert kurs.is_published
    tematy = [t for d in kurs.dzialy for t in d.tematy]
    assert len(tematy) == 4
    for t in tematy:
        style = {b.styl for b in t.bloki}
        assert style == {None, "V", "A", "K"}, t.tytul
        assert [b.typ for b in t.bloki][-1] == "quiz", t.tytul
        assert t.bloki[-1].styl is None, "quiz kończący temat jest wspólny"

    # Each style really gets a different view of the same topic
    widoki = {}
    for styl in "VAK":
        _, h = utworz_uzytkownika("uczen", ankieta_wypelniona=True, styl_uczenia=styl, styl_zrodlo="ankieta")
        widoki[styl] = [b["id"] for b in client.get(f"/tematy/{tematy[0].id}", headers=h).json()["bloki"]]
    assert len({tuple(v) for v in widoki.values()}) == 3


def test_seed_kursu_demo_dane_przechodza_walidacje():
    from app.schemas import BlokCreate, waliduj_dane_bloku

    for dzial in KURS_DEMO["dzialy"]:
        for temat in dzial["tematy"]:
            for b in temat["bloki"]:
                BlokCreate(**b)
                waliduj_dane_bloku(b["typ"], b.get("dane"))
