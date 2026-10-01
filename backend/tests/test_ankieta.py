import pytest

from app import models
from app.seed import seed, seed_ankieta
from app.seed_ankieta import PYTANIA_VAK

PYTANIE = {
    "tresc": "Jak się uczysz?",
    "odpowiedzi": [
        {"tresc": "Patrzę", "styl": "V"},
        {"tresc": "Słucham", "styl": "A"},
        {"tresc": "Działam", "styl": "K"},
    ],
}


@pytest.fixture
def ankieta(db):
    """Seeds the 20 VAK questions; returns {pytanie_id: {styl: odpowiedz_id}}."""
    seed_ankieta(db)
    db.commit()
    return {
        p.id: {o.styl: o.id for o in p.odpowiedzi}
        for p in db.query(models.PytanieAnkiety).order_by(models.PytanieAnkiety.kolejnosc)
    }


@pytest.fixture
def nowy_uczen(utworz_uzytkownika):
    """Student right after registration — survey not filled in."""
    return utworz_uzytkownika("uczen")


def _odpowiedzi(ankieta, style: str):
    """Builds a submission; `style` is one letter per question, e.g. 'V' * 12 + 'A' * 5 + 'K' * 3."""
    assert len(style) == len(ankieta)
    return {
        "odpowiedzi": [
            {"pytanie_id": pid, "odpowiedz_id": mapa[styl]} for (pid, mapa), styl in zip(ankieta.items(), style)
        ]
    }


# --- seed ---


def test_seed_ma_20_pytan_po_jednej_odpowiedzi_na_styl(ankieta, db):
    assert len(PYTANIA_VAK) == 20
    assert len(ankieta) == 20
    assert all(set(mapa) == {"V", "A", "K"} for mapa in ankieta.values())
    # Answer order is rotated, so V is not always the first option
    pierwsze = {p.odpowiedzi[0].styl for p in db.query(models.PytanieAnkiety)}
    assert pierwsze == {"V", "A", "K"}


def test_seed_ankiety_jest_idempotentny(db):
    seed(db)
    db.commit()
    seed(db)
    db.commit()
    assert db.query(models.PytanieAnkiety).count() == 20
    assert db.query(models.OdpowiedzAnkiety).count() == 60


# --- reading questions ---


def test_pytania_wymagaja_logowania(client, ankieta):
    assert client.get("/ankieta/pytania").status_code == 401


def test_pytania_nie_zdradzaja_stylu_odpowiedzi(client, ankieta, nowy_uczen):
    r = client.get("/ankieta/pytania", headers=nowy_uczen[1])
    assert r.status_code == 200
    pytania = r.json()
    assert len(pytania) == 20
    assert all(len(p["odpowiedzi"]) == 3 for p in pytania)
    assert all(set(o) == {"id", "tresc"} for p in pytania for o in p["odpowiedzi"])


# --- flag and backend enforcement ---


def test_nowy_uczen_ma_flage_false(client, nowy_uczen):
    me = client.get("/auth/me", headers=nowy_uczen[1]).json()
    assert me["ankieta_wypelniona"] is False
    assert me["styl_uczenia"] is None


def test_materialy_bez_ankiety_zwracaja_403_z_kodem(client, nowy_uczen, nauczyciel):
    kurs = client.post("/kursy", json={"nazwa": "K", "opis": "", "is_published": True}, headers=nauczyciel).json()
    for sciezka in ("/kursy", f"/kursy/{kurs['id']}", "/dzialy/1", "/tematy/1", "/szukaj"):
        r = client.get(sciezka, headers=nowy_uczen[1])
        assert r.status_code == 403, sciezka
        assert r.json()["detail"]["kod"] == "ANKIETA_WYMAGANA", sciezka


def test_ankieta_i_profil_dostepne_bez_wypelnionej_ankiety(client, ankieta, nowy_uczen):
    h = nowy_uczen[1]
    assert client.get("/ankieta/pytania", headers=h).status_code == 200
    assert client.get("/profil", headers=h).status_code == 200
    assert client.get("/auth/me", headers=h).status_code == 200


def test_nauczyciel_i_admin_nie_musza_wypelniac_ankiety(client, nauczyciel, admin):
    assert client.get("/kursy", headers=nauczyciel).status_code == 200
    assert client.get("/kursy", headers=admin).status_code == 200


def test_flaga_wykrywana_przy_kazdym_logowaniu(client, ankieta, utworz_uzytkownika):
    from .conftest import HASLO

    utworz_uzytkownika("uczen", email="przerwal@test.pl")
    for _ in range(2):
        r = client.post("/auth/logowanie", json={"email": "przerwal@test.pl", "haslo": HASLO})
        assert r.json()["uzytkownik"]["ankieta_wypelniona"] is False
        token = {"Authorization": f"Bearer {r.json()['access_token']}"}
        assert client.get("/kursy", headers=token).status_code == 403


# --- submitting the survey ---


def test_wyslanie_ankiety_liczy_punkty_i_ustawia_flage(client, db, ankieta, nowy_uczen):
    user_id, h = nowy_uczen
    r = client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "V" * 12 + "A" * 5 + "K" * 3), headers=h)
    assert r.status_code == 200
    body = r.json()
    wynik = body["wynik_ankiety"]
    assert (wynik["punkty_v"], wynik["punkty_a"], wynik["punkty_k"]) == (12, 5, 3)
    assert wynik["styl_dominujacy"] == "V"
    assert body["uzytkownik"]["ankieta_wypelniona"] is True
    assert body["uzytkownik"]["styl_uczenia"] == "V"
    assert body["uzytkownik"]["styl_zrodlo"] == "ankieta"

    # Materials are unlocked now
    assert client.get("/kursy", headers=h).status_code == 200
    assert db.query(models.WynikAnkiety).filter_by(user_id=user_id).count() == 1


def test_remis_daje_styl_mieszany(client, ankieta, nowy_uczen):
    r = client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "V" * 8 + "A" * 8 + "K" * 4), headers=nowy_uczen[1])
    assert r.json()["uzytkownik"]["styl_uczenia"] == "VA"


def test_niepelna_ankieta_jest_odrzucana_i_nie_ustawia_flagi(client, ankieta, nowy_uczen):
    h = nowy_uczen[1]
    dane = _odpowiedzi(ankieta, "V" * 20)
    dane["odpowiedzi"].pop()
    r = client.post("/ankieta/odpowiedzi", json=dane, headers=h)
    assert r.status_code == 400
    assert client.get("/auth/me", headers=h).json()["ankieta_wypelniona"] is False
    assert client.get("/kursy", headers=h).status_code == 403
    assert client.get("/ankieta/wynik", headers=h).status_code == 404


def test_odpowiedz_z_innego_pytania_jest_odrzucana(client, ankieta, nowy_uczen):
    dane = _odpowiedzi(ankieta, "V" * 20)
    dane["odpowiedzi"][0]["odpowiedz_id"] = dane["odpowiedzi"][1]["odpowiedz_id"]
    assert client.post("/ankieta/odpowiedzi", json=dane, headers=nowy_uczen[1]).status_code == 400


def test_podwojna_odpowiedz_na_pytanie_jest_odrzucana(client, ankieta, nowy_uczen):
    dane = _odpowiedzi(ankieta, "V" * 20)
    dane["odpowiedzi"].append(dane["odpowiedzi"][0])
    assert client.post("/ankieta/odpowiedzi", json=dane, headers=nowy_uczen[1]).status_code == 400


def test_pusta_ankieta_w_bazie(client, nowy_uczen):
    r = client.post(
        "/ankieta/odpowiedzi", json={"odpowiedzi": [{"pytanie_id": 1, "odpowiedz_id": 1}]}, headers=nowy_uczen[1]
    )
    assert r.status_code == 409


def test_nieaktywne_pytania_sa_pomijane(client, db, ankieta, nowy_uczen):
    pierwsze_id = next(iter(ankieta))
    db.get(models.PytanieAnkiety, pierwsze_id).aktywne = False
    db.commit()
    h = nowy_uczen[1]
    assert len(client.get("/ankieta/pytania", headers=h).json()) == 19

    aktywne = {pid: mapa for pid, mapa in ankieta.items() if pid != pierwsze_id}
    r = client.post("/ankieta/odpowiedzi", json=_odpowiedzi(aktywne, "K" * 19), headers=h)
    assert r.status_code == 200
    assert r.json()["wynik_ankiety"]["punkty_k"] == 19


# --- retake and history ---


def test_powtorzenie_ankiety_nadpisuje_styl_i_zostawia_historie(client, ankieta, nowy_uczen):
    h = nowy_uczen[1]
    client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "V" * 20), headers=h)
    r = client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "A" * 15 + "K" * 5), headers=h)
    assert r.json()["uzytkownik"]["styl_uczenia"] == "A"

    historia = client.get("/ankieta/historia", headers=h).json()
    assert [w["styl_dominujacy"] for w in historia] == ["A", "V"]
    assert client.get("/ankieta/wynik", headers=h).json()["styl_dominujacy"] == "A"


def test_historia_jest_prywatna(client, ankieta, nowy_uczen, utworz_uzytkownika):
    client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "V" * 20), headers=nowy_uczen[1])
    _, inny = utworz_uzytkownika("uczen")
    assert client.get("/ankieta/historia", headers=inny).json() == []


# --- manual style ---


def test_reczna_zmiana_stylu_nie_kasuje_wyniku_ankiety(client, ankieta, nowy_uczen):
    h = nowy_uczen[1]
    client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "V" * 12 + "A" * 5 + "K" * 3), headers=h)

    r = client.put("/profil/styl", json={"styl": "A"}, headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["uzytkownik"]["styl_uczenia"] == "A"
    assert body["uzytkownik"]["styl_zrodlo"] == "reczny"
    # Survey result is still there: "Wynik ankiety: wzrokowiec · wybrany ręcznie: słuchowiec"
    assert body["wynik_ankiety"]["styl_dominujacy"] == "V"
    assert len(client.get("/ankieta/historia", headers=h).json()) == 1


def test_przywrocenie_stylu_z_ankiety(client, ankieta, nowy_uczen):
    h = nowy_uczen[1]
    client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "K" * 20), headers=h)
    client.put("/profil/styl", json={"styl": "V"}, headers=h)
    r = client.delete("/profil/styl", headers=h)
    assert r.status_code == 200
    assert r.json()["uzytkownik"]["styl_uczenia"] == "K"
    assert r.json()["uzytkownik"]["styl_zrodlo"] == "ankieta"


def test_nowa_ankieta_nadpisuje_reczny_wybor(client, ankieta, nowy_uczen):
    h = nowy_uczen[1]
    client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "V" * 20), headers=h)
    client.put("/profil/styl", json={"styl": "A"}, headers=h)
    r = client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "K" * 20), headers=h)
    assert r.json()["uzytkownik"]["styl_uczenia"] == "K"
    assert r.json()["uzytkownik"]["styl_zrodlo"] == "ankieta"


def test_reczny_styl_wymaga_ankiety_i_poprawnej_wartosci(client, ankieta, nowy_uczen):
    h = nowy_uczen[1]
    r = client.put("/profil/styl", json={"styl": "A"}, headers=h)
    assert r.status_code == 403
    assert r.json()["detail"]["kod"] == "ANKIETA_WYMAGANA"
    assert client.delete("/profil/styl", headers=h).status_code == 404

    client.post("/ankieta/odpowiedzi", json=_odpowiedzi(ankieta, "V" * 20), headers=h)
    assert client.put("/profil/styl", json={"styl": "X"}, headers=h).status_code == 422
    assert client.put("/profil/styl", json={"styl": "VA"}, headers=h).status_code == 422


# --- survey editor ---


def test_edycja_ankiety_tylko_dla_nauczyciela_i_admina(client, uczen, nauczyciel, admin):
    assert client.get("/ankieta/edycja/pytania").status_code == 401
    assert client.get("/ankieta/edycja/pytania", headers=uczen).status_code == 403
    assert client.post("/ankieta/edycja/pytania", json=PYTANIE, headers=uczen).status_code == 403
    assert client.put("/ankieta/edycja/pytania/1", json=PYTANIE, headers=uczen).status_code == 403
    assert client.delete("/ankieta/edycja/pytania/1", headers=uczen).status_code == 403
    assert client.get("/ankieta/edycja/pytania", headers=nauczyciel).status_code == 200
    assert client.get("/ankieta/edycja/pytania", headers=admin).status_code == 200


def test_nauczyciel_tworzy_edytuje_i_usuwa_pytanie(client, nauczyciel):
    r = client.post("/ankieta/edycja/pytania", json=PYTANIE, headers=nauczyciel)
    assert r.status_code == 201
    pytanie = r.json()
    assert {o["styl"] for o in pytanie["odpowiedzi"]} == {"V", "A", "K"}

    zmiana = {**PYTANIE, "tresc": "Nowa treść", "aktywne": False}
    r = client.put(f"/ankieta/edycja/pytania/{pytanie['id']}", json=zmiana, headers=nauczyciel)
    assert r.status_code == 200
    assert r.json()["tresc"] == "Nowa treść"
    assert r.json()["aktywne"] is False
    assert len(r.json()["odpowiedzi"]) == 3

    assert client.delete(f"/ankieta/edycja/pytania/{pytanie['id']}", headers=nauczyciel).status_code == 200
    assert client.get("/ankieta/edycja/pytania", headers=nauczyciel).json() == []
    assert client.delete(f"/ankieta/edycja/pytania/{pytanie['id']}", headers=nauczyciel).status_code == 404


@pytest.mark.parametrize(
    "odpowiedzi",
    [
        PYTANIE["odpowiedzi"][:2],
        PYTANIE["odpowiedzi"] + [{"tresc": "Drugie V", "styl": "V"}],
        [{"tresc": "a", "styl": "V"}, {"tresc": "b", "styl": "V"}, {"tresc": "c", "styl": "A"}],
        [{"tresc": "  ", "styl": "V"}, {"tresc": "b", "styl": "A"}, {"tresc": "c", "styl": "K"}],
    ],
)
def test_pytanie_musi_miec_po_jednej_odpowiedzi_na_styl(client, nauczyciel, odpowiedzi):
    r = client.post("/ankieta/edycja/pytania", json={"tresc": "Pytanie", "odpowiedzi": odpowiedzi}, headers=nauczyciel)
    assert r.status_code == 422
