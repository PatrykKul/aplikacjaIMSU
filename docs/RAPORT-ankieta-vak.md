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

## Etap 2: backend, czyli ankieta, profil, lekcje pod styl i adaptacja (2026-11-08)

**Zrobione** (commity `772307f`, `f05fbee`, `0cf0e27`)
- Moduł `backend/app/modules/learning_style/`: `models.py`, czyste funkcje `scoring.py`, `personalization.py` i `adaptation.py` (logika z v1), `service.py`, `router.py`, `schemas.py`, `hooks.py`.
- Migracja `ea197399889b`: 5 tabel + 20 pytań ankiety z v1 (po 3 odpowiedzi V/A/K).
- Endpointy zgodne ze SPEC: `/survey/questions|answers|results`, `/profile/learning-style` (GET/PUT/DELETE, `/proposal/accept|reject`), `/lessons/{id}/personalized-blocks`.
- `record_quiz_result(db, user=..., lesson_id=..., block_id=..., percent=...)` dla quizu Bartka.
- Zmiany w plikach Bartka zgodne z akceptacją: B1 `main.py` (import + 3× `include_router`), B2 `alembic/env.py` (+1 import), B3 `.gitignore` (`*.bak`).

**Decyzje podjęte samodzielnie**
- `QuizFeedback` jest modelem Pydantic, a nie dataclass (jak było w SPEC), żeby Bartek mógł go wprost dołożyć do odpowiedzi JSON swojego quizu.
- Teksty „dlaczego” mają formy neutralne („ten styl został wybrany ręcznie”), a nie „wybrałeś” jak w v1.
- `record_quiz_result` sam robi `commit` (opisane w docstringu).
- „Pierwszy sukces / pierwsza porażka” liczone na parę (lekcja, styl ucznia w chwili quizu).

**Jak sprawdzone**
- `pytest`: **244 passed** (178 Bartka + 66 nowych w `tests/learning_style/`).
- `ruff check .` i `ruff format --check .`: czyste. `ruff format` nie zmienił żadnego pliku Bartka (sprawdzone `git status`).
- Migracja: `alembic downgrade -1` + `upgrade head` działa, w bazie 20 pytań i po 20 odpowiedzi V, A i K.

**Co nie działa / do uwagi**
- Hook alembica `ruff_fix` (w `alembic.ini` Bartka) wymaga `ruff` na PATH. Bez aktywnego venv generowanie migracji kończy się błędem po zapisaniu pliku, a plik trzeba sformatować ręcznie (`python -m ruff format`). Nie zmieniam, to konfiguracja Bartka.
