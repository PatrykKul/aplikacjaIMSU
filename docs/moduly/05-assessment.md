# Moduł `assessment`

Quiz lekcji: pula pytań z wyjaśnieniami, losowanie 5 pytań na podejście, ocenianie na serwerze, przekazanie wyniku do modelu ucznia. Decyzje: D29, D43, D49 (część quizu).

## Odpowiedzialność
- Jedna **pula pytań** na lekcję (JSONB), zapis w całości przez autora; administrator ją czyta.
- Losowanie zestawu dla ucznia (R9, `drawing.py`), zapis zestawu na serwerze (`quiz_draws`) — klucz odpowiedzi i wyjaśnienia nie trafiają do przeglądarki przed wysłaniem.
- Ocena **tylko wobec wylosowanego zestawu** (`grading.py`) i przekazanie wyniku do modelu ucznia **wyłącznie** przez `learning_style.hooks.record_quiz_result` (nie ma endpointu, przez który przeglądarka zgłasza wynik). Forma wyniku = forma lekcji w chwili wysłania.
- Gotowość puli do publikacji (R11, `readiness.py`).
- Korzysta z `curriculum.service` (`get_study_lesson`, `get_owned_lesson`, `get_visible_lesson`) i `learning_style.service` (`require_style`, `lesson_form`, `now`). Interfejs dla innych: `question_count(db, lesson_id)` (dla `authoring`), `current_draw`, `submit_attempt`, `save_quiz` (seed), `rng` (źródło losowości — seed i testy podstawiają `random.Random(seed)`).

## Model danych

| Tabela | Kolumny |
|---|---|
| `lesson_quizzes` | `id`, `lesson_id` → `lessons` (CASCADE, unikalny), `questions` (JSONB), `updated_at` |
| `quiz_draws` | `id`, `user_id` → `users` (CASCADE), `lesson_id` → `lessons` (CASCADE), `question_ids` (JSONB, w kolejności pokazania), `answers` (JSONB `{question_id: answer_id}`, null do wysłania), `percent` (0–100, null do wysłania), `created_at`, `submitted_at` (null = podejście otwarte); indeks (`user_id`, `lesson_id`) |

Migracje `2e7cf4c0d9fc`, `01324f58656d` (pytania v2 bez wyjaśnień usunięte, nowa tabela `quiz_draws`). Wynik w modelu ucznia (`quiz_results`) zapisuje `learning_style`.

Pytanie (`schemas.QuizQuestion`): `id` (`[A-Za-z0-9_-]{1,40}`), `text` (1–500), `answers` (3–4: `id`, `text` 1–200, unikalne `id`), `correct_answer_id` (jedna z odpowiedzi), **`explanation`** (1–1000, wymagane). Pula: 1–50 pytań (`MAX_QUESTIONS`), unikalne `id`; do publikacji lekcji ≥ 5 (`QUIZ_SIZE`). Pytania nie mają formy — quiz jest wspólny dla trzech wersji.

## Logika

### R9. Losowanie — `drawing.draw_questions(pool_ids, last_ids, k=5, rng)`
- Najpierw losowo pytania spoza **ostatniego wysłanego** zestawu, potem uzupełnienie losowo z tego zestawu; razem `min(k, len(pool))`; wybrane pytania tasowane (powtórzone nie są zawsze na końcu).
- Przykłady: pula 8, poprzedni zestaw 5 → powtórka daje 3 nowe + 2 z poprzedniego; pula 10 → 5 nowych; pula 5 → zawsze cała pula. `rng` wstrzykiwany (testy deterministyczne).

### Zestaw (`service.current_draw`)
- Otwarty zestaw ucznia w lekcji jest zwracany ponownie — odświeżenie strony nie losuje od nowa.
- Otwarty zestaw z pytaniem, którego nie ma już w puli (autor zmienił pulę), jest usuwany i losowany nowy; wysłanie takiego zestawu → `409 DRAW_NOT_OPEN` (zestaw usunięty, następny `GET` losuje).
- Po wysłaniu (`submitted_at`) zestaw jest zamknięty: drugie wysłanie, cudzy zestaw albo zestaw innej lekcji → `409 DRAW_NOT_OPEN`.

### Ocena — `grading.grade(questions, answers)`
- Odpowiedzi muszą dotyczyć dokładnie pytań zestawu (`400 QUIZ_INCOMPLETE`), każda odpowiedź musi należeć do pytania (`400 QUIZ_ANSWER_MISMATCH`). `percent = round(100 · poprawne / wszystkie)`; przy 5 pytaniach 0 / 20 / 40 / 60 / 80 / 100%.
- Zaliczenie: `percent >= 70` (`learning_style.rules.PASS_THRESHOLD`) — od 4 z 5. Podejść bez limitu.
- Po ocenie: zapis `answers`, `percent`, `submitted_at`, potem `record_quiz_result` (R2–R7, odblokowanie lekcji; `moduly/04-learning-style.md`).

### R11 — pula (`readiness.quiz_issues(count)`)
`count < 5` → `{area: "quiz", code: "QUIZ_TOO_FEW_QUESTIONS", count, min: 5}`. Opublikowana lekcja musi zachować pełną pulę: `PUT` z < 5 pytaniami i `DELETE` → `409 PUBLISHED_LESSON_INCOMPLETE` z `issues` (najpierw wycofanie publikacji). Szkic może mieć mniejszą pulę albo żadną.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/quiz/edit` | autor, admin (odczyt) | `{questions: [{id, text, answers, correct_answer_id, explanation}]}` (pusta lista bez puli) | 404 `LESSON_NOT_FOUND`, 403 `FORBIDDEN` (uczeń) / `TEACHER_NOT_APPROVED` |
| `PUT /lessons/{id}/quiz` | autor | zapis puli (1–50) → jak wyżej | 422, 404, 409 `PUBLISHED_LESSON_INCOMPLETE` |
| `DELETE /lessons/{id}/quiz` | autor | usunięcie puli, 204 | 404, 409 (lekcja opublikowana) |
| `GET /lessons/{id}/quiz` | uczeń (ankieta, przyjęty, lekcja odblokowana) | otwarty albo nowy zestaw: `{draw_id, questions: [{id, text, answers}], pool_size, form}` — **bez klucza i wyjaśnień** | 403 `SURVEY_REQUIRED` / `ENROLLMENT_REQUIRED` / `LESSON_LOCKED`, 404 `QUIZ_NOT_FOUND` / `LESSON_NOT_FOUND`, 403 `FORBIDDEN` (inne role) |
| `POST /lessons/{id}/quiz/attempts` | uczeń | `{draw_id, answers: {question_id: answer_id}}` → `AttemptResponse` | 409 `DRAW_NOT_OPEN`, 400 `QUIZ_INCOMPLETE` / `QUIZ_ANSWER_MISMATCH`, 403 jak wyżej |

`AttemptResponse`: `draw_id`, `percent`, `correct_count`, `total`, `passed`, `results`: [{`question_id`, `text`, `answers`, `chosen_answer_id`, `correct_answer_id`, `correct`, `explanation`}], `feedback`: `QuizFeedback` (`moduly/04-learning-style.md`). `form` w `GET` = forma, w której wynik zostanie zapisany (wybór lekcji albo aktywny styl).

## Frontend
- `features/assessment`:
  - `LessonQuiz` („Sprawdź się” na końcu lekcji ucznia): 5 pytań (`RadioGroup`), „Sprawdź” po odpowiedzi na wszystkie; wynik słownie i liczbowo (`quizScoreText`), `QuizReview` (przy każdym pytaniu wybrana i poprawna odpowiedź + wyjaśnienie), `QuizFeedbackPanel` z `learning-style` („Co to zmieniło”, pochwała, sugestia z przyciskiem „Przerób tę lekcję w formie X”, propozycja, okres próbny), „Rozwiąż jeszcze raz” (`resetQueries` klucza quizu → nowe losowanie); ostatni wynik w lekcji z `study.last_result`.
  - `QuizPoolPreview` (podgląd lekcji autora i admina): pula z poprawnymi odpowiedziami i wyjaśnieniami, bez rozwiązywania.
  - `hooks.ts`: zestaw ucznia `["lessons", id, "quiz"]` (`QUIZ_NOT_FOUND` → brak quizu); wysłanie unieważnia quiz, profil, `study`, lekcję, kurs (stany lekcji), listę kursów i `["me"]` (postępy, dziennik); pula `["lessons", id, "quiz-edit"]`, zapis i usunięcie unieważniają `["lessons", id, "readiness"]`.
- Edytor puli: zakładka „Quiz (pula)” edytora lekcji — `teach/PoolEditor` (pytania z odpowiedziami, poprawną i wyjaśnieniem; licznik „8 pytań w puli (min. 5)”; te same reguły walidacji co serwer przed zapisem). Stary adres `/teach/courses/[courseId]/lessons/[lessonId]/quiz` przekierowuje na `?tab=quiz`.

## Testy
`backend/tests/assessment/`:
- `test_drawing.py`: pierwsze losowanie 5 różnych, powtórka preferuje pytania spoza ostatniego zestawu, duża pula — same nowe, pula 5 — cała, pula < 5 — wszystkie, determinizm z ziarnem, tasowanie, domyślny generator.
- `test_grading.py`: liczenie poprawnych, komplet poprawnych / błędnych, niepasujące odpowiedzi, brak pytań.
- `test_quiz_api.py`: zapis i odczyt puli z wyjaśnieniami, pusta pula w edytorze, admin czyta, tylko autor edytuje, walidacja, szkic z małą pulą i usunięciem, opublikowana lekcja zachowuje pełną pulę; uczeń dostaje 5 pytań bez klucza, ten sam otwarty zestaw po odświeżeniu, inne pytania przy powtórce, warunki (ankieta, zapis, odblokowanie), inne role, lekcja bez puli, nieopublikowana lekcja → 404, wynik z wyjaśnieniami, zestaw wysyłany raz, cudzy zestaw / inna lekcja, odpowiedzi spoza zestawu, pula zmieniona po losowaniu, nieaktualny otwarty zestaw zastąpiony.
- Przebieg wyniku w modelu ucznia: `tests/learning_style/test_adaptation_flow.py`.

## Jak sprawdzić ręcznie
`uczen.demo@imsu.pl`: Matematyka → lekcja 3 → „Sprawdź się” (5 pytań) → F5: te same pytania → odpowiedzi → wynik z wyjaśnieniami i „Co to zmieniło” → „Rozwiąż jeszcze raz”: co najmniej 3 nowe pytania (pula 8), wynik powtórki w tej samej formie „procenty bez zmian”. `nauczyciel.demo@imsu.pl`: edytor lekcji → „Quiz (pula)” → usunięcie pytań do 4 w opublikowanej lekcji i zapis → komunikat o brakującym pytaniu.

## Ograniczenia
Tylko pytania jednokrotnego wyboru; quiz zawsze na końcu lekcji; przy puli 8 powtórka zawiera 2 pytania z poprzedniego zestawu (uczeń zna ich wyjaśnienia) — patrz „druga szansa” w `moduly/04-learning-style.md`; zmiana puli unieważnia otwarte zestawy uczniów zawierające usunięte pytania.
