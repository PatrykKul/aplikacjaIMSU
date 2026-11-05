# Etap 0 – czysty start   (01.10.2026, 18:45)

## Plan (krótko)
Usunąć pozostałości kodu startowego niezwiązane z aplikacją, założyć repo, spłacić dług techniczny backendu (Alembic, jeden endpoint reorder, błędy 500, nieblokujące AI), uruchomić całość na pustej bazie, README.

## Co zrobione (lista, z plikami)
- Frontend: usunięty landing, chatbot, formularz kontaktowy, stare grafiki, nieużywane hooki/utils/dane; nowa strona startowa `frontend/src/app/page.tsx`; nazwa „StylNauki" w `layout.tsx`, `Navbar.tsx`, `KursyListClient.tsx`.
- Frontend: wyłączony statyczny eksport (`next.config.ts`), strony kursów/działów/tematów renderowane dynamicznie, `lib/server-fetch.ts` bez cache (świeże dane).
- Backend: `app/database.py` (`DATABASE_URL`, domyślnie `stylnauki.db`), `app/main.py` bez `create_all` i ręcznych `ALTER TABLE`.
- Backend: Alembic (`alembic.ini`, `alembic/env.py`, `alembic/versions/0001_schemat_bazowy_kursow.py`), szkielet `app/seed.py`.
- Backend: `services/ai_generator.py` – tylko generator materiałów, z łańcuchem modeli zapasowych i wyjątkiem `AIConfigError`.
- Backend: `routers/kursy.py` – jeden endpoint `PUT /kursy/reorder`, usunięte duplikaty, komunikaty błędów bez treści wyjątków i ścieżek dysku, generowanie AI przez threadpool bez trzymania sesji bazy.
- Testy: `backend/tests/conftest.py`, `backend/tests/test_kursy.py`.
- `README.md`, `backend/env.example`, porządek w `CLAUDE.md`.

## Decyzje i dlaczego
- Start z pustą bazą (decyzja autora); schemat wyłącznie z migracji – testy też budują bazę migracjami, więc migracje są testowane.
- `PUT /kursy/reorder` musi być zadeklarowany przed `/kursy/{kurs_id}` – inaczej „reorder" jest parsowane jako id (422). To była przyczyna istnienia duplikatu.
- Błąd AI: 503 gdy brak klucza, 502 gdy model zawiódł – szczegóły tylko w logach.
- Strony dynamiczne zamiast eksportu statycznego – logowanie i personalizacja wymagają renderowania per użytkownik.

## Weryfikacja (komendy + wynik)
- `pytest` → 7 passed
- `npm run lint` → 0 błędów (3 ostrzeżenia o `<img>`)
- `npm run build` → OK
- Smoke: backend + `next start`, `/`, `/kursy`, `/kursy/1` → 200, `/kursy/999` → 404.
- Grep na nazwy starego projektu w kodzie, README i UI → brak trafień.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. Backend i frontend wg `README.md`.
2. http://localhost:3000 → strona startowa → „Przejdź do kursów".
3. Włącz tryb edycji w pasku nawigacji, dodaj kurs → dział → temat → blok.

## Znane problemy / TODO
- Tryb edycji nie jest jeszcze chroniony logowaniem (Etap 1).
- Ostrzeżenia lint o `<img>` w `TematLessonView.tsx` (obrazki z uploadu).

## Propozycje (poza zakresem)
- Brak.

## Commity (hash + opis)
- 648e134 Dokumentacja startowa: README, CLAUDE.md, .gitignore
- d3703e1 Backend: API kursów (FastAPI + SQLAlchemy) i generator materiałów AI
- 688e80b Backend: migracje Alembic (schemat bazowy) i szkielet seeda
- 06128aa Backend: testy pytest (kursy, zmiana kolejności, błędy generatora AI)
- 613f19e Frontend: strony kursów i strona startowa StylNauki
