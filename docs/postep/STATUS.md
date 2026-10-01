# STATUS

- **Ostatni ukończony etap:** Etap 4 – adaptacja w czasie ([raport](etap-4.md)).
- **W toku:** Etap 5 – panele ucznia, nauczyciela, admina.
- **Blokery:** brak.
- **Otwarte pytania:** [PYTANIA.md](PYTANIA.md).

## Jak uruchomić teraz
```powershell
# backend
cd backend
.\venv\Scripts\Activate.ps1      # pierwszy raz: python -m venv venv; pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev                      # http://localhost:3000
```
Konta testowe: `admin@stylnauki.pl` / `Admin123!`, `nauczyciel@stylnauki.pl` / `Nauczyciel123!`, `uczen@stylnauki.pl` / `Uczen123!`.

## Weryfikacja
`cd backend && pytest` · `cd frontend && npm run lint && npm run build`

## Raporty
- [Etap 0](etap-0.md)
- [Etap 1](etap-1.md)
- [Etap 2](etap-2.md)
- [Etap 3](etap-3.md)
- [Etap 4](etap-4.md)
