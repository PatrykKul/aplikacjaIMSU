"""Adaptacja przez API: quiz -> zdarzenie, postęp, wagi, rekomendacja, poziom, propozycja stylu."""
import pytest

from app import models

QUIZ = {
    "pytania": [
        {"tresc": f"Pytanie {i}", "odpowiedzi": ["dobra", "zła"], "poprawna": 0} for i in range(10)
    ]
}


def _odp(procent: int) -> dict:
    """Answers giving exactly `procent` (multiples of 10) in the 10-question quiz."""
    dobre = procent // 10
    return {"odpowiedzi": [0] * dobre + [1] * (10 - dobre)}


@pytest.fixture
def kurs(client, nauczyciel):
    """Published course with 3 topics; each has blocks for V/A/K, levels 1/3 and a quiz.

    Returns {"tematy": [id...], "quizy": [blok_id...], "kurs_id": id}.
    """
    h = nauczyciel
    k = client.post("/kursy", json={"nazwa": "Kurs", "opis": "", "is_published": True}, headers=h).json()
    d = client.post(f"/kursy/{k['id']}/dzialy", json={"nazwa": "Dział"}, headers=h).json()
    tematy, quizy = [], []
    for nazwa in ("Pierwszy", "Drugi", "Trzeci"):
        t = client.post(f"/dzialy/{d['id']}/tematy", json={"tytul": nazwa}, headers=h).json()["id"]
        for b in (
            {"typ": "teoria", "tresc": "wspolny"},
            {"typ": "diagram", "tresc": "dla-V", "styl": "V"},
            {"typ": "audio", "tresc": "dla-A", "styl": "A"},
            {"typ": "przyklad", "tresc": "latwy", "poziom": 1},
            {"typ": "przyklad", "tresc": "standard", "poziom": 2},
            {"typ": "przyklad", "tresc": "rozszerzenie", "poziom": 3},
        ):
            assert client.post(f"/tematy/{t}/bloki", json=b, headers=h).status_code == 200
        q = client.post(f"/tematy/{t}/bloki", json={"typ": "quiz", "tresc": "quiz", "dane": QUIZ}, headers=h).json()
        tematy.append(t)
        quizy.append(q["id"])
    return {"tematy": tematy, "quizy": quizy, "kurs_id": k["id"]}


@pytest.fixture
def uczen_v(utworz_uzytkownika):
    """Student with survey result V 8 / A 7 / K 5. Returns (user_id, headers)."""
    return utworz_uzytkownika(
        "uczen", ankieta_wypelniona=True, styl_uczenia="V", styl_zrodlo="ankieta", waga_v=8, waga_a=7, waga_k=5
    )


def _quiz(client, h, blok_id, procent, styl=None):
    body = _odp(procent)
    if styl:
        body["styl"] = styl
    r = client.post(f"/bloki/{blok_id}/quiz", json=body, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def _tresci(client, h, temat_id, styl=None):
    r = client.get(f"/tematy/{temat_id}" + (f"?styl={styl}" if styl else ""), headers=h)
    return [b["tresc"] for b in r.json()["bloki"]], r.json()


# --- survey sets starting weights ---


def test_wagi_startowe_z_ankiety(client, db, utworz_uzytkownika):
    from app.seed import seed_ankieta

    seed_ankieta(db)
    db.commit()
    user_id, h = utworz_uzytkownika("uczen")
    pytania = client.get("/ankieta/pytania", headers=h).json()
    # The editor endpoint is not available to students, so read styles from the DB
    styl_odp = {o.id: o.styl for o in db.query(models.OdpowiedzAnkiety)}
    cel = ["V"] * 12 + ["A"] * 5 + ["K"] * 3
    odpowiedzi = [
        {"pytanie_id": p["id"], "odpowiedz_id": next(o["id"] for o in p["odpowiedzi"] if styl_odp[o["id"]] == s)}
        for p, s in zip(pytania, cel)
    ]
    assert client.post("/ankieta/odpowiedzi", json={"odpowiedzi": odpowiedzi}, headers=h).status_code == 200
    sciezka = client.get("/nauka/sciezka", headers=h).json()
    assert sciezka["wagi"] == {"V": 12, "A": 5, "K": 3}
    assert sciezka["styl_ankiety"] == "V"


# --- quiz result: progress, weights, recommendation ---


def test_zaliczony_quiz_zalicza_temat_i_proponuje_nastepny(client, db, kurs, uczen_v):
    user_id, h = uczen_v
    w = _quiz(client, h, kurs["quizy"][0], 80)
    assert w["zaliczony"] is True
    assert w["rekomendacja"]["typ"] == "nastepny"
    assert w["rekomendacja"]["temat_id"] == kurs["tematy"][1]
    assert "bo quiz z tematu „Pierwszy”: 80%" in w["rekomendacja"]["dlaczego"]
    assert w["wagi"] == {"V": 9, "A": 7, "K": 5}

    postep = db.query(models.PostepTematu).filter_by(user_id=user_id, temat_id=kurs["tematy"][0]).one()
    assert (postep.zaliczony, postep.najlepszy_wynik, postep.liczba_prob, postep.ostatni_styl) == (True, 80, 1, "V")
    zdarzenie = db.query(models.ZdarzenieNauki).filter_by(user_id=user_id, typ="wynik_quizu").one()
    assert (zdarzenie.wartosc, zdarzenie.styl, zdarzenie.blok_id) == (80, "V", kurs["quizy"][0])


def test_niezaliczony_quiz_proponuje_powtorke_w_drugim_stylu(client, kurs, uczen_v):
    _, h = uczen_v
    w = _quiz(client, h, kurs["quizy"][0], 40)
    assert w["zaliczony"] is False
    rek = w["rekomendacja"]
    assert (rek["typ"], rek["styl"], rek["temat_id"]) == ("powtorka", "A", kurs["tematy"][0])
    assert "bo quiz z tematu „Pierwszy”: 40%" in rek["dlaczego"]
    assert w["wagi"] == {"V": 7, "A": 7, "K": 5}

    # The suggested retry really shows the other style's blocks
    tresci, temat = _tresci(client, h, kurs["tematy"][0], styl="A")
    assert "dla-A" in tresci and "dla-V" not in tresci
    assert "powtarzasz temat w innym stylu" in temat["personalizacja"]["dlaczego"][0]


def test_scenariusz_przelaczenia_stylu(client, kurs, uczen_v):
    """Porażka w V, sukces w A -> propozycja; uczeń akceptuje -> materiały dla A."""
    _, h = uczen_v
    w = _quiz(client, h, kurs["quizy"][0], 40)
    assert w["propozycja_stylu"] is None  # V 7 / A 7: tie, no suggestion

    w = _quiz(client, h, kurs["quizy"][0], 100, styl="A")
    assert w["wagi"] == {"V": 7, "A": 8, "K": 5}
    assert w["zaliczony"] is True
    propozycja = w["propozycja_stylu"]
    assert propozycja["styl"] == "A"
    assert propozycja["komunikat"] == "Lepiej Ci idzie z materiałami słuchowymi – przełączyć?"
    assert "V 7 / A 8 / K 5" in propozycja["dlaczego"]
    assert client.get("/nauka/sciezka", headers=h).json()["propozycja_stylu"]["styl"] == "A"

    # Nothing changes until the student decides
    assert client.get("/auth/me", headers=h).json()["styl_uczenia"] == "V"

    r = client.post("/nauka/propozycja-stylu", json={"styl": "A", "akceptuj": True}, headers=h)
    assert r.status_code == 200
    assert r.json()["uzytkownik"]["styl_uczenia"] == "A"
    assert r.json()["uzytkownik"]["styl_zrodlo"] == "adaptacja"
    assert r.json()["wynik_ankiety"] is None or r.json()["wynik_ankiety"]["styl_dominujacy"]

    tresci, temat = _tresci(client, h, kurs["tematy"][1])
    assert "dla-A" in tresci and "dla-V" not in tresci
    assert "propozycji" in temat["personalizacja"]["dlaczego"][0]
    assert client.get("/nauka/sciezka", headers=h).json()["propozycja_stylu"] is None


def test_odrzucona_propozycja_nie_wraca(client, kurs, uczen_v):
    _, h = uczen_v
    _quiz(client, h, kurs["quizy"][0], 40)
    _quiz(client, h, kurs["quizy"][0], 100, styl="A")
    r = client.post("/nauka/propozycja-stylu", json={"styl": "A", "akceptuj": False}, headers=h)
    assert r.status_code == 200
    assert r.json()["uzytkownik"]["styl_uczenia"] == "V"
    assert client.get("/nauka/sciezka", headers=h).json()["propozycja_stylu"] is None
    # Second answer to the same (now outdated) suggestion
    assert client.post("/nauka/propozycja-stylu", json={"styl": "A", "akceptuj": True}, headers=h).status_code == 409


def test_reczny_wybor_stylu_blokuje_propozycje(client, kurs, uczen_v):
    _, h = uczen_v
    client.put("/profil/styl", json={"styl": "V"}, headers=h)
    _quiz(client, h, kurs["quizy"][0], 40)
    w = _quiz(client, h, kurs["quizy"][0], 100, styl="A")
    assert w["wagi"] == {"V": 7, "A": 8, "K": 5}
    assert w["propozycja_stylu"] is None
    assert client.post("/nauka/propozycja-stylu", json={"styl": "A", "akceptuj": True}, headers=h).status_code == 409


def test_powtarzanie_quizu_nie_nabija_wag(client, kurs, uczen_v):
    _, h = uczen_v
    for _ in range(4):
        w = _quiz(client, h, kurs["quizy"][0], 100)
    assert w["wagi"] == {"V": 9, "A": 7, "K": 5}
    for _ in range(3):
        w = _quiz(client, h, kurs["quizy"][0], 0)
    assert w["wagi"] == {"V": 8, "A": 7, "K": 5}


def test_postep_trzyma_najlepszy_wynik_i_nie_cofa_zaliczenia(client, db, kurs, uczen_v):
    user_id, h = uczen_v
    _quiz(client, h, kurs["quizy"][0], 90)
    _quiz(client, h, kurs["quizy"][0], 30)
    postep = db.query(models.PostepTematu).filter_by(user_id=user_id).one()
    assert (postep.zaliczony, postep.najlepszy_wynik, postep.ostatni_wynik, postep.liczba_prob) == (True, 90, 30, 2)


def test_ostatni_temat_i_wszystkie_style_wyprobowane(client, kurs, uczen_v):
    _, h = uczen_v
    _quiz(client, h, kurs["quizy"][0], 100)
    _quiz(client, h, kurs["quizy"][1], 100)
    assert _quiz(client, h, kurs["quizy"][2], 100)["rekomendacja"]["typ"] == "koniec"

    w = _quiz(client, h, kurs["quizy"][2], 10)
    assert w["rekomendacja"]["typ"] == "powtorka" and w["rekomendacja"]["styl"] == "A"
    w = _quiz(client, h, kurs["quizy"][2], 10, styl="A")
    assert w["rekomendacja"]["typ"] == "powtorka" and w["rekomendacja"]["styl"] == "K"
    w = _quiz(client, h, kurs["quizy"][2], 10, styl="K")
    assert w["rekomendacja"]["typ"] == "powtorz"


# --- style sent with the quiz must be one the student could really use ---


def test_styl_quizu_spoza_dozwolonych_jest_odrzucany(client, db, kurs, uczen_v):
    """Uczeń V nie może przypisać wyniku stylowi, którego system mu nie zaproponował."""
    user_id, h = uczen_v
    for styl in ("A", "K"):
        r = client.post(f"/bloki/{kurs['quizy'][0]}/quiz", json={**_odp(100), "styl": styl}, headers=h)
        assert r.status_code == 400, styl
    # Nothing was recorded and the weights did not move
    assert db.query(models.ZdarzenieNauki).filter_by(user_id=user_id).count() == 0
    assert db.query(models.PostepTematu).filter_by(user_id=user_id).count() == 0
    assert client.get("/nauka/sciezka", headers=h).json()["wagi"] == {"V": 8, "A": 7, "K": 5}
    assert client.post(f"/bloki/{kurs['quizy'][0]}/quiz", json={**_odp(100), "styl": "X"}, headers=h).status_code == 422


def test_styl_quizu_wlasny_i_proponowany_sa_przyjmowane(client, kurs, uczen_v):
    _, h = uczen_v
    q = kurs["quizy"][0]
    # Own style, sent explicitly
    assert client.post(f"/bloki/{q}/quiz", json={**_odp(40), "styl": "V"}, headers=h).status_code == 200
    # System proposed A for the retry -> A is accepted, K still is not
    assert client.post(f"/bloki/{q}/quiz", json={**_odp(100), "styl": "K"}, headers=h).status_code == 400
    r = client.post(f"/bloki/{q}/quiz", json={**_odp(100), "styl": "A"}, headers=h)
    assert r.status_code == 200
    assert r.json()["wagi"] == {"V": 7, "A": 8, "K": 5}
    # A style already used in this topic stays valid for another attempt
    assert client.post(f"/bloki/{q}/quiz", json={**_odp(100), "styl": "A"}, headers=h).status_code == 200


def test_propozycja_powtorki_dotyczy_tylko_swojego_tematu(client, kurs, uczen_v):
    _, h = uczen_v
    _quiz(client, h, kurs["quizy"][0], 40)  # A proposed for topic 1 only
    r = client.post(f"/bloki/{kurs['quizy'][1]}/quiz", json={**_odp(100), "styl": "A"}, headers=h)
    assert r.status_code == 400


def test_styl_mieszany_pozwala_na_kazda_swoja_litere(client, kurs, utworz_uzytkownika):
    _, h = utworz_uzytkownika(
        "uczen", ankieta_wypelniona=True, styl_uczenia="VA", styl_zrodlo="ankieta", waga_v=8, waga_a=8, waga_k=4
    )
    q = kurs["quizy"][0]
    assert client.post(f"/bloki/{q}/quiz", json={**_odp(100), "styl": "A"}, headers=h).status_code == 200
    assert client.post(f"/bloki/{q}/quiz", json={**_odp(100), "styl": "K"}, headers=h).status_code == 400


def test_nauczyciel_nie_zostawia_sladow_w_adaptacji(client, db, kurs, nauczyciel):
    r = client.post(f"/bloki/{kurs['quizy'][0]}/quiz", json=_odp(100), headers=nauczyciel)
    assert r.status_code == 200
    assert r.json()["zaliczony"] is None and r.json()["rekomendacja"] is None
    assert db.query(models.ZdarzenieNauki).count() == 0
    assert db.query(models.PostepTematu).count() == 0


# --- difficulty level ---


def test_poziom_trudnosci_steruje_przykladami(client, kurs, uczen_v):
    _, h = uczen_v
    tresci, temat = _tresci(client, h, kurs["tematy"][0])
    assert "standard" in tresci and "latwy" not in tresci and "rozszerzenie" not in tresci
    assert temat["personalizacja"]["poziom"] == 2
    assert "V 0 / A 0 / K 0" not in temat["personalizacja"]["dlaczego"][0]

    # Two weak quizzes in a row -> easier examples
    _quiz(client, h, kurs["quizy"][0], 40)
    _quiz(client, h, kurs["quizy"][1], 50)
    tresci, temat = _tresci(client, h, kurs["tematy"][2])
    assert "latwy" in tresci and "standard" in tresci and "rozszerzenie" not in tresci
    assert temat["personalizacja"]["poziom"] == 1
    assert any("40%, 50%" in d for d in temat["personalizacja"]["dlaczego"])
    assert client.get("/nauka/sciezka", headers=h).json()["poziom"] == 1

    # Two very good quizzes -> extensions
    _quiz(client, h, kurs["quizy"][0], 100)
    _quiz(client, h, kurs["quizy"][1], 90)
    tresci, temat = _tresci(client, h, kurs["tematy"][2])
    assert "rozszerzenie" in tresci and "latwy" not in tresci
    assert temat["personalizacja"]["poziom"] == 3


def test_nauczyciel_widzi_wszystkie_poziomy_i_moze_je_ustawiac(client, kurs, nauczyciel):
    temat = client.get(f"/tematy/{kurs['tematy'][0]}", headers=nauczyciel).json()
    assert {"latwy", "standard", "rozszerzenie"} <= {b["tresc"] for b in temat["bloki"]}
    assert temat["personalizacja"] is None
    blok = next(b for b in temat["bloki"] if b["tresc"] == "latwy")
    assert client.put(f"/bloki/{blok['id']}", json={"poziom": 3}, headers=nauczyciel).json()["poziom"] == 3
    assert client.put(f"/bloki/{blok['id']}", json={"poziom": None}, headers=nauczyciel).json()["poziom"] is None
    assert client.put(f"/bloki/{blok['id']}", json={"poziom": 4}, headers=nauczyciel).status_code == 422


# --- "why you see this" ---


def test_dlaczego_to_widzisz_styl_z_ankiety(client, db, kurs, uczen_v):
    user_id, h = uczen_v
    db.add(models.WynikAnkiety(user_id=user_id, punkty_v=8, punkty_a=7, punkty_k=5, styl_dominujacy="V"))
    db.commit()
    _, temat = _tresci(client, h, kurs["tematy"][0])
    p = temat["personalizacja"]
    assert p["styl"] == "V"
    assert "wzrokowiec" in p["dlaczego"][0] and "V 8 / A 7 / K 5" in p["dlaczego"][0]

    client.put("/profil/styl", json={"styl": "K"}, headers=h)
    _, temat = _tresci(client, h, kurs["tematy"][0])
    assert "ręcznie" in temat["personalizacja"]["dlaczego"][0]


# --- learning path ---


def test_sciezka_ucznia(client, kurs, uczen_v):
    _, h = uczen_v
    s = client.get("/nauka/sciezka", headers=h).json()
    assert s["kursy"][0]["zaliczone"] == 0
    assert [t["tytul"] for t in s["kursy"][0]["tematy"]] == ["Pierwszy", "Drugi", "Trzeci"]
    assert s["nastepny_krok"]["temat_id"] == kurs["tematy"][0]
    assert "pierwszy temat" in s["nastepny_krok"]["dlaczego"]

    _quiz(client, h, kurs["quizy"][0], 100)
    s = client.get("/nauka/sciezka", headers=h).json()
    assert s["kursy"][0]["zaliczone"] == 1
    assert s["kursy"][0]["tematy"][0]["najlepszy_wynik"] == 100
    assert s["nastepny_krok"]["temat_id"] == kurs["tematy"][1]
    assert "kolejny temat" in s["nastepny_krok"]["dlaczego"]

    _quiz(client, h, kurs["quizy"][1], 40)
    s = client.get("/nauka/sciezka", headers=h).json()
    assert s["nastepny_krok"]["temat_id"] == kurs["tematy"][1]
    assert "bo quiz z tematu „Drugi”: 40%" in s["nastepny_krok"]["dlaczego"]

    _quiz(client, h, kurs["quizy"][1], 100)
    _quiz(client, h, kurs["quizy"][2], 100)
    s = client.get("/nauka/sciezka", headers=h).json()
    assert s["nastepny_krok"] is None
    assert s["kursy"][0]["zaliczone"] == 3


def test_sciezka_tylko_dla_ucznia_i_tylko_opublikowane(client, kurs, uczen_v, nauczyciel):
    assert client.get("/nauka/sciezka").status_code == 401
    assert client.get("/nauka/sciezka", headers=nauczyciel).status_code == 403
    client.post("/kursy", json={"nazwa": "Ukryty", "opis": ""}, headers=nauczyciel)
    s = client.get("/nauka/sciezka", headers=uczen_v[1]).json()
    assert [k["nazwa"] for k in s["kursy"]] == ["Kurs"]


def test_sciezka_wymaga_ankiety(client, utworz_uzytkownika):
    _, h = utworz_uzytkownika("uczen")
    r = client.get("/nauka/sciezka", headers=h)
    assert r.status_code == 403 and r.json()["detail"]["kod"] == "ANKIETA_WYMAGANA"


# --- learning events ---


def test_zdarzenia_nauki(client, db, kurs, uczen_v, nauczyciel):
    user_id, h = uczen_v
    temat_id = kurs["tematy"][0]
    for dane in (
        {"temat_id": temat_id, "typ": "otwarcie_tematu", "styl": "V"},
        {"temat_id": temat_id, "typ": "odtworzenie_audio", "blok_id": kurs["quizy"][0]},
        {"temat_id": temat_id, "typ": "czas_w_temacie", "czas_s": 125},
    ):
        assert client.post("/nauka/zdarzenia", json=dane, headers=h).status_code == 201
    zdarzenia = db.query(models.ZdarzenieNauki).filter_by(user_id=user_id).order_by(models.ZdarzenieNauki.id).all()
    assert [z.typ for z in zdarzenia] == ["otwarcie_tematu", "odtworzenie_audio", "czas_w_temacie"]
    assert zdarzenia[2].czas_s == 125

    # Teacher activity is not tracked
    assert client.post("/nauka/zdarzenia", json={"temat_id": temat_id, "typ": "otwarcie_tematu"}, headers=nauczyciel).status_code == 201
    assert db.query(models.ZdarzenieNauki).count() == 3


def test_zdarzenia_walidacja(client, kurs, uczen_v):
    _, h = uczen_v
    t = kurs["tematy"][0]
    # Quiz results can only be recorded by the server
    assert client.post("/nauka/zdarzenia", json={"temat_id": t, "typ": "wynik_quizu"}, headers=h).status_code == 422
    assert client.post("/nauka/zdarzenia", json={"temat_id": 99999, "typ": "otwarcie_tematu"}, headers=h).status_code == 404
    assert client.post("/nauka/zdarzenia", json={"temat_id": t, "typ": "otwarcie_tematu", "blok_id": kurs["quizy"][1]}, headers=h).status_code == 400
    assert client.post("/nauka/zdarzenia", json={"temat_id": t, "typ": "czas_w_temacie", "czas_s": -1}, headers=h).status_code == 422
    assert client.post("/nauka/zdarzenia", json={"temat_id": t, "typ": "otwarcie_tematu"}).status_code == 401


# --- manual completion ---


def test_reczne_ukonczenie_tylko_dla_tematu_bez_quizu(client, db, kurs, uczen_v, nauczyciel):
    user_id, h = uczen_v
    assert client.post(f"/tematy/{kurs['tematy'][0]}/ukoncz", headers=h).status_code == 400

    dzial_id = client.get(f"/tematy/{kurs['tematy'][0]}", headers=nauczyciel).json()["dzial_id"]
    bez_quizu = client.post(f"/dzialy/{dzial_id}/tematy", json={"tytul": "Bez quizu"}, headers=nauczyciel).json()["id"]
    r = client.post(f"/tematy/{bez_quizu}/ukoncz", headers=h)
    assert r.status_code == 200 and r.json()["zaliczony"] is True
    assert client.post(f"/tematy/{bez_quizu}/ukoncz", headers=h).status_code == 200  # idempotent
    assert db.query(models.PostepTematu).filter_by(user_id=user_id, temat_id=bez_quizu).count() == 1
    assert client.post(f"/tematy/{bez_quizu}/ukoncz", headers=nauczyciel).status_code == 403


def test_usuniecie_tematu_usuwa_postep_i_zdarzenia(client, db, kurs, uczen_v, nauczyciel):
    _, h = uczen_v
    _quiz(client, h, kurs["quizy"][0], 100)
    assert client.delete(f"/tematy/{kurs['tematy'][0]}", headers=nauczyciel).status_code == 200
    assert db.query(models.PostepTematu).count() == 0
    assert db.query(models.ZdarzenieNauki).count() == 0


def test_seed_demo_ma_przyklady_na_trzech_poziomach(db):
    from app.seed import seed_kurs_demo

    seed_kurs_demo(db)
    db.commit()
    for temat in db.query(models.Temat):
        assert {b.poziom for b in temat.bloki} >= {None, 1, 3}, temat.tytul
