from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import models
from app.security import JWT_ALGORITHM, JWT_SECRET, dekoduj_token, hash_haslo, sprawdz_haslo
from app.seed import HASLO_UCZNIA_DEMO, KONTA_TESTOWE, UCZNIOWIE_DEMO, seed

from .conftest import HASLO

REJESTRACJA = {"email": "Nowy@Test.pl", "imie": "Nowy", "haslo": "BardzoTajne1"}


# --- passwords and tokens ---


def test_haslo_jest_hashowane_bcryptem():
    h = hash_haslo("tajne-haslo")
    assert h != "tajne-haslo"
    assert h.startswith("$2")
    assert sprawdz_haslo("tajne-haslo", h)
    assert not sprawdz_haslo("inne-haslo", h)


def test_sprawdz_haslo_przy_uszkodzonym_hashu():
    assert sprawdz_haslo("cokolwiek", "to-nie-jest-hash") is False


def test_dekoduj_token_odrzuca_smieci():
    assert dekoduj_token("to.nie.token") is None


# --- registration ---


def test_rejestracja_tworzy_ucznia_i_zwraca_token(client, db):
    r = client.post("/auth/rejestracja", json=REJESTRACJA)
    assert r.status_code == 201
    body = r.json()
    assert body["uzytkownik"]["email"] == "nowy@test.pl"
    assert body["uzytkownik"]["rola"] == "uczen"
    assert body["uzytkownik"]["ankieta_wypelniona"] is False
    assert "haslo_hash" not in body["uzytkownik"]

    payload = dekoduj_token(body["access_token"])
    assert payload["rola"] == "uczen"
    assert payload["sub"] == str(body["uzytkownik"]["id"])

    user = db.query(models.Uzytkownik).filter_by(email="nowy@test.pl").one()
    assert user.haslo_hash != REJESTRACJA["haslo"]


def test_rejestracja_nie_pozwala_wybrac_roli(client):
    r = client.post("/auth/rejestracja", json={**REJESTRACJA, "rola": "admin"})
    assert r.status_code == 201
    assert r.json()["uzytkownik"]["rola"] == "uczen"


def test_rejestracja_duplikat_emaila(client):
    assert client.post("/auth/rejestracja", json=REJESTRACJA).status_code == 201
    r = client.post("/auth/rejestracja", json={**REJESTRACJA, "email": "NOWY@test.pl"})
    assert r.status_code == 409


@pytest.mark.parametrize(
    "poprawka",
    [{"email": "bez-malpy"}, {"haslo": "krotkie"}, {"imie": "   "}, {"haslo": "x" * 73}],
)
def test_rejestracja_walidacja(client, poprawka):
    r = client.post("/auth/rejestracja", json={**REJESTRACJA, **poprawka})
    assert r.status_code == 422


# --- login ---


def test_logowanie_poprawne(client, utworz_uzytkownika):
    utworz_uzytkownika("nauczyciel", email="n@test.pl")
    r = client.post("/auth/logowanie", json={"email": " N@test.pl ", "haslo": HASLO})
    assert r.status_code == 200
    assert r.json()["uzytkownik"]["rola"] == "nauczyciel"
    assert dekoduj_token(r.json()["access_token"])["rola"] == "nauczyciel"


def test_logowanie_zle_haslo_i_nieznany_email_daja_ten_sam_blad(client, utworz_uzytkownika):
    utworz_uzytkownika("uczen", email="u@test.pl")
    zle_haslo = client.post("/auth/logowanie", json={"email": "u@test.pl", "haslo": "zle-haslo"})
    nieznany = client.post("/auth/logowanie", json={"email": "nikt@test.pl", "haslo": HASLO})
    assert zle_haslo.status_code == nieznany.status_code == 401
    assert zle_haslo.json() == nieznany.json()


def test_logowanie_nieaktywnego_konta(client, utworz_uzytkownika):
    utworz_uzytkownika("uczen", email="off@test.pl", aktywny=False)
    r = client.post("/auth/logowanie", json={"email": "off@test.pl", "haslo": HASLO})
    assert r.status_code == 401


# --- token handling ---


def test_me_wymaga_tokenu(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer smieci"}).status_code == 401


def test_me_zwraca_uzytkownika(client, nauczyciel):
    r = client.get("/auth/me", headers=nauczyciel)
    assert r.status_code == 200
    assert r.json()["rola"] == "nauczyciel"


def test_wygasly_token_jest_odrzucany(client, utworz_uzytkownika):
    user_id, _ = utworz_uzytkownika("uczen")
    token = jwt.encode(
        {"sub": str(user_id), "rola": "uczen", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_token_podpisany_innym_sekretem_jest_odrzucany(client, utworz_uzytkownika):
    user_id, _ = utworz_uzytkownika("admin")
    token = jwt.encode(
        {"sub": str(user_id), "rola": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "inny-sekret-inny-sekret-inny-sekret-inny",
        algorithm=JWT_ALGORITHM,
    )
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_rola_w_tokenie_nie_wystarcza_liczy_sie_baza(client, utworz_uzytkownika):
    # Token claims "admin", but the account in the DB is a student
    user_id, _ = utworz_uzytkownika("uczen")
    token = jwt.encode(
        {"sub": str(user_id), "rola": "admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )
    assert client.get("/uzytkownicy", headers={"Authorization": f"Bearer {token}"}).status_code == 403


# --- permissions: courses ---


def test_tresci_wymagaja_logowania(client):
    for sciezka in ("/kursy", "/kursy/1", "/dzialy/1", "/tematy/1", "/szukaj"):
        assert client.get(sciezka).status_code == 401, sciezka


def test_uczen_nie_moze_edytowac(client, uczen, nauczyciel):
    kurs = client.post("/kursy", json={"nazwa": "K", "opis": "", "is_published": True}, headers=nauczyciel).json()
    assert client.post("/kursy", json={"nazwa": "X", "opis": ""}, headers=uczen).status_code == 403
    assert client.put(f"/kursy/{kurs['id']}", json={"nazwa": "Y"}, headers=uczen).status_code == 403
    assert client.delete(f"/kursy/{kurs['id']}", headers=uczen).status_code == 403
    assert client.put("/kursy/reorder", json={"ids": [kurs["id"]]}, headers=uczen).status_code == 403
    assert client.post(f"/kursy/{kurs['id']}/dzialy", json={"nazwa": "D"}, headers=uczen).status_code == 403
    assert client.put("/tematy/1/generuj-bloki", headers=uczen).status_code == 403


def test_edycja_bez_tokenu_to_401(client):
    assert client.post("/kursy", json={"nazwa": "X", "opis": ""}).status_code == 401
    assert client.delete("/bloki/1").status_code == 401


def test_nauczyciel_i_admin_moga_edytowac(client, nauczyciel, admin):
    assert client.post("/kursy", json={"nazwa": "N", "opis": ""}, headers=nauczyciel).status_code == 200
    assert client.post("/kursy", json={"nazwa": "A", "opis": ""}, headers=admin).status_code == 200


def test_uczen_widzi_tylko_opublikowane_kursy(client, uczen, nauczyciel):
    jawny = client.post("/kursy", json={"nazwa": "Jawny", "opis": "", "is_published": True}, headers=nauczyciel).json()
    ukryty = client.post("/kursy", json={"nazwa": "Ukryty", "opis": ""}, headers=nauczyciel).json()
    dzial = client.post(f"/kursy/{ukryty['id']}/dzialy", json={"nazwa": "Tajny dział"}, headers=nauczyciel).json()
    temat = client.post(f"/dzialy/{dzial['id']}/tematy", json={"tytul": "Tajny temat"}, headers=nauczyciel).json()

    assert [k["nazwa"] for k in client.get("/kursy", headers=uczen).json()] == ["Jawny"]
    assert client.get(f"/kursy/{jawny['id']}", headers=uczen).status_code == 200
    assert client.get(f"/kursy/{ukryty['id']}", headers=uczen).status_code == 404
    assert client.get(f"/dzialy/{dzial['id']}", headers=uczen).status_code == 404
    assert client.get(f"/tematy/{temat['id']}", headers=uczen).status_code == 404
    assert client.get("/szukaj?q=Tajny", headers=uczen).json() == {"dzialy": [], "tematy": []}

    # Teacher sees everything
    assert len(client.get("/kursy", headers=nauczyciel).json()) == 2
    assert client.get(f"/tematy/{temat['id']}", headers=nauczyciel).status_code == 200
    assert len(client.get("/szukaj?q=Tajny", headers=nauczyciel).json()["tematy"]) == 1


# --- permissions: user management ---


def test_lista_uzytkownikow_tylko_dla_admina(client, admin, nauczyciel, uczen):
    assert client.get("/uzytkownicy").status_code == 401
    assert client.get("/uzytkownicy", headers=uczen).status_code == 403
    assert client.get("/uzytkownicy", headers=nauczyciel).status_code == 403
    r = client.get("/uzytkownicy", headers=admin)
    assert r.status_code == 200
    assert {u["rola"] for u in r.json()} == {"admin", "nauczyciel", "uczen"}
    assert all("haslo_hash" not in u for u in r.json())


def test_admin_zmienia_role(client, admin, utworz_uzytkownika):
    user_id, naglowki = utworz_uzytkownika("uczen")
    assert client.post("/kursy", json={"nazwa": "X", "opis": ""}, headers=naglowki).status_code == 403

    r = client.put(f"/uzytkownicy/{user_id}/rola", json={"rola": "nauczyciel"}, headers=admin)
    assert r.status_code == 200
    assert r.json()["rola"] == "nauczyciel"

    # Old token keeps working and the new role applies immediately
    assert client.post("/kursy", json={"nazwa": "X", "opis": ""}, headers=naglowki).status_code == 200


def test_zmiana_roli_walidacja_i_uprawnienia(client, admin, nauczyciel, utworz_uzytkownika):
    user_id, _ = utworz_uzytkownika("uczen")
    assert client.put(f"/uzytkownicy/{user_id}/rola", json={"rola": "superadmin"}, headers=admin).status_code == 422
    assert client.put(f"/uzytkownicy/{user_id}/rola", json={"rola": "admin"}, headers=nauczyciel).status_code == 403
    assert client.put("/uzytkownicy/999999/rola", json={"rola": "admin"}, headers=admin).status_code == 404


def test_admin_nie_moze_zmienic_wlasnej_roli(client, utworz_uzytkownika):
    admin_id, naglowki = utworz_uzytkownika("admin")
    r = client.put(f"/uzytkownicy/{admin_id}/rola", json={"rola": "uczen"}, headers=naglowki)
    assert r.status_code == 400


# --- seed ---


def test_seed_tworzy_konta_testowe_i_jest_idempotentny(client, db):
    seed(db)
    db.commit()
    seed(db)
    db.commit()
    assert db.query(models.Uzytkownik).count() == len(KONTA_TESTOWE) + len(UCZNIOWIE_DEMO)
    assert {u.rola for u in db.query(models.Uzytkownik)} == {"admin", "nauczyciel", "uczen"}

    for konto in KONTA_TESTOWE:
        r = client.post("/auth/logowanie", json={"email": konto["email"], "haslo": konto["haslo"]})
        assert r.status_code == 200, konto["email"]
        assert r.json()["uzytkownik"]["rola"] == konto["rola"]


def test_seed_uczniowie_demo_po_jednym_na_styl(client, db):
    seed(db)
    db.commit()
    style = []
    for konto in UCZNIOWIE_DEMO:
        r = client.post("/auth/logowanie", json={"email": konto["email"], "haslo": HASLO_UCZNIA_DEMO})
        assert r.status_code == 200, konto["email"]
        u = r.json()["uzytkownik"]
        assert u["ankieta_wypelniona"] is True and u["styl_zrodlo"] == "ankieta"
        style.append(u["styl_uczenia"])
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        sciezka = client.get("/nauka/sciezka", headers=h).json()
        assert tuple(sciezka["wagi"][s] for s in "VAK") == konto["punkty"]
        assert sciezka["styl_ankiety"] == u["styl_uczenia"]
    assert style == ["V", "A", "K"]
    # The plain test student still has to fill in the survey
    r = client.post("/auth/logowanie", json={"email": "uczen@stylnauki.pl", "haslo": "Uczen123!"})
    assert r.json()["uzytkownik"]["ankieta_wypelniona"] is False
