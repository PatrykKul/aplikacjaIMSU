# Architektura (wersja 3)

Ścieżki `backend/…` i `frontend/…` są względem katalogu głównego repozytorium. Szczegóły modułów: `moduly/<nr>-<moduł>.md`.

## 1. Założenia

- **Modularny monolit**: jedna aplikacja backendowa podzielona na moduły domenowe, jedna baza; mały moduł nie musi mieć wszystkich plików.
- Stos: **Next.js** (frontend), **FastAPI** (backend), **PostgreSQL** (JSONB dla dokumentów TipTap, bloków wersji, puli pytań, dowodów decyzji), SQLAlchemy 2, Alembic, pytest, Docker Compose.
- Kod po angielsku; interfejs i dokumentacja po polsku (`06-konwencje.md`). Backend zwraca **kody i liczby**, polskie zdania składa frontend (D3, D45).
- „Inteligencja” to **reguły** w czystych funkcjach — działa bez danych treningowych i bez LLM, jest przewidywalna, wyjaśnialna i testowalna. Każda decyzja ma wpis w dzienniku z danymi, z których wynika.

## 2. Mapowanie na architekturę z wykładu

| Wykład (MITS / IEEE LTSC) | Moduł v3 |
|---|---|
| moduł dziedziny / baza wiedzy | `curriculum` (kursy, lekcje, zarys, wnioski, zapisy, kolejność) + `content` (wersje V / A / K, załączniki, pliki) |
| ocena | `assessment` (pula pytań, losowanie, ocenianie) |
| model ucznia | `learning_style` (ankieta, styl, procenty, wyniki, statystyki form, dziennik) |
| moduł nauczyciela / silnik uczący / baza metod | czyste funkcje `learning_style/rules.py` (R1–R8), `assessment/drawing.py` (R9), `curriculum/progress.py` (R10) |
| autorstwo (moduł nauczyciela) | `authoring` (gotowość R11 i publikacja lekcji) + edytor we frontendzie |
| prezentacja | frontend: lekcja w formie ucznia, edytor nauczyciela, panele |
| komunikacja / interfejs | „Moje postępy” i dziennik ucznia, panel kursu nauczyciela |

## 3. Moduły backendu

```
backend/app/
  core/              config, db session, errors (AppError with params), health, rich text (TipTap type, is_empty_document)
  modules/
    identity/        auth, users, fixed roles, teacher approval, admin user management, create-admin CLI
    curriculum/      courses, lessons (outline, conclusions, publication flag), enrollments, lesson unlocking
    content/         lesson versions V / A / K (text blocks, attachments), files, version readiness
    learning_style/  survey, profile (style, percentages), study, adaptation rules, proposals, trials, journal, stats
    assessment/      question pool, drawing, grading, quiz API
    authoring/       lesson readiness (R11) and publication
  demo/              idempotent demo seed, course contents, generated assets and their generators
```

Struktura modułu: `models.py`, `schemas.py`, `service.py` (publiczny interfejs), `router.py` (cienki), czyste funkcje w osobnych plikach, opcjonalnie `cli.py`, `hooks.py`, `dependencies.py`; testy w `backend/tests/<module>/`.

### Zasady zależności

- Kierunek: `core` ← `identity` ← `curriculum` ← `content` ← `learning_style` ← `assessment` ← `authoring`; `demo` korzysta ze wszystkich serwisów. Moduł importuje tylko moduły po swojej lewej stronie.
- Moduł korzysta z innego **przez jego `service.py`** (i `dependencies.py` w `identity`, `hooks.py` w `learning_style`), nie przez cudze tabele w zapytaniach. Klucze obce do tabel innych modułów — tylko na poziomie bazy.
- Wyjątek: `learning_style` czyta modele `Lesson` i `Course` z `curriculum` **po kluczu** (tytuły lekcji i kursów w dowodach decyzji, dzienniku i wynikach).
- Odblokowanie lekcji należy do `curriculum` (`lesson_completions`), więc blokada (R10) nie wymaga zależności „w górę”: `learning_style.hooks` po zaliczeniu woła `curriculum.service.mark_lesson_passed`.
- `assessment` przekazuje wynik quizu do modelu ucznia **tylko** przez `learning_style.hooks.record_quiz_result` (wynik liczy serwer; nie ma endpointu, przez który przeglądarka zgłasza wynik).
- `authoring` nie ma tabel: zbiera braki z `curriculum`, `content` i `assessment`, publikuje przez `curriculum.service.set_lesson_published`.
- `core` nie zależy od żadnego modułu. Czyste funkcje **nie importują FastAPI ani SQLAlchemy** — dostają proste struktury i zwracają decyzje.

## 4. Model domeny

| Pojęcie | Tabela | Moduł | Opis |
|---|---|---|---|
| User | `users` | identity | e-mail, imię, rola (student / teacher / admin), `approval_status` (approved / pending / rejected), aktywność |
| Course | `courses` | curriculum | tytuł, opis, wstęp i podsumowanie (TipTap), `owner_id`, `is_published`, `is_archived` |
| Lesson | `lessons` | curriculum | kurs, tytuł, pozycja, zarys i wnioski (TipTap), `is_published`, archiwizacja |
| Enrollment | `enrollments` | curriculum | prośba o zapis: kurs, uczeń, status (pending / accepted / rejected), daty prośby i decyzji |
| LessonCompletion | `lesson_completions` | curriculum | pierwsze zaliczenie lekcji przez ucznia (podstawa odblokowania) |
| CourseOwnerChange | `course_owner_changes` | curriculum | zmiana właściciela kursu przez administratora: kurs, z kogo, na kogo, kto, kiedy (D56) |
| LessonContent | `lesson_contents` | content | jedna wersja lekcji (`form` V / A / K) — bloki w JSONB: `text` (TipTap) albo `attachment` (`kind`, tytuł, opis, plik / adres / tekst lektora) |
| File | `files` | content | wgrany plik (właściciel, nazwa, typ, rozmiar, losowa nazwa na dysku) |
| SurveyQuestion / SurveyAnswer | `survey_questions`, `survey_answers` | learning_style | ankieta VAK (odpowiedź ma styl V / A / K) |
| SurveyResult | `survey_results` | learning_style | punkty V / A / K i lider (litery remisu), raz na ucznia |
| LearningProfile | `learning_profiles` | learning_style | aktywny styl (albo null przy remisie), źródło stylu, procenty V / A / K |
| StyleHistory | `style_history` | learning_style | procenty i styl po każdej zmianie (wykres), powiązanie ze zdarzeniem |
| QuizResult | `quiz_results` | learning_style | wynik w modelu ucznia: kurs, lekcja, zestaw, forma, procent, zaliczenie, `counted` |
| LessonForm | `lesson_forms` | learning_style | jawny wybór formy lekcji przez ucznia |
| StyleProposal | `style_proposals` | learning_style | propozycja `switch` / `revert` z dowodem i statusem (najwyżej jedna otwarta) |
| StyleTrial | `style_trials` | learning_style | okres próbny: style, źródło, średnie przed / po, wynik |
| DecisionEvent | `decision_events` | learning_style | dziennik decyzji: typ, kurs, lekcja, dane |
| LessonQuiz | `lesson_quizzes` | assessment | pula pytań lekcji w JSONB (treść, odpowiedzi, poprawna, wyjaśnienie) |
| QuizDraw | `quiz_draws` | assessment | wylosowany zestaw ucznia: pytania, forma lekcji przy losowaniu, odpowiedzi, wynik, czas wysłania (null = otwarty) |

Migracje: od `be52e423dcf8` do `01324f58656d_v3_adaptation` (usuwa tabele klas, `material_openings`, `quiz_attempts`; dane uczenia v2 nie są przenoszone — bazy przebudowujemy: `alembic downgrade base`, `alembic upgrade head`, seed).

## 5. Reguły — interfejs czystych funkcji

```python
# learning_style/scoring.py
compute_score(answer_styles) -> SurveyScore                        # points, dominant_style
# learning_style/rules.py (R1-R8)
survey_percentages(points) -> Percentages                           # R1
survey_leaders(points) -> list[str]                                 # R1, tie -> several
apply_result(percentages, form, passed) -> Percentages              # R2
is_counted(previous_forms_in_lesson, form) -> bool                  # R2
form_stats(results) -> dict[str, FormStats]                         # R3: lessons, average, confirmed
counted_total(stats) -> int
praise(results) -> Praise | None                                    # R4
retry_suggestion(failed, percentages, stats, survey, results) -> Suggestion   # R5
switch_proposal(style, percentages, stats, rejections, trial_active) -> ProposalDraft | None  # R6
form_evidence(form, percentages, stats) -> dict
forms_to_clear(chosen_forms, passed_lesson_ids) -> list[int]        # R6
trial_baseline(results, previous_style) -> int | None               # R7
trial_outcome(before_average, form, after_results) -> TrialOutcome | None     # R7
trial_progress(form, after_results) -> int                          # R7
course_hint(course_results, student_id) -> Hint | None              # R8
# learning_style/stats.py
form_effectiveness(course_results) -> dict[str, FormEffect]
style_distribution(styles) -> dict[str, int]
counted_average(results) -> int | None
lesson_results(lessons, attempts, passed_ids) -> list[dict]
# assessment/drawing.py, grading.py
draw_questions(pool_ids, last_ids, k=5, rng=None) -> list[str]      # R9
grade(questions, answers) -> Graded
# curriculum/progress.py
lesson_states(lesson_ids, passed) -> list[LessonState]              # R10
next_lesson_id(lesson_ids, lesson_id) -> int | None
# readiness (R11)
curriculum/readiness.py: lesson_issues(outline, conclusions) -> list[Issue]
content/readiness.py:    version_issues(form, blocks) -> list[Issue]
assessment/readiness.py: quiz_issues(question_count) -> list[Issue]
```
Reguły, progi i przykłady: `moduly/04-learning-style.md` (R1–R8), `moduly/05-assessment.md` (R9), `moduly/02-curriculum.md` (R10), `moduly/07-authoring.md` (R11). Kolejność stosowania reguł po quizie: `hooks.record_quiz_result` (`moduly/04-learning-style.md`).

## 6. Frontend

```
frontend/src/
  app/                 routes only (thin pages composing features); (app) with AppShell, (focus) for lessons, (auth) for login / register
  features/<feature>/  api.ts, hooks.ts, types.ts, errors.ts, components/
  shared/              ui (shadcn), api client and query provider, layout, rich-text, hooks, lib
frontend/e2e/
  demo-tour.mjs        Playwright walk through the demo show, run by hand
```

| Feature | Zawartość |
|---|---|
| `auth` | logowanie, rejestracja, strażnicy (`AuthGuard`, `GuestGuard`, `RoleGate`), nawigacja ról, ekran `/pending` |
| `users` | administracja kont, zatwierdzanie nauczycieli |
| `dashboard` | `/dashboard` z kartami według roli |
| `landing` | strona startowa gościa pod `/` |
| `courses` | katalog i „Moje kursy”, strona kursu ze stanami lekcji, lekcja ucznia (`LessonStudy`) i podgląd autora (`LessonPreview`) |
| `teach` | kursy nauczyciela, edytor kursu i lekcji (zakładki wersji, pula, gotowość, publikacja), panel kursu, szczegóły ucznia |
| `content` | wyświetlanie bloków i załączników, lektor, wersje lekcji |
| `learning-style` | ankieta i `SurveyGate`, „Mój styl”, pasek formy lekcji, sugestia, propozycja, okres próbny, informacja po quizie, **`explain.ts`** (jedyne miejsce składania zdań decyzji) |
| `assessment` | quiz ucznia, przegląd odpowiedzi z wyjaśnieniami, podgląd puli |
| `progress` | „Moje postępy”: `PercentChart` (własny wykres SVG z tabelą danych), `LessonResultsTable`, `DecisionJournal`, `FormPercentages` (używane też w szczegółach ucznia) |

`health` — mały feature stanu API na placu zabaw `/dev/ui`.

- Dane przez TanStack Query, jeden klient API (`credentials: "include"`); klucze w `hooks.ts` featurów (lista w opisach modułów). Błąd `TEACHER_NOT_APPROVED` z dowolnego zapytania odświeża `["auth","me"]` (`shared/api/query-provider.tsx`), więc odrzucony nauczyciel trafia na `/pending`.
- `SurveyGate` w layoutach `(app)` i `(focus)` kieruje ucznia bez ankiety na `/survey`, a z nierozstrzygniętym remisem na `/survey/result`.
- Edytor TipTap (tekst, tryb tylko do odczytu u ucznia), wzory KaTeX, lektor przeglądarki, odtwarzacze audio / wideo, podgląd PDF.
- Interfejs dla dzieci: prostota, spójność, czytelne błędy z drogą poprawy (BPiT); design w `07-design.md`.

## 7. Infrastruktura

- `docker-compose.yml` (projekt `imsu`): PostgreSQL 17 (bazy `imsu` i `imsu_test`, port 5433); backend i frontend uruchamiane lokalnie (porty 8001 / 3001).
- Migracje Alembic od zera; pytania ankiety wstawia migracja; testowa baza budowana prawdziwymi migracjami.
- `.env` poza repozytorium, `.env.example` z nazwami zmiennych (`JWT_SECRET` ≥ 32 znaki).
- Wgrane pliki w `UPLOAD_DIR` poza repozytorium, serwowane przez backend (`GET /files/{id}`, z obsługą Range).
- Dane demo: `python -m app.demo.seed` (`--reset-students`, `--refresh-demo-media`; `moduly/06-demo.md`). Generatory zasobów demo — w osobnym venv narzędziowym (Pillow, edge-tts, imageio-ffmpeg; internet dla nagrań).
- Testy backendu: `pytest` (540 testów, w tym reguły w `test_rules.py`), dwie bazy w jednym kontenerze (`imsu_test` tworzona przez `docker/init-test-db.sql` przy pierwszym starcie); wspólne fixture'y (`db`, `client`, `make_user`, `login`, `student`, `teacher`, `other_teacher`, `admin`, `make_course`, `enroll`) w `backend/tests/conftest.py`. Kontrola: `ruff check .`, `ruff format --check .`.
- Frontend: Next.js 16 (Cache Components wyłączone — dane pobiera przeglądarka z FastAPI), Tailwind przez PostCSS, shadcn/ui `base-nova`; kontrola `npm run lint`, `npm run format:check`, `npm run build`; przejście scenariusza pokazu `node e2e/demo-tour.mjs` (Playwright spoza zależności projektu, zrzuty do `docs/zrzuty-v3/`).
- `GET /health` zwraca stan API i bazy. Po restarcie komputera: Docker Desktop i `docker compose up -d`. Uruchomienie od zera: `README.md` i `SCENARIUSZ-POKAZU.md`.
