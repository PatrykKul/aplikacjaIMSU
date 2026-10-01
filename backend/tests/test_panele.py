"""Panel nauczyciela (lista uczniów, szczegóły) i panel admina (blokowanie kont)."""
from app import models

from .conftest import HASLO
from .test_nauka import _quiz, kurs  # noqa: F401  (fixture reuse)


def _uczen(utworz_uzytkownika, **pola):
    domyslne = dict(ankieta_wypelniona=True, styl_uczenia="V", styl_zrodlo="ankieta", waga_v=8, waga_a=7, waga_k=5)
    domyslne.update(pola)
    return utworz_uzytkownika("uczen", **domyslne)


# --- teacher: student list ---


def test_lista_uczniow_tylko_dla_nauczyciela_i_admina(client, uczen, nauczyciel, admin):
    assert client.get("/nauczyciel/uczniowie").status_code == 401
    assert client.get("/nauczyciel/uczniowie", headers=uczen).status_code == 403
    assert client.get("/nauczyciel/uczniowie", headers=nauczyciel).status_code == 200
    assert client.get("/nauczyciel/uczniowie", headers=admin).status_code == 200


def test_lista_uczniow_pokazuje_styl_z_ankiety_i_reczny(client, db, utworz_uzytkownika, nauczyciel, admin):
    user_id, h = _uczen(utworz_uzytkownika, email="ola@test.pl")
    db.add(models.WynikAnkiety(user_id=user_id, punkty_v=12, punkty_a=5, punkty_k=3, styl_dominujacy="V"))
    db.commit()
    client.put("/profil/styl", json={"styl": "A"}, headers=h)
    utworz_uzytkownika("uczen", email="nowy@test.pl")  # registered, no survey yet

    lista = client.get("/nauczyciel/uczniowie", headers=nauczyciel).json()
    # Only students are listed (the teacher and admin fixtures are not)
    assert {u["email"] for u in lista} == {"ola@test.pl", "nowy@test.pl"}
    ola = next(u for u in lista if u["email"] == "ola@test.pl")
    assert ola["styl_ankiety"] == "V"
    assert ola["styl_uczenia"] == "A"
    assert ola["styl_zrodlo"] == "reczny"
    assert ola["punkty_ankiety"] == {"V": 12, "A": 5, "K": 3}
    nowy = next(u for u in lista if u["email"] == "nowy@test.pl")
    assert nowy["ankieta_wypelniona"] is False
    assert nowy["styl_ankiety"] is None and nowy["punkty_ankiety"] is None
    assert all("haslo_hash" not in u for u in lista)


def test_lista_uczniow_postep(client, kurs, utworz_uzytkownika, nauczyciel):  # noqa: F811
    _, h = _uczen(utworz_uzytkownika)
    _quiz(client, h, kurs["quizy"][0], 100)
    _quiz(client, h, kurs["quizy"][1], 40)
    _quiz(client, h, kurs["quizy"][1], 50)
    u = client.get("/nauczyciel/uczniowie", headers=nauczyciel).json()[0]
    assert u["zaliczone_tematy"] == 1
    assert u["liczba_prob"] == 3
    assert u["wagi"] == {"V": 8, "A": 7, "K": 5}  # +1 for the pass, -1 for the first fail
    assert u["ostatnia_aktywnosc"] is not None


# --- teacher: student details ---


def test_szczegoly_ucznia_sciezka_i_zdarzenia(client, db, kurs, utworz_uzytkownika, nauczyciel):  # noqa: F811
    user_id, h = _uczen(utworz_uzytkownika)
    db.add(models.WynikAnkiety(user_id=user_id, punkty_v=8, punkty_a=7, punkty_k=5, styl_dominujacy="V"))
    db.commit()
    _quiz(client, h, kurs["quizy"][0], 40)
    client.post("/nauka/zdarzenia", json={"temat_id": kurs["tematy"][0], "typ": "odtworzenie_audio"}, headers=h)

    r = client.get(f"/nauczyciel/uczniowie/{user_id}", headers=nauczyciel)
    assert r.status_code == 200
    d = r.json()
    assert d["uczen"]["styl_ankiety"] == "V"
    assert d["sciezka"]["wagi"] == {"V": 7, "A": 7, "K": 5}
    assert d["sciezka"]["kursy"][0]["tematy"][0]["ostatni_wynik"] == 40
    assert "40%" in d["sciezka"]["nastepny_krok"]["dlaczego"]
    assert len(d["historia_ankiet"]) == 1
    assert [z["typ"] for z in d["zdarzenia"]] == ["odtworzenie_audio", "wynik_quizu"]
    assert d["zdarzenia"][1]["wartosc"] == 40 and d["zdarzenia"][1]["temat"] == "Pierwszy"


def test_szczegoly_ucznia_uprawnienia_i_404(client, utworz_uzytkownika, nauczyciel, uczen):
    user_id, h = _uczen(utworz_uzytkownika)
    nauczyciel_id, _ = utworz_uzytkownika("nauczyciel")
    assert client.get(f"/nauczyciel/uczniowie/{user_id}", headers=uczen).status_code == 403
    assert client.get(f"/nauczyciel/uczniowie/{user_id}", headers=h).status_code == 403
    assert client.get("/nauczyciel/uczniowie/999999", headers=nauczyciel).status_code == 404
    # Other teachers are not "students"
    assert client.get(f"/nauczyciel/uczniowie/{nauczyciel_id}", headers=nauczyciel).status_code == 404


# --- admin: block / unblock accounts ---


def test_admin_blokuje_i_odblokowuje_konto(client, admin, utworz_uzytkownika):
    user_id, h = utworz_uzytkownika("uczen", email="blok@test.pl")
    assert client.get("/auth/me", headers=h).status_code == 200

    r = client.put(f"/uzytkownicy/{user_id}/aktywny", json={"aktywny": False}, headers=admin)
    assert r.status_code == 200 and r.json()["aktywny"] is False
    # Existing token stops working and logging in is refused
    assert client.get("/auth/me", headers=h).status_code == 401
    assert client.post("/auth/logowanie", json={"email": "blok@test.pl", "haslo": HASLO}).status_code == 401

    r = client.put(f"/uzytkownicy/{user_id}/aktywny", json={"aktywny": True}, headers=admin)
    assert r.json()["aktywny"] is True
    assert client.get("/auth/me", headers=h).status_code == 200


def test_blokowanie_uprawnienia(client, nauczyciel, uczen, utworz_uzytkownika):
    user_id, _ = utworz_uzytkownika("uczen")
    admin_id, admin_h = utworz_uzytkownika("admin")
    assert client.put(f"/uzytkownicy/{user_id}/aktywny", json={"aktywny": False}, headers=nauczyciel).status_code == 403
    assert client.put(f"/uzytkownicy/{user_id}/aktywny", json={"aktywny": False}, headers=uczen).status_code == 403
    assert client.put(f"/uzytkownicy/{user_id}/aktywny", json={"aktywny": False}).status_code == 401
    assert client.put(f"/uzytkownicy/{admin_id}/aktywny", json={"aktywny": False}, headers=admin_h).status_code == 400
    assert client.put("/uzytkownicy/999999/aktywny", json={"aktywny": False}, headers=admin_h).status_code == 404
