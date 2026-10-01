from app.services import ai_generator


def _utworz_temat(client, h, opublikowany: bool = True) -> int:
    kurs = client.post(
        "/kursy", json={"nazwa": "Kurs testowy", "opis": "Opis", "is_published": opublikowany}, headers=h
    ).json()
    dzial = client.post(f"/kursy/{kurs['id']}/dzialy", json={"nazwa": "Dział"}, headers=h).json()
    temat = client.post(f"/dzialy/{dzial['id']}/tematy", json={"tytul": "Temat"}, headers=h).json()
    return temat["id"]


def test_serwer_dziala(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_pusta_baza_zwraca_pusta_liste_kursow(client, nauczyciel):
    r = client.get("/kursy", headers=nauczyciel)
    assert r.status_code == 200
    assert r.json() == []


def test_kurs_dzial_temat_blok(client, nauczyciel):
    temat_id = _utworz_temat(client, nauczyciel)
    r = client.post(f"/tematy/{temat_id}/bloki", json={"typ": "teoria", "tresc": "Treść"}, headers=nauczyciel)
    assert r.status_code == 200
    temat = client.get(f"/tematy/{temat_id}", headers=nauczyciel).json()
    assert [b["tresc"] for b in temat["bloki"]] == ["Treść"]


def test_reorder_kursow_jeden_endpoint(client, nauczyciel):
    a = client.post("/kursy", json={"nazwa": "A", "opis": ""}, headers=nauczyciel).json()
    b = client.post("/kursy", json={"nazwa": "B", "opis": ""}, headers=nauczyciel).json()

    r = client.put("/kursy/reorder", json={"ids": [b["id"], a["id"]]}, headers=nauczyciel)
    assert r.status_code == 200
    assert [k["nazwa"] for k in client.get("/kursy", headers=nauczyciel).json()] == ["B", "A"]

    # Duplicate path was removed
    r = client.put("/reorder/kursy", json={"ids": [a["id"], b["id"]]}, headers=nauczyciel)
    assert r.status_code in (404, 405)


def test_generator_bez_klucza_zwraca_503(client, nauczyciel, monkeypatch):
    temat_id = _utworz_temat(client, nauczyciel)
    monkeypatch.setattr(ai_generator, "_api_key", None)
    r = client.put(f"/tematy/{temat_id}/generuj-bloki", headers=nauczyciel)
    assert r.status_code == 503


def test_blad_ai_nie_wycieka_do_klienta(client, nauczyciel, monkeypatch):
    temat_id = _utworz_temat(client, nauczyciel)

    def _awaria(*_args):
        raise RuntimeError("sekretny-szczegol-wyjatku")

    monkeypatch.setattr(ai_generator, "generuj_materialy_ai", _awaria)
    r = client.put(f"/tematy/{temat_id}/generuj-bloki", headers=nauczyciel)
    assert r.status_code == 502
    assert "sekretny-szczegol-wyjatku" not in r.text


def test_generator_zapisuje_bloki(client, nauczyciel, monkeypatch):
    temat_id = _utworz_temat(client, nauczyciel)
    bloki = [
        {"typ": "teoria", "tresc": "T", "odpowiedz": None, "rozwiazanie": None},
        {"typ": "zadanie", "tresc": "Z", "odpowiedz": "4", "rozwiazanie": "2+2"},
    ]
    monkeypatch.setattr(ai_generator, "generuj_materialy_ai", lambda *_: bloki)
    r = client.put(f"/tematy/{temat_id}/generuj-bloki", headers=nauczyciel)
    assert r.status_code == 200
    assert [b["typ"] for b in r.json()["bloki"]] == ["teoria", "zadanie"]
