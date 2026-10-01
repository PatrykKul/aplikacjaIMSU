# Etap 1 – auth + role + seed użytkowników   (01.10.2026)

## Plan (krótko)
1. Backend: tabela `uzytkownicy`, hasła bcrypt, JWT z rolą, zależności `get_current_user` / `wymagaj_roli`, ochrona endpointów kursów, zarządzanie rolami dla admina, seed 3 kont.
2. Frontend: logowanie, rejestracja, sesja w `localStorage`, bramka chroniąca strony, tryb edycji tylko dla nauczyciela/admina, wylogowanie.
3. Testy pytest: auth, uprawnienia, seed.

## Co zrobione (lista, z plikami)
**Backend**
- `app/models.py` – model `Uzytkownik` (email, imie, haslo_hash, rola, aktywny, ankieta_wypelniona, styl_uczenia, styl_zrodlo, utworzono); migracja `alembic/versions/0002_uzytkownicy.py`.
- `app/security.py` – `hash_haslo`, `sprawdz_haslo` (bcrypt), `utworz_token`, `dekoduj_token` (PyJWT, HS256, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`).
- `app/deps.py` – `get_db`, `get_current_user`, `wymagaj_roli`, `wymagaj_edytora`, `wymagaj_admina`.
- `app/routers/auth.py` – `POST /auth/rejestracja`, `POST /auth/logowanie`, `GET /auth/me`.
- `app/routers/uzytkownicy.py` – `GET /uzytkownicy`, `PUT /uzytkownicy/{id}/rola` (tylko admin).
- `app/routers/kursy.py` – odczyt wymaga logowania; zapis (POST/PUT/DELETE, upload, generator AI) tylko nauczyciel/admin; uczeń widzi wyłącznie opublikowane kursy (nieopublikowane → 404, także w wyszukiwarce).
- `app/seed.py` – idempotentny seed kont: admin, nauczyciel, uczeń.
- `app/schemas.py` – schematy auth z walidacją e-maila, imienia i hasła (8–72 znaki).

**Frontend**
- `src/store/useAuthStore.ts` – token + użytkownik (zustand persist).
- `src/lib/api.ts` – `authFetch` (nagłówek Authorization, 401 → wylogowanie), `ApiError`, `login`, `register`, `getMe`.
- `src/components/auth/AuthGate.tsx` – przekierowania: niezalogowany → `/logowanie`; `/admin/*` tylko admin; `/nauczyciel/*` nauczyciel/admin; uczeń bez ankiety → `/ankieta` (strona powstanie w Etapie 2).
- `src/components/auth/AuthForm.tsx`, `src/app/logowanie`, `src/app/rejestracja`, `src/components/UserMenu.tsx`.
- `src/components/Navbar.tsx` – „Tryb Edycji" widoczny tylko dla nauczyciela/admina; indeks wyszukiwarki pobierany po zalogowaniu.
- Strony kursów/działów/tematów pobierają dane po stronie klienta z tokenem (usunięty `lib/server-fetch.ts`).

**Testy**: `backend/tests/test_auth.py` (28 testów), `tests/conftest.py` (fabryka użytkowników), `tests/test_kursy.py` (dostosowane do auth).

## Decyzje i dlaczego
- **Uprawnienia sprawdzane po roli z bazy, nie z tokenu.** Token zawiera rolę (wymóg), ale zmiana roli przez admina działa natychmiast i podrobiona/stara rola w tokenie nic nie daje (jest na to test).
- **Rejestracja zawsze tworzy ucznia** – rolę nadaje admin; pole `rola` w żądaniu jest ignorowane.
- **Admin nie może zmienić własnej roli** – ochrona przed utratą ostatniego admina.
- **Jeden komunikat dla złego hasła i nieznanego e-maila** – nie ujawniamy, które konta istnieją.
- **Brak `JWT_SECRET` → losowy sekret na proces** (z ostrzeżeniem w logach) zamiast stałego domyślnego w kodzie; lokalny `.env` dostał wygenerowany sekret.
- **Token w `localStorage`, dane pobierane po stronie klienta** – najprostszy wariant bez ciasteczek i middleware; wystarczający dla projektu zaliczeniowego.
- **Walidacja e-maila prostym wyrażeniem regularnym** – bez dodatkowej zależności.
- Nieopublikowany kurs dla ucznia to 404 (nie 403), żeby nie zdradzać istnienia treści.

## Weryfikacja (komendy + wynik)
- `pytest` → 35 passed
- `npm run lint` → 0 błędów (3 ostrzeżenia `<img>`)
- `npm run build` → OK
- Smoke w przeglądarce headless (Edge przez playwright-core, skrypt poza repo): przekierowanie niezalogowanego na `/logowanie`, komunikat przy złym haśle, logowanie nauczyciela (przełącznik edycji widoczny), logowanie ucznia (brak przełącznika, brak wejścia na `/admin`), API: uczeń `POST /kursy` → 403, anonim → 401. Wynik: wszystkie kroki OK, brak błędów w konsoli.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. `cd backend && alembic upgrade head && python -m app.seed && uvicorn app.main:app --port 8000`; `cd frontend && npm run dev`.
2. Wejdź na http://localhost:3000/kursy bez logowania → przekierowanie na logowanie.
3. Zaloguj się jako `nauczyciel@stylnauki.pl` / `Nauczyciel123!` → widać „Tryb Edycji"; dodaj kurs i opublikuj go.
4. Wyloguj, zaloguj jako `uczen@stylnauki.pl` / `Uczen123!` → brak trybu edycji. Do Etapu 2 uczeń bez ankiety jest kierowany na `/ankieta` (404 – strona powstaje w Etapie 2).
5. Zarejestruj nowe konto na `/rejestracja`.
6. `http://127.0.0.1:8000/docs` → `GET /uzytkownicy` z tokenem admina.

## Znane problemy / TODO
- Strona `/ankieta` jeszcze nie istnieje (Etap 2) – uczeń z flagą `ankieta_wypelniona = false` trafia na 404.
- Panel admina (lista użytkowników, zmiana ról) ma na razie tylko API; UI w Etapie 5.
- Brak resetu hasła i potwierdzania e-maila (poza zakresem).

## Propozycje (poza zakresem)
- Testy E2E (Playwright) w repo zamiast skryptu ad hoc.
- Blokowanie/odblokowywanie kont przez admina (pole `aktywny` już jest).
- Ograniczenie liczby prób logowania (rate limiting).

## Commity (hash + opis)
- e2c4c60 Backend: logowanie JWT, hasła bcrypt, role i ochrona endpointów
- 8992378 Backend: testy auth, uprawnień i seeda kont
- f371419 Frontend: logowanie, rejestracja, ochrona stron i tryb edycji wg roli
- 7b6551c README: konta testowe i zmienne JWT
