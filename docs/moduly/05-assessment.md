# Moduł `assessment`

Quiz lekcji: pytania, ocenianie na serwerze, edytor quizu. Decyzje: D11, D15, D29; odroczone: O5 (baza pytań z losowaniem).

Stan: po etapie 4. Etap 5 (w toku, `08-praca-biezaca.md`) dobiera pytania do stylu efektywnego lekcji.

## Odpowiedzialność
- Jeden quiz na lekcję (pytania w JSONB), zapis w całości przez autora kursu.
- Wybór pytań dla ucznia i ocenianie (czyste funkcje w `grading.py`).
- Przekazanie wyniku do modelu ucznia **tylko** przez `learning_style.hooks.record_quiz_result` — nie ma endpointu, przez który przeglądarka zgłasza wynik.
- Dostęp jak do lekcji: `curriculum.service.get_visible_lesson` / `get_owned_lesson`.

## Model danych

`lesson_quizzes`: `id`, `lesson_id` (unikalny), `questions` (JSONB), `updated_at`. Migracja `2e7cf4c0d9fc`.

Pytanie: `id` (`[A-Za-z0-9_-]{1,40}`), `text` (≤ 500), `form` (V / A / K albo brak = pytanie wspólne), `answers` (3–4: `id`, `text` ≤ 200), `correct_answer_id` (jedna z odpowiedzi). Quiz: 1–20 pytań, unikalne identyfikatory pytań i odpowiedzi.

## Logika (`grading.py`)
- Uczeń dostaje pytania wspólne i pytania o formy swojego stylu (`visible_questions`); nauczyciel / administrator — wszystkie.
- Odpowiedzi muszą dokładnie odpowiadać widocznym pytaniom; wynik = poprawne / wszystkie w procentach (zaokrąglony).
- Próg zaliczenia 70% (w `learning_style.adaptation`); bez limitu podejść; po podejściu odpowiedź zawiera poprawne odpowiedzi.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/quiz` | widzący lekcję | pytania **bez klucza** (uczeń: wybrane wg stylu, `hidden_count`) | 404 `QUIZ_NOT_FOUND` (brak quizu albo brak pytań dla stylu), 403 `SURVEY_REQUIRED` |
| `POST /lessons/{id}/quiz/attempts` | widzący lekcję | `{answers: {question_id: answer_id}}` → `percent`, `correct_count`, `total`, `results` (wybrana i poprawna odpowiedź), `adaptation` (`QuizFeedback` albo `null`) | 400 `QUIZ_INCOMPLETE`, `QUIZ_ANSWER_MISMATCH` |
| `GET /lessons/{id}/quiz/edit` | autor kursu | pytania z kluczem (pusta lista, gdy brak quizu) | 404 |
| `PUT /lessons/{id}/quiz` | autor kursu | zapis całości | 422, 404 |
| `DELETE /lessons/{id}/quiz` | autor kursu | usunięcie, 204 | 404 |

## Frontend (`features/assessment`)
- `LessonQuiz` pod blokami w `LessonView`: karta „Sprawdź się”, pytania z plakietką formy, wysyłka po odpowiedzi na wszystkie, wynik (poprawne / błędne zaznaczone, liczba i procent), `AdaptationFeedback`, „Rozwiąż jeszcze raz”; autor widzi „Dodaj quiz” / „Edytuj quiz”.
- `QuizEditor` na `/teach/courses/[courseId]/lessons/[lessonId]/quiz`: pytania z treścią, formą („Dotyczy materiału”), odpowiedziami i wyborem poprawnej; zapis, usunięcie, ostrzeżenie o niezapisanych zmianach.
- `hooks.ts`: quiz ucznia z **stylem w kluczu** (`["quiz", lessonId, style]`), po wysłaniu odświeżenie profilu; quiz do edycji `["quiz-edit", lessonId]`; zapis i usunięcie unieważniają quiz ucznia.

## Testy
`backend/tests/assessment/`: ocenianie i wybór pytań (czyste funkcje), uprawnienia edytora, walidacja treści, brak klucza w odpowiedzi ucznia, filtrowanie wg stylu, `SURVEY_REQUIRED`, integracja z adaptacją (wagi po quizie, powtórki bez zmiany wag, podgląd nauczyciela bez adaptacji).

## Jak sprawdzić ręcznie
Jako uczeń: lekcja demo → „Sprawdź się” (4 pytania: 3 wspólne + 1 o materiale stylu) → wynik i informacja o adaptacji → „Rozwiąż jeszcze raz” (wagi bez zmian). Jako nauczyciel: podgląd lekcji → „Edytuj quiz” → zmiana pytania i formy → „Zapisz quiz” → „Zapisano”.

## Ograniczenia
Stały zestaw pytań (kolejne podejście po zobaczeniu poprawnych odpowiedzi jest łatwe); uczniowie różnych stylów mają różne zestawy pytań; tylko pytania jednokrotnego wyboru; quiz zawsze na końcu lekcji.
