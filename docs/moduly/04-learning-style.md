# Moduł `learning_style`

Model ucznia: ankieta VAK, styl i wagi, personalizacja lekcji, adaptacja po quizie, propozycja zmiany stylu. Decyzje: D3 (wyjątek), D16–D19, D29, D31. Logika przejęta w uproszczeniu z wersji 1 (tag `v1-final`: `vak.py`, `personalizacja.py`, `adaptacja.py`).

Stan: po etapie 4. Etap 5 (w toku, `08-praca-biezaca.md`) zmienia ukrywanie na zwijanie i dodaje styl efektywny lekcji — po jego zakończeniu ten opis zostanie zaktualizowany.

## Odpowiedzialność
- Ankieta: pytania, wynik, historia; ankieta wymagana dla ucznia.
- Profil ucznia: styl, źródło stylu, wagi, odrzucona propozycja; ręczna zmiana i powrót do ankiety.
- Personalizacja bloków lekcji (na bazie `content.service.get_blocks`) z uzasadnieniem.
- Adaptacja: zapis prób quizu, zmiana wag, propozycja zmiany stylu.
- Punkt styku dla `assessment`: `hooks.record_quiz_result(db, user=, lesson_id=, block_id=, percent=) -> QuizFeedback | None` (zapisuje próbę, robi `commit`; `None` dla nauczyciela, administratora i ucznia bez ankiety).

## Model danych

Migracje: `ea197399889b` (tabele + 20 pytań z v1), `c3a91f2d7b40` (teksty neutralne płciowo — zmienia tylko wiersze o oczekiwanej treści, odwracalna).

| Tabela | Kolumny | Uwagi |
|---|---|---|
| `survey_questions` | `id`, `text` (300), `position`, `is_active` | |
| `survey_answers` | `id`, `question_id`, `text`, `style` (V / A / K), `position` | 3 odpowiedzi na pytanie |
| `survey_results` | `id`, `user_id`, `points_v/a/k`, `dominant_style`, `created_at` | każde wypełnienie to nowy wiersz |
| `learning_profiles` | `user_id` (PK), `style`, `style_source` (`survey` / `manual` / `adaptation`), `weight_v/a/k` (0–30), `rejected_proposal`, `updated_at` | brak wiersza = ankieta niewypełniona |
| `quiz_attempts` | `id`, `user_id`, `lesson_id`, `block_id` (`quiz-<id>`), `percent`, `style`, `counted_for_weights`, `created_at` | indeks (`user_id`, `lesson_id`) |

`style`: jedna lub kilka liter w kolejności V, A, K (`V`, `VA`, `VAK`).

## Logika (czyste funkcje)

| Plik | Reguły |
|---|---|
| `scoring.py` | punkt dla stylu za odpowiedź; styl = style z maksimum punktów (remis → kilka liter); walidacja zapisu stylu |
| `personalization.py` | tekst zawsze widoczny; załącznik widoczny, gdy jego `forms` ma wspólną literę ze stylem; kolejność nauczyciela; zdanie „dlaczego to widzisz” zależne od źródła stylu |
| `adaptation.py` | wagi startowe = punkty ankiety (0–30); quiz ≥ 70% = sukces → litery stylu +1, porażka −1; w lekcji liczy się tylko pierwszy sukces i pierwsza porażka dla danego stylu; propozycja, gdy jedna forma prowadzi samodzielnie i nie należy do stylu — nie przy stylu ręcznym ani po odrzuceniu tej propozycji; teksty propozycji i uzasadnień |

Serwis: nowa ankieta ustawia styl i wagi od nowa i czyści odrzuconą propozycję; ręczna zmiana nie usuwa wyników ankiety; przyjęcie propozycji → źródło `adaptation`.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /survey/questions` | zalogowany | aktywne pytania **bez klucza** | |
| `POST /survey/answers` | uczeń | `{answers: [{question_id, answer_id}]}` → profil | 409 `SURVEY_EMPTY`; 400 `SURVEY_INCOMPLETE`, `SURVEY_DUPLICATE_ANSWER`, `SURVEY_ANSWER_MISMATCH`; 403 dla innych ról |
| `GET /survey/results` | uczeń | historia wyników, od najnowszego | |
| `GET /profile/learning-style` | zalogowany | `survey_completed`, `style`, `style_source`, `weights`, `last_result`, `explanation`, `proposal` (`style`, `message`, `why`) | |
| `PUT /profile/learning-style` | uczeń | `{style}` → styl ręczny | 403 `SURVEY_REQUIRED`, 422 |
| `DELETE /profile/learning-style` | uczeń | powrót do stylu z ostatniej ankiety | 403 `SURVEY_REQUIRED` |
| `POST /profile/learning-style/proposal/accept` / `reject` | uczeń | przyjęcie / odrzucenie propozycji | 409 `NO_PROPOSAL` |
| `GET /lessons/{id}/personalized-blocks` | zalogowany | uczeń: bloki pasujące do stylu, `style`, `hidden_count`, `explanation`; nauczyciel / admin: wszystkie, `style: null` | 403 `SURVEY_REQUIRED`, 404 jak lekcja |

## Frontend (`features/learning-style`)
- `SurveyGate` w layoutach `(app)` i `(focus)`: uczeń bez ankiety → `/survey` (inne role przechodzą).
- `/survey` — `SurveyForm` (pasek postępu, deterministycznie mieszane odpowiedzi, przewinięcie do brakującego pytania); `/survey/result` — `SurveyResult` (styl, opis, punkty jako `StyleBars`); `/profile` („Mój styl”) — `LearningStylePanel` (styl i źródło, uzasadnienie, wagi, ręczna zmiana, powrót do ankiety, ponowna ankieta, historia).
- `StyleProposalBanner` („Przełącz” / „Zostaję przy swoim”, „Dlaczego to widzisz”) w profilu i nad lekcją; `PersonalizationNote` nad lekcją; `AdaptationFeedback` w wyniku quizu.
- `hooks.ts`: profil (klucz `["learning-style", "profile"]`), pytania, wyniki, spersonalizowane bloki; mutacje profilu zapisują odpowiedź i odświeżają pozostałe zapytania featura. `errors.ts`: kody modułu → komunikaty.

## Testy
`backend/tests/learning_style/`: punktacja i remisy, walidacja stylu; personalizacja; adaptacja (wagi, zakres, pierwszy sukces / porażka, propozycja, styl ręczny, odrzucenie, teksty); API ankiety (20 pytań, brak klucza, błędy, historia, role), profilu (ręczny styl, powrót, propozycje), spersonalizowanych bloków (filtrowanie, `SURVEY_REQUIRED`, podgląd nauczyciela, 404); hook quizu; brak form męskich w ankiecie.

## Jak sprawdzić ręcznie
`uczen.nowy@imsu.pl` (moduł `demo`): wymuszenie ankiety (także z `/courses`) → ankieta → wynik → lekcja „Wzór i wykres funkcji liniowej” (uzasadnienie, materiały stylu) → „Mój styl”: zmiana ręczna i powrót do ankiety. `uczen.demo@imsu.pl`: baner propozycji A z uzasadnieniem wag → „Przełącz” → lekcja z materiałami słuchowymi.

## Ograniczenia
- Materiały innych stylów są ukryte, a `GET /lessons/{id}/blocks` zwraca uczniowi wszystkie bloki (personalizacja w widoku) — etap 5.
- Wagi zmieniają się tylko dla liter stylu ucznia, więc propozycja wynika głównie ze spadku wag własnego stylu — etap 5 (styl efektywny).
- Moduł zwraca gotowe polskie zdania (`explanation`, `message`, `why`) — wyjątek od D3.
