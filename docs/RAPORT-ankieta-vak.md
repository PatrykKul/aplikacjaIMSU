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

## Etap 3: frontend (2026-11-08)

**Zrobione** (commity `e904861`, `69affb8`)
- `frontend/src/features/learning-style/`: `api.ts`, `hooks.ts` (React Query), `types.ts`, `styles.ts`, `errors.ts` i komponenty `SurveyGate`, `SurveyForm`, `SurveyResult`, `LearningStylePanel`, `StyleBars`, `StyleProposalBanner`, `PersonalizationNote`, `AdaptationFeedback`.
- Strony: `/survey` (ankieta), `/survey/result` (wynik), `/profile` („Mój styl uczenia się”), wszystkie tylko dla roli `student` (`RoleGate` Bartka).
- Podpięcia zgodne z akceptacją: F1 `(app)/layout.tsx` i F2 `(focus)/layout.tsx` (`SurveyGate`), F3 link „Mój styl” w menu ucznia, F4 `LessonView.tsx` (`usePersonalizedBlocks` + `PersonalizationNote`).

**Decyzje podjęte samodzielnie**
- `SurveyGate` w `(app)/layout` stoi **wewnątrz** `AuthenticatedShell`, żeby na ekranie ankiety był nagłówek z wylogowaniem.
- Kolejność odpowiedzi w pytaniu jest mieszana deterministycznie (wg id), a nie `Math.random`, żeby uniknąć różnic przy renderowaniu i ostrzeżeń lintera. Efekt jest ten sam: V nie jest zawsze pierwsze.
- Komunikaty błędów nowych kodów (`SURVEY_*`, `NO_PROPOSAL`) są we własnym `errors.ts`, z fallbackiem do `errorMessage` Bartka, bez zmiany jego `error-messages.ts`.
- Notka „dlaczego to widzisz” pokazuje się tylko uczniom. Nauczyciel/admin w podglądzie widzi lekcję jak wcześniej.

**Jak sprawdzone**
- `npm run lint`: czysto. `tsc --noEmit`: 0 błędów w `src/`. `npm run build`: OK, nowe trasy `/survey`, `/survey/result`, `/profile`.

**Co nie działa / do uwagi**
- Pierwszy `npm run build` padał na `EPERM rmdir .next/server/...`: katalogi starego builda v1 (z 01.10) miały atrybut **tylko do odczytu** (pozostałość po kopiowaniu folderu). Usunąłem stare `.next/server|static|types|diagnostics` (artefakty, ignorowane przez git). `.next/dev` działającego serwera nie był ruszany.
- Przejście w przeglądarce: w etapie 5 (po decyzji o quizie).

## Etap 4: dane demo (2026-11-08)

**Zrobione**
- Komenda `python -m app.demo.seed` (z katalogu `backend/`), idempotentna; `--reset-students` czyści tylko dane ankiety i quizów **dwóch kont demo uczniów**.
- 3 opublikowane kursy nauczyciela demo, razem 7 lekcji. W każdej lekcji: blok tekstowy (wspólny), obrazy **V**, nagrania **A** (tekst czytany przez lektora przeglądarki), karty ćwiczeń PDF **K** i materiały mieszane (V+K, A+K):
  - Matematyka: funkcja liniowa (Wzór i wykres; Współczynnik kierunkowy a; Miejsce zerowe),
  - Angielski: Present Perfect (Budowa zdania; Present Perfect czy Past Simple?),
  - Programowanie: pętle w Pythonie (Pętla for; Pętla while).
- Materiały lokalne: 10 PNG (wykresy, schematy, schemat blokowy, kod) i 7 PDF (karty ćwiczeń) w `backend/app/demo/assets/`; zero linków zewnętrznych. Generator: `app/demo/generate_assets.py` (wymaga Pillow, którego **nie** dodałem do `requirements.txt`; wygenerowane pliki są w repo, więc seed nie potrzebuje niczego dodatkowego).
- Konta (hasło `Demo123!`):

| Konto | Rola | Stan |
|---|---|---|
| `nauczyciel.demo@imsu.pl` | nauczyciel | właściciel 3 kursów |
| `admin.demo@imsu.pl` | admin | – |
| `uczen.nowy@imsu.pl` | uczeń | bez ankiety → pokaz wymuszenia |
| `uczen.demo@imsu.pl` | uczeń | ankieta V 9 / A 8 / K 3 (styl V), 4 quizy przez `record_quiz_result` (85%, 55%, 40%, 45%) → wagi V 7 / A 8 / K 3 → **propozycja zmiany na A** z uzasadnieniem |

**Decyzje podjęte samodzielnie**
- SVG nie wchodzi w grę: moduł plików Bartka go nie przyjmuje (świadomie, ze względów bezpieczeństwa). Dlatego PNG.
- Brak wideo: nie ma lokalnego źródła, a YouTube to link zewnętrzny (zakazany przez polecenie).
- Lektor przeglądarki czyta po polsku (`pl-PL` w `SpeechReader` Bartka), więc transkrypcje A są po polsku, także w kursie angielskiego. Angielskie zdania są w tekście i PDF-ach.
- `# ruff: noqa: E501` na górze `courses.py` i `generate_assets.py`: to treść dydaktyczna, zdania zostają w całości; `pyproject.toml` Bartka bez zmian.
- Kurs rozpoznawany po (nauczyciel demo, tytuł). Jeśli istnieje, seed go nie dotyka (nie nadpisuje zmian zrobionych ręcznie).

**Jak sprawdzone**
- Seed uruchomiony dwa razy na bazie deweloperskiej: drugi przebieg niczego nie dubluje.
- `tests/demo/test_seed.py` (4 testy): kursy opublikowane z plikami, nowy uczeń bez ankiety, uczeń demo z propozycją A, idempotencja, reset czyści tylko dane stylu.
- `ruff check .` / `ruff format --check .`: czyste. Obrazy obejrzane, 2 poprawione (łączniki w schemacie wzoru, napis na osi czasu, strzałka powrotu w schemacie pętli).

**Co nie działa / do uwagi**
- Jeśli seed zostanie przerwany w połowie tworzenia kursu, kolejne uruchomienie uzna kurs za istniejący. Wtedy trzeba go zarchiwizować w UI nauczyciela i uruchomić seed ponownie.
