# Etap 2 – ankieta VAK + flaga + wymuszenie po logowaniu   (01.10.2026)

## Plan (krótko)
1. Backend: tabele ankiety, czysta funkcja liczenia wyniku, endpointy ankiety i profilu, blokada materiałów bez ankiety (403 `ANKIETA_WYMAGANA`), edycja pytań dla nauczyciela, seed 20 pytań.
2. Frontend: strona ankiety (wymuszana flagą przy każdym wejściu), strona wyniku, profil z ręczną zmianą stylu.
3. Testy: liczenie VAK (czysta funkcja), flaga, wymuszenie, ręczny styl, edycja pytań.

## Co zrobione (lista, z plikami)
**Backend**
- `app/models.py` – `PytanieAnkiety`, `OdpowiedzAnkiety` (treść + styl), `WynikAnkiety` (punkty V/A/K, styl dominujący, data); migracja `alembic/versions/0003_ankieta_vak.py`.
- `app/services/vak.py` – czyste funkcje: `policz_wynik`, `style_dominujace`, `poprawny_styl`.
- `app/routers/ankieta.py`:
  - `GET /ankieta/pytania` (bez stylu odpowiedzi), `POST /ankieta/odpowiedzi`, `GET /ankieta/wynik`, `GET /ankieta/historia`;
  - `GET /profil`, `PUT /profil/styl` (ręczny wybór V/A/K), `DELETE /profil/styl` (powrót do wyniku ankiety);
  - edycja pytań (nauczyciel/admin): `GET/POST /ankieta/edycja/pytania`, `PUT/DELETE /ankieta/edycja/pytania/{id}`.
- `app/deps.py` – `get_uczestnik`: uczeń bez ankiety dostaje 403 z `detail.kod = "ANKIETA_WYMAGANA"`; podpięte pod wszystkie endpointy materiałów (`/kursy`, `/kursy/{id}`, `/dzialy/{id}`, `/tematy/{id}`, `/szukaj`).
- `app/seed_ankieta.py` + `app/seed.py` – 20 pytań VAK, po jednej odpowiedzi na styl, z rotacją kolejności odpowiedzi.

**Frontend**
- `src/app/ankieta/page.tsx` – ankieta pytanie po pytaniu z paskiem postępu; `src/app/ankieta/wynik/page.tsx` – „Jesteś: wzrokowiec", `V 12 / A 5 / K 3`, słupki.
- `src/app/profil/page.tsx` – „Mój styl uczenia": „Wynik ankiety: … · wybrany ręcznie: …", wybór V/A/K, powrót do wyniku ankiety, ponowne wypełnienie, historia.
- `src/components/ankieta/WynikVak.tsx`, `src/lib/labels.ts` (nazwy, opisy i kolory stylów).
- `src/components/auth/AuthGate.tsx` – uczeń z `ankieta_wypelniona = false` jest przekierowywany na `/ankieta` z każdej strony; `src/lib/api.ts` – odpowiedź 403 `ANKIETA_WYMAGANA` cofa flagę w sesji (drugi bezpiecznik).

**Testy**: `tests/test_vak.py` (27 przypadków), `tests/test_ankieta.py` (27 przypadków).

## Decyzje i dlaczego
- **Remis → styl mieszany zapisany jako litery w kolejności V, A, K** (np. `VA`, `VAK`). Uczeń o stylu `VA` zobaczy bloki V i A (Etap 3). Ręcznie można wybrać tylko pojedynczy styl.
- **Każde pytanie ma dokładnie 3 odpowiedzi – po jednej na styl** (walidacja w edytorze). Dzięki temu każda ankieta daje porównywalne punkty.
- **Styl odpowiedzi nigdy nie trafia do ucznia** – schemat odpowiedzi API nie ma pola `styl`, a kolejność odpowiedzi jest rotowana w seedzie.
- **Nowa ankieta zawsze nadpisuje styl (także ręczny)**, historia wyników zostaje – zgodnie z wymaganiem.
- **Ręczna zmiana wymaga wypełnionej ankiety**; nie tworzy nowego wyniku i nie kasuje starego. Dodatkowo `DELETE /profil/styl` przywraca styl z ostatniej ankiety.
- **Ankietę wypełnia się w całości** – niepełne zgłoszenie jest odrzucane (400) i flaga zostaje `false`, więc przerwana ankieta wraca przy następnym logowaniu.
- **Pytania nieaktywne** są pomijane – nauczyciel może wyłączyć pytanie bez usuwania.
- Seed pytań tylko do pustej ankiety – nie nadpisuje zmian nauczyciela.

## Weryfikacja (komendy + wynik)
- `pytest` → 89 passed
- `npm run lint` → 0 błędów (3 ostrzeżenia `<img>`)
- `npm run build` → OK
- Smoke w przeglądarce headless: rejestracja → `/ankieta`; wejście na `/kursy` wraca na ankietę; przerwanie ankiety i ponowne logowanie → znów ankieta; wypełnienie 20 pytań → wynik (suma punktów 20) → `/kursy` odblokowane; profil: ręczna zmiana stylu pokazuje „Wynik ankiety: … · wybrany ręcznie: …", przetrwa odświeżenie, powrót do wyniku ankiety działa. Wynik: OK, brak błędów w konsoli.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. `alembic upgrade head`, `python -m app.seed` (doda 20 pytań), uruchom backend i frontend.
2. Zarejestruj nowe konto → automatycznie ankieta. Spróbuj wejść na `/kursy` → powrót na ankietę.
3. Wyloguj się w połowie, zaloguj ponownie → znów ankieta.
4. Wypełnij ankietę → strona wyniku z punktami V/A/K.
5. Kliknij swoje imię w pasku → profil → zmień styl ręcznie → widać obie informacje; „Wróć do wyniku ankiety".
6. API: `GET /kursy` tokenem ucznia bez ankiety → 403 `{"detail": {"kod": "ANKIETA_WYMAGANA", ...}}`.

## Znane problemy / TODO
- Edycja pytań ankiety ma tylko API – UI dla nauczyciela w Etapie 5.
- Odpowiedzi w trakcie wypełniania nie są zapisywane (odświeżenie strony zaczyna ankietę od nowa) – zgodne z wymaganiem „nie dokończył → wraca na ankietę".
- `TODO(prowadzący)`: czy pytania VAK mają pochodzić z konkretnego, uznanego kwestionariusza – obecne są autorskie.

## Propozycje (poza zakresem)
- Zapisywanie pojedynczych odpowiedzi ucznia (dziś zapisujemy tylko sumy punktów) – przydatne do analizy pytań.
- Wznawianie przerwanej ankiety od ostatniego pytania.

## Commity (hash + opis)
- 706eb56 Backend: ankieta VAK (pytania, wynik, flaga, ręczny styl, edycja pytań) i seed 20 pytań
- 13deb50 Backend: testy liczenia VAK, flagi ankiety i ręcznej zmiany stylu
- bab91dd Frontend: ankieta VAK, wynik, profil ze zmianą stylu
