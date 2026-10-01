# STATUS

- **Ostatni ukończony etap:** Etap 6 – dopracowanie UI, dokumentacja do zaliczenia ([raport](etap-6.md)). Etapy 0–6 są zakończone.
- **Poprawki po audycie:** [poprawki-1](poprawki-1.md) – wykonane (walidacja stylu quizu, końce linii, dopisek w dokumentacji).
- **W toku:** nic. Etap 7 (dodatek LLM) pominięty zgodnie z poleceniem.
- **Blokery:** brak.
- **Otwarte pytania:** [PYTANIA.md](PYTANIA.md) – wymagania prowadzącego (termin, forma oddania, zakres) i decyzje podjęte samodzielnie do potwierdzenia.

## Jak uruchomić teraz
```powershell
# backend
cd backend
.\venv\Scripts\Activate.ps1      # pierwszy raz: python -m venv venv; pip install -r requirements.txt; copy env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --port 8000

# frontend
cd frontend
npm install
npm run dev                      # http://localhost:3000
```

Konta testowe (pełna tabela w `README.md`):
- `admin@stylnauki.pl` / `Admin123!`
- `nauczyciel@stylnauki.pl` / `Nauczyciel123!`
- `uczen@stylnauki.pl` / `Uczen123!` (bez ankiety)
- `wzrokowiec@stylnauki.pl`, `sluchowiec@stylnauki.pl`, `kinestetyk@stylnauki.pl` / `Uczen123!`

## Weryfikacja
`cd backend && pytest` (229 passed) · `cd frontend && npm run lint && npm run build` (OK)

## Uwaga do lokalnej bazy deweloperskiej
- Kurs demonstracyjny utworzony przed Etapem 4 nie ma przykładów na poziomach 1 i 3 – seed nie nadpisuje istniejącego kursu. W tej kopii kurs został już odtworzony; na innej maszynie wystarczy czysta baza + `python -m app.seed`.
- Konta `*@test.pl` tworzone przez testy przeglądarkowe zostały z bazy usunięte.

## Dokumenty
- [Dokumentacja projektu](../dokumentacja.md) – w tym scenariusz prezentacji
- Raporty: [Etap 0](etap-0.md) · [Etap 1](etap-1.md) · [Etap 2](etap-2.md) · [Etap 3](etap-3.md) · [Etap 4](etap-4.md) · [Etap 5](etap-5.md) · [Etap 6](etap-6.md) · [Poprawki 1](poprawki-1.md)
