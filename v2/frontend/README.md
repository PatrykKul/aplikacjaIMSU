# IMSU v2

## Uruchomienie

1. Uruchom Docker Desktop, potem w `v2/`:
   ```
   docker compose up -d
   ```
2. Backend (`v2/backend`, pierwsze uruchomienie: `python -m venv venv` i `pip install -r requirements.txt`):
   ```
   .\venv\Scripts\Activate.ps1
   alembic upgrade head
   uvicorn app.main:app --reload --port 8001
   ```
3. Frontend (`v2/frontend`, pierwsze uruchomienie: `npm install`):
   ```
   npm run dev
   ```
4. Otwórz http://localhost:3001: serwer i baza powinny pokazywać „działa”.

Pliki `.env` tworzysz, kopiując `.env.example` w `v2/`, `v2/backend/` oraz `.env.local` w `v2/frontend/`.

## Sprawdzenie kodu

- Backend: `pytest`, `ruff check .`, `ruff format --check .`
- Frontend: `npm run lint`, `npm run build`