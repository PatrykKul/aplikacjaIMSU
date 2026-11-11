# Architektura wersji 2

Ścieżki `backend/…` i `frontend/…` są względem katalogu głównego repozytorium. Szczegóły modułów: `moduly/<nr>-<moduł>.md`.

## 1. Założenia

- **Modularny monolit**: jedna aplikacja backendowa podzielona na moduły domenowe, jedna baza; mały moduł nie musi mieć wszystkich plików.
- Stos: **Next.js** (frontend), **FastAPI** (backend), **PostgreSQL** (JSONB dla treści bloków i quizów), Alembic, pytest, Docker Compose.
- Kod po angielsku; interfejs i dokumentacja po polsku (`06-konwencje.md`).
- „Inteligencja” to **reguły** w czystych funkcjach — działa bez danych treningowych i bez LLM, jest przewidywalna, wyjaśnialna i testowalna.

## 2. Mapowanie na architekturę z wykładu

| Wykład (MITS / IEEE LTSC) | Moduł v2 |
|---|---|
| moduł dziedziny / baza wiedzy | `curriculum` (kursy, lekcje, klasy) + `content` (bloki, załączniki, pliki) |
| ocena | `assessment` (quiz lekcji, ocenianie) |
| model ucznia | `learning_style` (ankieta VAK, styl, wagi, próby quizów, rozwinięcia materiałów) |
| moduł nauczyciela / silnik uczący / baza metod | czyste funkcje w `learning_style` (`personalization.py`, `adaptation.py`) i `assessment/grading.py` |
| prezentacja | frontend: widok ucznia, edytor nauczyciela |
| komunikacja / interfejs | panel ucznia, panel nauczyciela, ewentualnie mentor |

## 3. Moduły backendu

```
backend/app/
  core/              config, db session, errors, rich text schema
  modules/
    identity/        auth, users, roles (fixed), admin user management, create-admin CLI
    curriculum/      courses, lessons, owners, publishing, classrooms
    content/         lesson blocks (TipTap text, attachments with forms), files
    learning_style/  VAK survey, learning profile, personalization, adaptation, quiz attempts, hooks
    assessment/      lesson quiz, grading, quiz editor API
  demo/              idempotent demo seed, generated assets and their generators
```

Struktura modułu: `models.py`, `schemas.py`, `service.py` (publiczny interfejs), `router.py` (cienki), czyste funkcje w osobnych plikach (`scoring.py`, `personalization.py`, `adaptation.py`, `grading.py`, `blocks.py`), opcjonalnie `cli.py`, `hooks.py`; testy w `backend/tests/<module>/`.

### Zasady zależności

- Moduł korzysta z innego **przez jego `service.py`** (i `dependencies.py` w `identity`, `hooks.py` w `learning_style`), nie przez cudze tabele w zapytaniach. Klucze obce do tabel innych modułów są dozwolone na poziomie bazy. Wyjątek: `learning_style.hooks` odczytuje tytuł lekcji przez model `Lesson` (do uzasadnienia wyniku).
- `core` nie zależy od żadnego modułu.
- Czyste funkcje **nie importują FastAPI ani SQLAlchemy** — dostają proste struktury i zwracają decyzje.
- Kierunek zależności: `core` ← `identity` ← `curriculum` ← `content` ← `learning_style` ← `assessment`; `demo` korzysta ze wszystkich serwisów.
- `assessment` przekazuje wynik quizu do modelu ucznia **tylko** przez `learning_style.hooks.record_quiz_result` (wynik liczy serwer; nie ma endpointu, przez który przeglądarka zgłasza wynik).

## 4. Model domeny

| Pojęcie | Tabela | Opis |
|---|---|---|
| User | `users` | e-mail, imię, rola (student / teacher / admin), aktywność |
| Course | `courses` | tytuł, opis, wstęp (TipTap), `owner_id`, `is_published`, `is_archived` |
| Lesson | `lessons` | kurs, tytuł, pozycja, archiwizacja |
| LessonContent / Block | `lesson_contents` | bloki lekcji w JSONB: `text` (dokument TipTap) albo `attachment` (`kind`, `forms` ⊆ {V, A, K}, tytuł, opis, plik / adres / tekst lektora) |
| File | `files` | wgrany plik (właściciel, nazwa, typ, rozmiar, losowa nazwa na dysku) |
| SurveyQuestion / SurveyAnswer | `survey_questions`, `survey_answers` | ankieta VAK (odpowiedź ma styl V / A / K) |
| SurveyResult | `survey_results` | punkty V / A / K, styl dominujący, data — historia |
| LearningProfile | `learning_profiles` | styl, źródło stylu, wagi V / A / K, odrzucona propozycja |
| QuizAttempt | `quiz_attempts` | uczeń, lekcja, wynik %, styl (efektywny) w chwili próby, czy zmieniła wagi |
| MaterialOpening | `material_openings` | rozwinięcie zwiniętego załącznika: uczeń, lekcja, blok, formy |
| LessonQuiz | `lesson_quizzes` | pytania quizu lekcji w JSONB (treść, forma, odpowiedzi, poprawna) |
| Classroom | `classrooms` | klasa nauczyciela: nazwa, `teacher_id` |
| ClassroomStudent | `classroom_students` | uczeń klasy (wiele do wielu) |
| ClassroomCourse | `classroom_courses` | kurs przypisany klasie (wiele do wielu) |

## 5. Reguły — interfejs czystych funkcji

```python
# learning_style/scoring.py
compute_score(answer_styles) -> SurveyScore                      # points, dominant_style
# learning_style/personalization.py
matches_style(block, style) -> bool                                # otherwise shown collapsed
collapsed_ids(blocks, style) -> list[str]
effective_style(style, opened_forms) -> str                        # style + forms of opened materials
style_explanation(style, source, points) -> str
# learning_style/adaptation.py
initial_weights(points) -> Weights
update_weights(weights, style, success) -> Weights
counts_for_weights(previous_results, success) -> bool
proposed_style(weights, style, source, rejected) -> str | None
# assessment/grading.py
visible_questions(questions, style) -> list
grade(questions, answers) -> Graded
```
Reguły i progi: `02-koncepcja.md` §5.

## 6. Frontend

```
frontend/src/
  app/                 routes only (thin pages composing features); (app) with AppShell, (focus) for lessons
  features/<feature>/  api.ts, hooks.ts, types.ts, errors.ts, components/
                       auth, users, dashboard, courses, teach, classes, content, learning-style, assessment
  shared/              ui (shadcn), api client, layout, rich-text, hooks, utils
```
- Dane przez TanStack Query, jeden klient API (`credentials: "include"`).
- Edytor TipTap (bloki tekstu, tryb tylko do odczytu u ucznia), wzory KaTeX, lektor przeglądarki, odtwarzacze audio / wideo, podgląd PDF.
- `SurveyGate` w layoutach `(app)` i `(focus)` kieruje ucznia bez ankiety na `/survey`.
- Interfejs dla dzieci: prostota, spójność, czytelne błędy z drogą poprawy (BPiT); design w `07-design.md`.

## 7. Infrastruktura

- `docker-compose.yml`: PostgreSQL (bazy `imsu` i `imsu_test`, port 5433); backend i frontend uruchamiane lokalnie (porty 8001 / 3001).
- Migracje Alembic od zera; testowa baza budowana migracjami; pytania ankiety wstawia migracja.
- `.env` poza repozytorium, `.env.example` z nazwami zmiennych (`JWT_SECRET` ≥ 32 znaki).
- Wgrane pliki w `UPLOAD_DIR` poza repozytorium, serwowane przez backend (`GET /files/{id}`, z obsługą Range).
- Dane demo: `python -m app.demo.seed` (`moduly/06-demo.md`).
- Testy backendu: dwie bazy w jednym kontenerze (`imsu`, `imsu_test` — tworzona przez `docker/init-test-db.sql` przy pierwszym starcie); schemat testowy budowany prawdziwymi migracjami; wspólne fixture'y (`client`, `login`, `student`, `teacher`, `admin`, `make_course`…) w `backend/tests/conftest.py`.
- `GET /health` zwraca stan API i bazy (`connect_timeout=5`, więc przy wyłączonej bazie `database: error` zamiast zawieszenia). Po restarcie komputera: Docker Desktop i `docker compose up -d`.
- Frontend: Next.js 16 (Cache Components wyłączone — dane pobiera przeglądarka z FastAPI), Tailwind przez PostCSS, shadcn/ui `base-nova`. Uruchomienie od zera: `README.md` i `SCENARIUSZ-POKAZU.md`.
