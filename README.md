# IMSU — inteligentny system uczący (wersja 3)

Każda lekcja ma tę samą treść w trzech wersjach: V (tekst ze schematami), A (nagranie) i K (zadanie z kartą PDF). Uczeń uczy się w jednym stylu naraz. System sprawdza wynikami quizów, czy forma działa, i gdy nie działa, proponuje inną z argumentami z danych. Każdą decyzję zapisuje w dzienniku. Dokumentacja: `docs/00-START.md`.

## Uruchomienie od zera

1. Uruchom Docker Desktop, potem w katalogu głównym:
   ```
   docker compose up -d
   ```
2. Backend (`backend/`; pierwsze uruchomienie: `python -m venv venv` i `pip install -r requirements.txt`):
   ```
   .\venv\Scripts\Activate.ps1
   alembic upgrade head
   python -m app.demo.seed
   uvicorn app.main:app --reload --port 8001
   ```
3. Frontend (`frontend/`; pierwsze uruchomienie: `npm ci`, Node 20+):
   ```
   npm run dev
   ```
4. Otwórz http://localhost:3001. Konta demo (hasło `Demo123!`) i przebieg pokazu: `docs/SCENARIUSZ-POKAZU.md`.

Pliki `.env` tworzysz, kopiując `.env.example` w katalogu głównym i w `backend/` oraz `.env.local` w `frontend/`.

Baza sprzed wersji 3 (etap 9): dane uczenia v2 nie przechodzą do v3, więc przebuduj ją: `alembic downgrade base`, `alembic upgrade head`, `python -m app.demo.seed`.

## Konta demo

- Stan startowy wszystkich kont demo (po pokazie): `python -m app.demo.seed --reset-students` (w `backend/`).
- Seed jest idempotentny: drugie uruchomienie niczego nie zmienia.

## Sprawdzenie kodu

- Backend (`backend/`): `pytest`, `ruff check .`, `ruff format --check .`, migracja od zera (`alembic downgrade base`, `alembic upgrade head`).
- Frontend (`frontend/`): `npm run lint`, `npm run format:check`, `npm run build`.
- Przejście pokazu w przeglądarce ze zrzutami ekranów (Playwright spoza zależności projektu): opis na początku `frontend/e2e/demo-tour.mjs`.
