# RAPORT: ankieta VAK, profilowanie, adaptacja (gałąź `feat/ankieta-vak`)

## Etap 0: porządki (2026-11-08)

**Zrobione**
- Utworzona gałąź `feat/ankieta-vak` od `v2` (`45a252f`).
- Kopia starego `backend/.env` (z v1) przeniesiona z katalogu tymczasowego do `backend/.env.v1.bak`.
- Środowisko lokalne: odtworzony `backend/venv` (stary miał zapisaną ścieżkę `Magisterka 1 semestr`, przez co `uvicorn.exe` i `alembic.exe` nie startowały), utworzone `.env` i `frontend/.env.local` z przykładów, do `backend/.env` dopisane brakujące klucze v2.

**Jak sprawdzone**
- `git check-ignore -v`: `.env`, `backend/.env` (`.gitignore`) i `frontend/.env.local` (`frontend/.gitignore`) są ignorowane.
- Wartości z plików env nie były wypisywane.

**Co nie działa / do uwagi**
- `*.bak` **nie było** w `.gitignore`, więc `backend/.env.v1.bak` (zawiera klucze) mógł trafić do commita. Tymczasowo zabezpieczone lokalnym `.git/info/exclude` (`*.bak`), bez zmiany plików w repo. Docelowo dopisać `*.bak` do `.gitignore`: zmiana B3 w specyfikacji, czeka na akceptację.
- `frontend/package-lock.json` jest zmodyfikowany po `npm install` z innej wersji npm. To nie są moje zmiany i nie są commitowane.
- Rejestracja z rolą `teacher` przez `/auth/register`: zgodnie z poleceniem nie poprawiane, zgłasza autor.

## Etap 1: specyfikacja (2026-11-08)

**Zrobione**
- `docs/SPEC-ankieta-vak.md`: tabele i migracja, endpointy, ekrany, adaptacja z interfejsem dla quizu, lista zmian w istniejących plikach (B1–B3, F1–F4), plan testów, kolejność commitów.

**Jak sprawdzone**
- Logika przeniesiona z v1: `services/vak.py`, `personalizacja.py`, `adaptacja.py`, `routers/ankieta.py`, `seed_ankieta.py`.
- Punkty styku w v2 sprawdzone w kodzie: `main.py`, `alembic/env.py`, `content/service.get_blocks`, `curriculum/service.get_visible_lesson`, `tests/conftest.py`, frontend `LessonView.tsx`, `(app)/layout.tsx`, `(focus)/layout.tsx`, `AuthenticatedShell.tsx`.
- Stan wyjściowy: `pytest` 178 passed, `npm run lint` czysty, aplikacja uruchomiona lokalnie.

**Co nie działa / do uwagi**
- Kodu jeszcze nie ma. **Czeka na akceptację specyfikacji** (sekcja 8 SPEC).
