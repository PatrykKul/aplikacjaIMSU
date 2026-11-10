# Moduł `learning_style`

Model ucznia: ankieta VAK, styl i wagi, personalizacja lekcji, adaptacja po quizie, propozycja zmiany stylu. Decyzje: D3 (wyjątek), D16–D19, D29, D31. Logika przejęta w uproszczeniu z wersji 1 (tag `v1-final`: `vak.py`, `personalizacja.py`, `adaptacja.py`).

## Odpowiedzialność
- Ankieta: pytania, wynik, historia; ankieta wymagana dla ucznia.
- Profil ucznia: styl, źródło stylu, wagi, odrzucona propozycja; ręczna zmiana i powrót do ankiety.
- Personalizacja lekcji (na bazie `content.service.get_blocks`): materiały innych stylów zwinięte w miejscu, uzasadnienie; zapis pierwszego rozwinięcia zwiniętego materiału.
- **Styl efektywny lekcji** = styl ucznia + formy rozwiniętych w tej lekcji materiałów (`service.lesson_style`); używają go adaptacja i `assessment` (dobór pytań).
- Adaptacja: zapis prób quizu, zmiana wag, propozycja zmiany stylu.
- Punkt styku dla `assessment`: `hooks.record_quiz_result(db, user=, lesson_id=, block_id=, percent=) -> QuizFeedback | None` (zapisuje próbę, robi `commit`; `None` dla nauczyciela, administratora i ucznia bez ankiety).

## Model danych

Migracje: `ea197399889b` (tabele + 20 pytań z v1), `c3a91f2d7b40` (teksty neutralne płciowo — zmienia tylko wiersze o oczekiwanej treści, odwracalna), `f3c3eff41f5a` (`material_openings`).

| Tabela | Kolumny | Uwagi |
|---|---|---|
| `survey_questions` | `id`, `text` (300), `position`, `is_active` | |
| `survey_answers` | `id`, `question_id`, `text`, `style` (V / A / K), `position` | 3 odpowiedzi na pytanie |
| `survey_results` | `id`, `user_id`, `points_v/a/k`, `dominant_style`, `created_at` | każde wypełnienie to nowy wiersz |
| `learning_profiles` | `user_id` (PK), `style`, `style_source` (`survey` / `manual` / `adaptation`), `weight_v/a/k` (0–30), `rejected_proposal`, `updated_at` | brak wiersza = ankieta niewypełniona |
| `quiz_attempts` | `id`, `user_id`, `lesson_id`, `block_id` (`quiz-<id>`), `percent`, `style` (styl efektywny w chwili próby), `counted_for_weights`, `created_at` | indeks (`user_id`, `lesson_id`) |
| `material_openings` | `id`, `user_id`, `lesson_id`, `block_id`, `forms` (formy materiału, kolejność V, A, K), `created_at` | unikalne (`user_id`, `lesson_id`, `block_id`) — rozwinięcie zapisuje się raz |

`style`: jedna lub kilka liter w kolejności V, A, K (`V`, `VA`, `VAK`).

## Logika (czyste funkcje)

| Plik | Reguły |
|---|---|
| `scoring.py` | punkt dla stylu za odpowiedź; styl = style z maksimum punktów (remis → kilka liter); walidacja zapisu stylu |
| `personalization.py` | `matches_style`: tekst zawsze, załącznik — gdy jego `forms` ma wspólną literę ze stylem; `collapsed_ids`: niepasujące załączniki w kolejności nauczyciela; `effective_style`: styl + formy rozwiniętych materiałów (litery V, A, K); zdanie „dlaczego to widzisz” zależne od źródła stylu |
| `adaptation.py` | wagi startowe = punkty ankiety (0–30); quiz ≥ 70% = sukces → litery **stylu efektywnego** +1, porażka −1; w lekcji liczy się tylko pierwszy sukces i pierwsza porażka dla danego stylu efektywnego; propozycja, gdy jedna forma prowadzi samodzielnie i nie należy do stylu ucznia — nie przy stylu ręcznym ani po odrzuceniu tej propozycji; teksty: „Wagi wskazują na materiały słuchowe – przełączyć?” i uzasadnienie z wagami |

Serwis: nowa ankieta ustawia styl i wagi od nowa i czyści odrzuconą propozycję; ręczna zmiana nie usuwa wyników ankiety; przyjęcie propozycji → źródło `adaptation`. Rozwinięcie zapisuje się tylko dla zwiniętego załącznika (tekst i materiał własnego stylu — bez zapisu); formy bierze serwer z bloku. Rozwinięcia sprzed próby wpływają na tę próbę, późniejsze — na kolejne.

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
| `GET /lessons/{id}/personalized-blocks` | zalogowany | wszystkie bloki, `style`, `collapsed_block_ids` (załączniki do zwinięcia), `opened_block_ids` (już rozwinięte), `explanation`; nauczyciel / admin: listy puste, `style: null` | 403 `SURVEY_REQUIRED`, 404 jak lekcja |
| `POST /lessons/{id}/blocks/{block_id}/open` | uczeń | zapis pierwszego rozwinięcia zwiniętego materiału, 204 (powtórka i materiał niezwinięty — bez zmian) | 403 `SURVEY_REQUIRED`, 403 `FORBIDDEN` (inne role), 404 `BLOCK_NOT_FOUND`, 404 jak lekcja |

## Frontend (`features/learning-style`)
- `SurveyGate` w layoutach `(app)` i `(focus)`: uczeń bez ankiety → `/survey` (inne role przechodzą).
- `/survey` — `SurveyForm` (pasek postępu, deterministycznie mieszane odpowiedzi, przewinięcie do brakującego pytania); `/survey/result` — `SurveyResult` (styl, opis, punkty jako `StyleBars`); `/profile` („Mój styl”) — `LearningStylePanel` (styl i źródło, uzasadnienie, wagi, ręczna zmiana, powrót do ankiety, ponowna ankieta, historia).
- `StyleProposalBanner` („Przełącz” / „Zostaję przy swoim”, „Dlaczego to widzisz”) w profilu i nad lekcją; `PersonalizationNote` nad lekcją (styl, uzasadnienie, „N materiałów dla innych stylów jest zwiniętych – możesz je rozwinąć”); `AdaptationFeedback` w wyniku quizu.
- `CollapsedMaterial`: zwinięty załącznik w miejscu (ikona, rodzaj, tytuł, „Pokaż materiał”); używa go `courses/components/LessonView` — pierwsze rozwinięcie wywołuje `useOpenMaterial` i odświeża quiz lekcji (`lessonQuizKey` z `assessment`); rozwinięty materiał można zwinąć („Zwiń materiał”, tylko w widoku), zapisane rozwinięcia są rozwinięte po odświeżeniu.
- `hooks.ts`: profil (klucz `["learning-style", "profile"]`), pytania, wyniki, spersonalizowane bloki, `useOpenMaterial`; mutacje profilu zapisują odpowiedź i odświeżają pozostałe zapytania featura. `errors.ts`: kody modułu → komunikaty.

## Testy
`backend/tests/learning_style/`: punktacja i remisy, walidacja stylu; personalizacja; adaptacja (wagi, zakres, pierwszy sukces / porażka, propozycja, styl ręczny, odrzucenie, teksty); API ankiety (20 pytań, brak klucza, błędy, historia, role), profilu (ręczny styl, powrót, propozycje), spersonalizowanych bloków (zwinięte i rozwinięte, `SURVEY_REQUIRED`, podgląd nauczyciela, 404); rozwinięcia (zapis raz, bez zapisu dla tekstu i własnego stylu, 404, role, styl efektywny w adaptacji, rozwinięcia tylko w swojej lekcji); styl efektywny (czyste funkcje); hook quizu; brak form męskich w ankiecie.

## Jak sprawdzić ręcznie
`uczen.nowy@imsu.pl` (moduł `demo`): wymuszenie ankiety (także z `/courses`) → ankieta → wynik → lekcja „Wzór i wykres funkcji liniowej” (uzasadnienie, materiały stylu) → „Mój styl”: zmiana ręczna i powrót do ankiety. `uczen.demo@imsu.pl` (styl V): lekcja „Wzór i wykres funkcji liniowej” — 3 materiały zwinięte, w quizie pytanie V → „Pokaż materiał” przy nagraniu → w quizie pytanie A → F5: nagranie nadal rozwinięte; baner propozycji A z uzasadnieniem wag → „Przełącz” → materiały słuchowe rozwinięte.

## Ograniczenia
- Rozwinięcie nie oznacza, że uczeń z materiału skorzystał — liczy się tylko w połączeniu z wynikiem quizu.
- Uczeń, który nie rozwija materiałów innych stylów, zmienia tylko wagi własnego stylu; propozycja wynika wtedy ze spadku tych wag.
- Moduł zwraca gotowe polskie zdania (`explanation`, `message`, `why`) — wyjątek od D3.
