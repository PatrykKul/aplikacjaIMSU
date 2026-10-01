# StylNauki

Platforma z kursami, która dopasowuje sposób podania materiału do stylu uczenia się ucznia (model VAK: wzrokowiec / słuchowiec / kinestetyk).
Projekt zaliczeniowy z przedmiotu *Inteligentne multimedialne systemy uczące* (Informatyka UwB, 2026/27). Autor: Patryk Kulesza.

## Stos technologiczny

- **Backend** (`backend/`): FastAPI, SQLAlchemy 2, SQLite, migracje Alembic, testy pytest.
- **Frontend** (`frontend/`): Next.js 16, React 19, Tailwind 4, react-query, zustand, KaTeX/Markdown.

## Wymagania

- Python 3.12+
- Node.js 20+

## Uruchomienie backendu

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy env.example .env        # ustaw JWT_SECRET, opcjonalnie GEMINI_API_KEY
alembic upgrade head         # tworzy pustą bazę stylnauki.db
python -m app.seed           # dane startowe (konta testowe)
uvicorn app.main:app --reload --port 8000
```

API: http://127.0.0.1:8000, dokumentacja: http://127.0.0.1:8000/docs

Testy:

```powershell
cd backend
pytest
```

### Migracje

Schemat bazy tworzą wyłącznie migracje Alembic. Po zmianie modeli w `app/models.py`:

```powershell
alembic revision --autogenerate -m "opis zmiany"
alembic upgrade head
```

## Uruchomienie frontendu

```powershell
cd frontend
npm install
copy env.example .env.local  # opcjonalnie, domyślny adres API to http://127.0.0.1:8000
npm run dev
```

Aplikacja: http://localhost:3000 (backend musi działać, żeby zobaczyć kursy).

Pozostałe komendy: `npm run lint`, `npm run build`, `npm run start`.

## Zmienne środowiskowe

| Plik | Zmienna | Opis |
|---|---|---|
| `backend/.env` | `DATABASE_URL` | adres bazy, domyślnie `sqlite:///./stylnauki.db` |
| `backend/.env` | `JWT_SECRET` | sekret do podpisywania tokenów JWT (bez niego tokeny wygasają po restarcie serwera) |
| `backend/.env` | `JWT_EXPIRE_MINUTES` | czas życia tokenu, domyślnie 480 |
| `backend/.env` | `GEMINI_API_KEY` | opcjonalny klucz do generatora materiałów AI |
| `backend/.env` | `GEMINI_MODEL` | opcjonalna nazwa modelu Gemini |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | adres API backendu |

Plików `.env` nie commitujemy — wzorce są w `backend/env.example` i `frontend/env.example`.

## Konta testowe

Tworzy je `python -m app.seed` (tylko do prezentacji i testów):

| Rola | E-mail | Hasło |
|---|---|---|
| Admin | `admin@stylnauki.pl` | `Admin123!` |
| Nauczyciel | `nauczyciel@stylnauki.pl` | `Nauczyciel123!` |
| Uczeń | `uczen@stylnauki.pl` | `Uczen123!` |

Nowe konta z formularza rejestracji zawsze dostają rolę ucznia; role zmienia administrator.
