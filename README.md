# StylNauki

Platforma z kursami, która dopasowuje sposób podania materiału do ucznia: na start według stylu uczenia się (ankieta VAK: wzrokowiec / słuchowiec / kinestetyk), potem według wyników quizów (adaptacja regułowa, bez LLM).

Projekt zaliczeniowy z przedmiotu *Inteligentne multimedialne systemy uczące* (Informatyka UwB, 2026/27). Autor: Patryk Kulesza.

- Opis działania, architektura, model danych i scenariusz prezentacji: [docs/dokumentacja.md](docs/dokumentacja.md)
- Postęp prac i raporty etapów: [docs/postep/STATUS.md](docs/postep/STATUS.md)

## Stos technologiczny

- **Backend** (`backend/`): FastAPI, SQLAlchemy 2, SQLite, migracje Alembic, JWT + bcrypt, testy pytest.
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
alembic upgrade head         # tworzy bazę stylnauki.db
python -m app.seed           # konta testowe, 20 pytań ankiety, kurs demonstracyjny V/A/K
uvicorn app.main:app --reload --port 8000
```

API: http://127.0.0.1:8000, dokumentacja: http://127.0.0.1:8000/docs

Seed jest idempotentny — można go uruchamiać wielokrotnie.

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

Aplikacja: http://localhost:3000 (backend musi działać).

Pozostałe komendy: `npm run lint`, `npm run build`, `npm run start`.

## Zmienne środowiskowe

| Plik | Zmienna | Opis |
|---|---|---|
| `backend/.env` | `DATABASE_URL` | adres bazy, domyślnie `sqlite:///./stylnauki.db` |
| `backend/.env` | `JWT_SECRET` | sekret do podpisywania tokenów JWT (bez niego tokeny wygasają po restarcie serwera) |
| `backend/.env` | `JWT_EXPIRE_MINUTES` | czas życia tokenu, domyślnie 480 |
| `backend/.env` | `MEDIA_ROOT` | opcjonalny katalog na wgrywane obrazki i nagrania, domyślnie `backend/uploads` |
| `backend/.env` | `GEMINI_API_KEY` | opcjonalny klucz do generatora szkicu lekcji (AI) dla nauczyciela |
| `backend/.env` | `GEMINI_MODEL` | opcjonalna nazwa modelu Gemini |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | adres API backendu |

Plików `.env` nie commitujemy — wzorce są w `backend/env.example` i `frontend/env.example`.

## Konta testowe

Tworzy je `python -m app.seed` (tylko do prezentacji i testów):

| Rola | E-mail | Hasło | Uwagi |
|---|---|---|---|
| Admin | `admin@stylnauki.pl` | `Admin123!` | użytkownicy, role, blokady |
| Nauczyciel | `nauczyciel@stylnauki.pl` | `Nauczyciel123!` | kursy, ankieta, uczniowie |
| Uczeń | `uczen@stylnauki.pl` | `Uczen123!` | bez ankiety — pokazuje wymuszenie ankiety |
| Uczeń | `wzrokowiec@stylnauki.pl` | `Uczen123!` | ankieta V 12 / A 5 / K 3 |
| Uczeń | `sluchowiec@stylnauki.pl` | `Uczen123!` | ankieta V 4 / A 12 / K 4 |
| Uczeń | `kinestetyk@stylnauki.pl` | `Uczen123!` | ankieta V 3 / A 5 / K 12 |

Nowe konta z formularza rejestracji zawsze dostają rolę ucznia; role zmienia administrator.

## Co gdzie jest w aplikacji

| Rola | Strona startowa | Najważniejsze widoki |
|---|---|---|
| Uczeń | `/panel` | ankieta (`/ankieta`), kursy (`/kursy`), profil i styl (`/profil`) |
| Nauczyciel | `/nauczyciel` | uczniowie, edytor ankiety (`/nauczyciel/ankieta`), kursy z „Trybem Edycji" i podglądem V / A / K |
| Admin | `/admin/uzytkownicy` | użytkownicy + wszystko, co nauczyciel |
