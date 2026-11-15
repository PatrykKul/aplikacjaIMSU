# Moduł `assessment`

Quiz lekcji: pula pytań z wyjaśnieniami, losowanie 5 pytań na podejście, ocenianie na serwerze, przekazanie wyniku do modelu ucznia. Decyzje: D29, D43, D49 (część quizu).

## Odpowiedzialność
- Jedna **pula pytań** na lekcję (JSONB), zapis w całości przez autora; administrator ją czyta.
- Losowanie zestawu dla ucznia (R9, `drawing.py`), zapis zestawu na serwerze (`quiz_draws`) — klucz odpowiedzi i wyjaśnienia nie trafiają do przeglądarki przed wysłaniem.
- Ocena **tylko wobec wylosowanego zestawu** (`grading.py`) i przekazanie wyniku do modelu ucznia **wyłącznie** przez `learning_style.hooks.record_quiz_result` (nie ma endpointu, przez który przeglądarka zgłasza wynik). Forma wyniku = forma lekcji w chwili wysłania.
- Gotowość puli do publikacji (R11, `readiness.py`).
- Statystyki pytań (`stats.py`): „Do powtórki” dla ucznia i analiza pytań dla autora — z wysłanych zestawów (`quiz_draws.answers`), bez nowych tabel.
- Korzysta z `curriculum.service` (`get_study_lesson`, `get_owned_lesson`, `get_visible_lesson`, `get_owned_course`, `list_courses`, `is_accepted`, `published_lessons`, `accepted_student_ids`), `learning_style.service` (`require_style`, `require_student`, `lesson_form`, `now`) i stałych / pomocniczych funkcji `learning_style.rules` (`QUIZ_SIZE`, `rate`). Interfejs dla innych: `question_count(db, lesson_id)` (dla `authoring`), `current_draw`, `submit_attempt`, `save_quiz` (seed), `rng` (źródło losowości — seed i testy podstawiają `random.Random(seed)`).

## Model danych

| Tabela | Kolumny |
|---|---|
| `lesson_quizzes` | `id`, `lesson_id` → `lessons` (CASCADE, unikalny), `questions` (JSONB), `updated_at` |
| `quiz_draws` | `id`, `user_id` → `users` (CASCADE), `lesson_id` → `lessons` (CASCADE), `question_ids` (JSONB, w kolejności pokazania), `answers` (JSONB `{question_id: answer_id}`, null do wysłania), `percent` (0–100, null do wysłania), `form` (`V` / `A` / `K`, `CHECK`; forma lekcji przy losowaniu, null w zestawach sprzed `7d2e9b4c1a35`), `created_at`, `submitted_at` (null = podejście otwarte); indeks (`user_id`, `lesson_id`) |

Migracje `2e7cf4c0d9fc`, `01324f58656d` (pytania v2 bez wyjaśnień usunięte, nowa tabela `quiz_draws`), `7d2e9b4c1a35` (`quiz_draws.form`). Wynik w modelu ucznia (`quiz_results`) zapisuje `learning_style`.

Pytanie (`schemas.QuizQuestion`): `id` (`[A-Za-z0-9_-]{1,40}`), `text` (1–500), `answers` (3–4: `id`, `text` 1–200, unikalne `id`), `correct_answer_id` (jedna z odpowiedzi), **`explanation`** (1–1000, wymagane). Pula: 1–50 pytań (`MAX_QUESTIONS`), unikalne `id`; do publikacji lekcji ≥ 5 (`QUIZ_SIZE`). Pytania nie mają formy — quiz jest wspólny dla trzech wersji.

## Logika

### R9. Losowanie — `drawing.draw_questions(pool_ids, last_ids, k=5, rng)`
- Najpierw losowo pytania spoza **ostatniego wysłanego** zestawu, potem uzupełnienie losowo z tego zestawu; razem `min(k, len(pool))`; wybrane pytania tasowane (powtórzone nie są zawsze na końcu).
- Przykłady: pula 8, poprzedni zestaw 5 → powtórka daje 3 nowe + 2 z poprzedniego; pula 10 → 5 nowych; pula 5 → zawsze cała pula. `rng` wstrzykiwany (testy deterministyczne).

### Zestaw (`service.current_draw`)
- Otwarty zestaw ucznia w lekcji jest zwracany ponownie — odświeżenie strony nie losuje od nowa.
- Zestaw ma formę (`quiz_draws.form` = forma lekcji przy losowaniu, D61). Otwarty zestaw innej formy niż bieżąca forma lekcji (uczeń zmienił formę albo styl) jest usuwany i losowany nowy (pytania spoza ostatniego **wysłanego** zestawu, jak zawsze). Zestaw bez formy (sprzed migracji) zostaje. Ocena bez zmian: wynik dostaje formę lekcji z chwili wysłania.
- Otwarty zestaw z pytaniem, którego nie ma już w puli (autor zmienił pulę), jest usuwany i losowany nowy; wysłanie takiego zestawu → `409 DRAW_NOT_OPEN` (zestaw usunięty, następny `GET` losuje).
- Po wysłaniu (`submitted_at`) zestaw jest zamknięty: drugie wysłanie, cudzy zestaw albo zestaw innej lekcji → `409 DRAW_NOT_OPEN`.

### Ocena — `grading.grade(questions, answers)`
- Odpowiedzi muszą dotyczyć dokładnie pytań zestawu (`400 QUIZ_INCOMPLETE`), każda odpowiedź musi należeć do pytania (`400 QUIZ_ANSWER_MISMATCH`). `percent = round(100 · poprawne / wszystkie)`; przy 5 pytaniach 0 / 20 / 40 / 60 / 80 / 100%.
- Zaliczenie: `percent >= 70` (`learning_style.rules.PASS_THRESHOLD`) — od 4 z 5. Podejść bez limitu.
- Po ocenie: zapis `answers`, `percent`, `submitted_at`, potem `record_quiz_result` (R2–R7, odblokowanie lekcji; `moduly/04-learning-style.md`).

### Statystyki pytań (`stats.py`, czyste funkcje)
Odpowiedzi z wysłanych zestawów sprawdzane są wobec **bieżącej** puli: pytanie usunięte z puli wypada, zmieniony klucz zmienia, co jest poprawne. Udziały: `learning_style.rules.rate` (połówka w górę); poniżej progu `null` razem z liczebnością (`drawn`).

| Stała | Wartość | Znaczenie |
|---|---|---|
| `QUESTION_MIN_DRAWS` | 5 | analiza pytań: `correct_percent`, `top_wrong.percent`, `rating` |
| `HARD_BELOW` / `EASY_ABOVE` | 40 / 90 | ocena pytania: `hard` (< 40), `easy` (> 90), inaczej `normal` |
| `REVIEW_LIMIT` | 5 | „Do powtórki”: najwyżej tyle pytań |

Stałe powtórzone we frontendzie (`explain.ts`).

- `question_stats(questions, draws)` (autor) — dla każdego pytania puli: `drawn` (w ilu wysłanych zestawach), `correct` (ile razy dobrze), `correct_percent` (`null`, gdy `drawn < 5`), `top_wrong` — najczęściej wybrana zła odpowiedź {`answer_id`, `text`, `count`, `percent` = `count / drawn` (`null`, gdy `drawn < 5`)}, remis → kolejność odpowiedzi w pytaniu, `null`, gdy nikt nie odpowiedział źle; `rating` (`null`, gdy `drawn < 5`). Kolejność: `correct_percent` rosnąco, bez procentu na końcu, potem kolejność w puli.
  - Przykład: pytanie w 5 zestawach, 2 razy dobrze, „B” wybrane 2 razy → `correct_percent` 40, `normal`, `top_wrong` B (2, 40%); w 6 zestawach 2 razy dobrze → 33, `hard`; zawsze dobrze → 100, `easy`, `top_wrong = null`.
- `review_questions(lessons, pools, draws)` (uczeń) — dla każdej lekcji **ostatni wysłany zestaw** (`submitted_at`, potem `id`); pytania odpowiedziane w nim źle i nadal obecne w puli. Najnowsze zestawy pierwsze, w zestawie kolejność pokazania; najwyżej 5. Pomijane: pytanie spoza puli, wybrana odpowiedź usunięta przez autora (nie ma czego pokazać), odpowiedź poprawna według bieżącego klucza. Poprawne kolejne podejście „czyści” lekcję.

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
| `GET /me/review-questions` | uczeń | `ReviewQuestionResponse[]` (maks. 5) — tylko opublikowane lekcje kursów, na które uczeń jest przyjęty | 403 `FORBIDDEN` (inne role) |
| `GET /courses/{id}/question-stats` | autor (zatwierdzony) | `[{lesson_id, title, number, questions: QuestionStatsRow[]}]` — opublikowane lekcje w kolejności kursu, zestawy uczniów obecnie przyjętych | 404 `COURSE_NOT_FOUND` (także cudzy kurs), 403 `FORBIDDEN` / `TEACHER_NOT_APPROVED` |

`AttemptResponse`: `draw_id`, `percent`, `correct_count`, `total`, `passed`, `results`: [{`question_id`, `text`, `answers`, `chosen_answer_id`, `correct_answer_id`, `correct`, `explanation`}], `feedback`: `QuizFeedback` (`moduly/04-learning-style.md`). `form` w `GET` = forma, w której wynik zostanie zapisany (wybór lekcji albo aktywny styl).

`ReviewQuestionResponse`: `course_id`, `course_title`, `lesson_id`, `lesson_title`, `number`, `question_id`, `text`, `chosen_answer` {`id`, `text`}, `correct_answer` {`id`, `text`}, `explanation`, `answered_at` (`submitted_at` zestawu). `QuestionStatsRow`: `question_id`, `text`, `drawn`, `correct`, `correct_percent`, `top_wrong` {`answer_id`, `text`, `count`, `percent`} / null, `rating` (`hard` / `easy` / `normal` / null).

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
- `test_quiz_api.py`: zapis i odczyt puli z wyjaśnieniami, pusta pula w edytorze, admin czyta, tylko autor edytuje, walidacja, szkic z małą pulą i usunięciem, opublikowana lekcja zachowuje pełną pulę; uczeń dostaje 5 pytań bez klucza, ten sam otwarty zestaw po odświeżeniu, inne pytania przy powtórce, warunki (ankieta, zapis, odblokowanie), inne role, lekcja bez puli, nieopublikowana lekcja → 404, wynik z wyjaśnieniami, zestaw wysyłany raz, cudzy zestaw / inna lekcja, odpowiedzi spoza zestawu, pula zmieniona po losowaniu, nieaktualny otwarty zestaw zastąpiony, zestaw zapisuje formę, zmiana formy lekcji przy otwartym zestawie losuje nowy (powrót do tej samej formy — bez zmian).
- `test_stats.py` (czyste funkcje): stałe, granice oceny (39 / 40 / 90 / 91), liczby pytania i najczęstsza zła odpowiedź, próg 5 zestawów, remis złych odpowiedzi w kolejności pytania, brak złych odpowiedzi, kolejność (procent rosnąco, remis według puli, bez danych na końcu), pytania spoza puli; do powtórki: pola, ostatni wysłany zestaw lekcji, poprawne podejście czyści lekcję, najnowsze pierwsze i kolejność w zestawie, limit 5, pytanie usunięte / odpowiedź usunięta / zmieniony klucz, tylko podane lekcje, lekcja bez puli.
- `test_stats_api.py`: „Do powtórki” przez API (pola, ostatni zestaw, najnowsze pierwsze, tylko własne pytania, kurs po odrzuceniu ucznia znika, tylko uczeń); analiza pytań (kolejność lekcji i pytań, liczby i ocena, zła odpowiedź z procentem, próg 5 zestawów, uczeń odrzucony nie liczy się) i dostęp (cudzy kurs 404, uczeń i admin 403 `FORBIDDEN`, brak kursu 404, niezatwierdzony nauczyciel 403 `TEACHER_NOT_APPROVED`).
- Przebieg wyniku w modelu ucznia: `tests/learning_style/test_adaptation_flow.py`.

## Jak sprawdzić ręcznie
`uczen.demo@imsu.pl`: Matematyka → lekcja 3 → „Sprawdź się” (5 pytań) → F5: te same pytania → odpowiedzi → wynik z wyjaśnieniami i „Co to zmieniło” → „Rozwiąż jeszcze raz”: co najmniej 3 nowe pytania (pula 8), wynik powtórki w tej samej formie „procenty bez zmian”. `nauczyciel.demo@imsu.pl`: edytor lekcji → „Quiz (pula)” → usunięcie pytań do 4 w opublikowanej lekcji i zapis → komunikat o brakującym pytaniu.

## Ograniczenia
Tylko pytania jednokrotnego wyboru; quiz zawsze na końcu lekcji; przy puli 8 powtórka zawiera 2 pytania z poprzedniego zestawu (uczeń zna ich wyjaśnienia) — patrz „druga szansa” w `moduly/04-learning-style.md`; zmiana puli unieważnia otwarte zestawy uczniów zawierające usunięte pytania; zmiana formy lekcji porzuca otwarty zestaw (uczeń może zobaczyć część jego pytań przed nowym losowaniem). Statystyki pytań oceniają stare odpowiedzi według bieżącego klucza — po zmianie poprawnej odpowiedzi liczby pytania mieszają dwie wersje; powtórki tego samego ucznia liczą się jako kolejne zestawy.
