from app.services import ai_generator


def _utworz_temat(client) -> int:
    kurs = client.post("/kursy", json={"nazwa": "Kurs testowy", "opis": "Opis"}).json()
    dzial = client.post(f"/kursy/{kurs['id']}/dzialy", json={"nazwa": "Dział"}).json()
    temat = client.post(f"/dzialy/{dzial['id']}/tematy", json={"tytul": "Temat"}).json()
    return temat["id"]


def test_serwer_dziala(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"] == "success"


def test_pusta_baza_zwraca_pusta_liste_kursow(client):
    r = client.get("/kursy")
    assert r.status_code == 200
    assert r.json() == []


def test_kurs_dzial_temat_blok(client):
    temat_id = _utworz_temat(client)
    r = client.post(f"/tematy/{temat_id}/bloki", json={"typ": "teoria", "tresc": "Treść"})
    assert r.status_code == 200
    temat = client.get(f"/tematy/{temat_id}").json()
    assert [b["tresc"] for b in temat["bloki"]] == ["Treść"]


def test_reorder_kursow_jeden_endpoint(client):
    a = client.post("/kursy", json={"nazwa": "A", "opis": ""}).json()
    b = client.post("/kursy", json={"nazwa": "B", "opis": ""}).json()

    r = client.put("/kursy/reorder", json={"ids": [b["id"], a["id"]]})
    assert r.status_code == 200
    assert [k["nazwa"] for k in client.get("/kursy").json()] == ["B", "A"]

    # Duplicate path was removed
    assert client.put("/reorder/kursy", json={"ids": [a["id"], b["id"]]}).status_code in (404, 405)


def test_generator_bez_klucza_zwraca_503(client, monkeypatch):
    temat_id = _utworz_temat(client)
    monkeypatch.setattr(ai_generator, "_api_key", None)
    r = client.put(f"/tematy/{temat_id}/generuj-bloki")
    assert r.status_code == 503


def test_blad_ai_nie_wycieka_do_klienta(client, monkeypatch):
    temat_id = _utworz_temat(client)

    def _awaria(*_args):
        raise RuntimeError("sekretny-szczegol-wyjatku")

    monkeypatch.setattr(ai_generator, "generuj_materialy_ai", _awaria)
    r = client.put(f"/tematy/{temat_id}/generuj-bloki")
    assert r.status_code == 502
    assert "sekretny-szczegol-wyjatku" not in r.text


def test_generator_zapisuje_bloki(client, monkeypatch):
    temat_id = _utworz_temat(client)
    bloki = [
        {"typ": "teoria", "tresc": "T", "odpowiedz": None, "rozwiazanie": None},
        {"typ": "zadanie", "tresc": "Z", "odpowiedz": "4", "rozwiazanie": "2+2"},
    ]
    monkeypatch.setattr(ai_generator, "generuj_materialy_ai", lambda *_: bloki)
    r = client.put(f"/tematy/{temat_id}/generuj-bloki")
    assert r.status_code == 200
    assert [b["typ"] for b in r.json()["bloki"]] == ["teoria", "zadanie"]
