# Moduł `learning_style`

Model ucznia i silnik adaptacji: ankieta VAK, jeden aktywny styl i profil procentowy, wersja lekcji w formie ucznia, reguły po quizie (sugestia, propozycja zmiany stylu, okres próbny, podpowiedź z kursu), dziennik decyzji, statystyki ucznia i kursu. Decyzje: D29, D31, D41, D44, D45, D50, D51, D52, D57, D60–D62; D3 (bez wyjątku — backend zwraca kody i liczby).

Zasada: **każda reakcja systemu wynika z jednej czystej funkcji w `rules.py` i niesie liczby, z których wynika**; serwis tylko ładuje dane, zapisuje decyzję i wpis w dzienniku.

## Odpowiedzialność
- Ankieta (raz, D50), profil: aktywny styl (V, A albo K), źródło stylu, procenty V / A / K, historia procentów.
- Wersja lekcji dla ucznia (`/study`): forma lekcji = jawny wybór (`lesson_forms`) albo aktywny styl; bloki z `content.service.get_version`. **Forma równa aktywnemu stylowi to nie jawny wybór** (D57): `form_source = style`, liczone w chwili odpowiedzi (wiersz `lesson_forms` równy stylowi — np. wybór zostawiony w zaliczonej lekcji, a potem zmiana stylu na tę formę — nie daje `choice`); wybór formy równej stylowi usuwa wiersz.
- Wynik quizu w modelu ucznia (`quiz_results`) i reguły R2–R7 oraz R12 — jedyny punkt styku z `assessment`: `hooks.record_quiz_result`.
- Propozycje zmiany stylu, okresy próbne, ręczna zmiana stylu, rozstrzygnięcie remisu ankiety.
- Dziennik decyzji (`decision_events`) — uczeń i autor kursu go widzą.
- Statystyki: „Moje postępy” ucznia (podsumowanie, tabela form, seria porażek R12), podpowiedź z kursu (R8), panel kursu (statystyki lekcji, najtrudniejsza lekcja, macierz lekcja × forma) i szczegóły ucznia dla autora. Pytania do powtórki i analiza pytań należą do `assessment` (`moduly/05-assessment.md`).
- Interfejs dla innych modułów (`service.py`): `require_style(db, user)` (uczeń ze stylem albo 403), `require_student(user)` (uczeń albo 403), `lesson_form(db, user_id, lesson_id, style) -> (form, source)`, `now()` (czas zapisu); dla `assessment`: `hooks.record_quiz_result(db, user=, lesson=, draw_id=, percent=) -> QuizFeedback`.
- Korzysta z `curriculum.service` (`get_study_lesson`, `get_visible_course`, `get_owned_course`, `is_accepted`, `mark_lesson_passed`, `passed_lesson_ids`, `published_lessons`, `course_progress`, `accepted_student_ids`, `lesson_number`, `pending_request_count`, `list_courses`), `content.service.get_version` i `identity.service.get_users`. Wyjątek od zasad zależności: tytuły lekcji i kursów czyta po kluczu przez modele `Lesson` / `Course` (dowód decyzji i dziennik pokazują tytuły).

## Model danych

Migracje: `ea197399889b` (ankieta + 20 pytań z v1), `c3a91f2d7b40` (teksty neutralne płciowo), `01324f58656d` (model v3; dane uczenia v2 usunięte, bez przenoszenia), `7d2e9b4c1a35` (`style_trials.result` = `cancelled`).

| Tabela | Kolumny | Uwagi |
|---|---|---|
| `survey_questions` | `id`, `text` (300), `position`, `is_active` | 20 pytań z migracji |
| `survey_answers` | `id`, `question_id` → (CASCADE), `text`, `style` (`V` / `A` / `K`, `CHECK`), `position` | 3 odpowiedzi na pytanie |
| `survey_results` | `id`, `user_id` (CASCADE), `points_v/a/k`, `dominant_style` (3 znaki: lider albo litery remisu, np. `VA`), `created_at` | jeden wiersz na ucznia (ankieta raz) |
| `learning_profiles` | `user_id` (PK, CASCADE), `style` (`V` / `A` / `K` albo `null` = remis nierozstrzygnięty), `style_source` (`survey` / `tie_choice` / `manual` / `proposal`), `percent_v/a/k`, `updated_at` | `CHECK`: każdy procent 5–90, suma 100; brak wiersza = ankieta niewypełniona |
| `style_history` | `id`, `user_id`, `percent_v/a/k`, `style`, `event_id` → `decision_events` (SET NULL), `created_at` | stan profilu po każdej zmianie (punkty wykresu); indeks (`user_id`, `created_at`) |
| `quiz_results` | `id`, `user_id`, `course_id` (indeks), `lesson_id`, `draw_id` → `quiz_draws` (SET NULL), `form`, `percent` (0–100), `passed`, `counted`, `created_at` | wynik w modelu ucznia (S z wykładu); indeks (`user_id`, `lesson_id`) |
| `lesson_forms` | `user_id`, `lesson_id` (PK razem), `form`, `updated_at` | jawny wybór formy lekcji; brak wiersza = forma = aktywny styl |
| `style_proposals` | `id`, `user_id`, `kind` (`switch` / `revert`), `from_style`, `to_style`, `evidence` (JSONB), `status` (`open` / `accepted` / `rejected` / `expired` / `superseded`), `counted_at_decision`, `created_at`, `decided_at` | częściowy indeks unikalny: najwyżej jedna `open` na ucznia |
| `style_trials` | `id`, `user_id`, `from_style`, `to_style`, `source` (`proposal` / `manual`), `before_average` (null = brak danych), `after_average`, `result` (`helped` / `neutral` / `worse` / `no_baseline` / `cancelled` / null), `started_at`, `finished_at` (null = trwa) | okres próbny (R7); `cancelled` — cofnięty albo zastąpiony przed pierwszą policzoną lekcją (R7a), null po zakończeniu — przerwany zmianą stylu po policzonych lekcjach |
| `decision_events` | `id`, `user_id` (CASCADE), `type` (40), `course_id` (SET NULL, indeks), `lesson_id` (SET NULL), `data` (JSONB), `created_at` | dziennik decyzji; indeks (`user_id`, `created_at`) |

Czas w nowych wierszach (`quiz_results`, `decision_events`, `style_history`, propozycje, okresy próbne, `quiz_draws.submitted_at`) ustawia `service.now()` = `clock_timestamp()`: wiersze jednego żądania mają różne czasy, a okres próbny porównuje czas wyniku z czasem startu.

## Reguły (`rules.py`, czyste funkcje)

Bez SQLAlchemy i FastAPI; wejście: `dict` i dataklasy (`Result`, `Rejection`, `CourseResult`), wyjście: decyzja z danymi. Arytmetyka dokładna (`Fraction`): procenty zaokrąglane **metodą największych reszt** (podłoga, brakujące jednostki dla największych części ułamkowych, remis reszt → V, A, K), średnie **połówka w górę** (`average`: 53,5 → 54). Przykłady poniżej sprawdzają testy (`test_rules.py`).

### Stałe
| Stała | Wartość | Znaczenie |
|---|---|---|
| `FORMS` | `("V", "A", "K")` | także kolejność rozstrzygania remisów |
| `PASS_THRESHOLD` | 70 | zaliczenie: `percent >= 70`; przy 5 pytaniach wynik 0/20/40/60/80/100%, zaliczenie od 4 z 5 |
| `STEP` | 10 | zmiana procentu formy po policzonym wyniku |
| `MIN_PERCENT` / `MAX_PERCENT` | 5 / 90 | każda forma ≥ 5, więc ≤ 90 |
| `QUIZ_SIZE` | 5 | pytań na podejście |
| `TRIAL_LESSONS` | 2 | długość okresu próbnego |
| `HELPED_GAIN` / `REVERT_DROP` | 10 / 10 | progi wyniku okresu próbnego (pkt proc.) |
| `RENEW_AFTER` | 2 | nowe policzone wyniki, po których wraca odrzucona propozycja |
| `HINT_MIN_STUDENTS` | 2 | podpowiedź z kursu: min. uczniów w formie |
| `ATTENTION_STREAK` | 3 | seria porażek: kolejne niezaliczone policzone wyniki (R12) |

`rate(part, whole)` — udział w procentach zaokrąglany połówką w górę jak `average` (1/8 → 13); używają go statystyki (`stats.py`, `assessment/stats.py`).

### R1. Profil z ankiety — `survey_percentages(points)`, `survey_leaders(points)`
- Punkt dla stylu za każdą odpowiedź (`scoring.compute_score`). `raw[f] = points[f] / suma · 100`; forma z udziałem < 5% dostaje dokładnie 5%, pozostałe dzielą resztę proporcjonalnie do punktów (powtarzane, aż każda ma ≥ 5); zaokrąglenie największymi resztami; suma zawsze 100.
- Przykłady: V 9 / A 8 / K 3 → **V 45 / A 40 / K 15**; A 11 / V 6 / K 3 → A 55 / V 30 / K 15; V 6 / A 10 / K 4 → V 30 / A 50 / K 20; V 20 / A 0 / K 0 → V 90 / A 5 / K 5.
- `survey_leaders`: formy z maksimum punktów. Jedna → `style` = ta forma, `style_source = survey`. Kilka (np. V 8 / A 8 / K 4 → 40 / 40 / 20) → `style = null`, `dominant_style = "VA"`; uczeń wybiera jeden z remisujących (`tie_choice`), do tego czasu kursy, lekcje i quizy zwracają `403 SURVEY_REQUIRED` (D50).
- Ankieta raz: ponowne wysłanie → `409 SURVEY_ALREADY_DONE`. Potem procenty zmieniają tylko wyniki quizów.

### R2. Zmiana po quizie — `apply_result(percentages, form, passed)`, `is_counted(previous_forms_in_lesson, form)`
- `is_counted`: liczy się **tylko pierwsze podejście w danej formie w danej lekcji** (zaliczone albo nie). Kolejne podejście w tej samej formie jest zapisane (`counted = false`), procentów nie zmienia; pierwsze podejście w innej formie tej samej lekcji — liczy się.
- `new[form] = clamp(p[form] ± 10, 5, 90)`; dwie pozostałe formy dzielą `100 − new[form]` proporcjonalnie do swoich poprzednich wartości (z minimum 5); zaokrąglenie jak w R1.
- Przykłady:
  - V 45 / A 40 / K 15, porażka w V → **V 35 / A 47 / K 18** (A 65 · 40/55 = 47,27 → 47; K 17,73 → 18);
  - V 35 / A 47 / K 18, zaliczenie w A → **V 28 / A 57 / K 15** (V 28,40, K 14,60);
  - V 85 / A 10 / K 5, zaliczenie w V → V 90 / A 5 / K 5 (limit 90 i minimum 5);
  - V 5 / A 60 / K 35, porażka w V → bez zmian (forma już na minimum); wynik zapisany jako policzony, frontend pisze „Wzrokowe 5% – to już minimum”.

### R3. Statystyki form ucznia — `form_stats(results) -> {form: FormStats}`
- Z wyników ucznia **ze wszystkich kursów** (styl jest jeden dla ucznia): `lessons` = liczba policzonych wyników w formie, `average` = ich średnia (`null` bez danych), `confirmed` = co najmniej jedno **zaliczone** podejście w formie, także niepoliczone.
- Na ekranie: „potwierdzona wynikami (2 lekcje, średnio 88%)”, „jeszcze bez zaliczenia (1 lekcja, średnio 40%)”, „tylko z ankiety”.

### R4. Quiz zaliczony — odblokowanie i pochwała — `praise(results)`
- Każde zaliczone podejście (dowolne, także niepoliczone) woła `curriculum.mark_lesson_passed` (zapis w `lesson_completions` raz); następna opublikowana lekcja staje się dostępna (R10 w `curriculum`), `QuizFeedback.unlocked_lesson` podaje ją przy pierwszym zaliczeniu; `course_completed` — gdy właśnie zaliczona została ostatnia niezaliczona lekcja kursu.
- `praise`: bieżący wynik musi być policzony i zaliczony; seria = policzone zaliczone wyniki w tej samej formie liczone wstecz **przez wszystkie kursy**; niepoliczone wyniki są pomijane, serię przerywa policzony wynik niezaliczony albo w innej formie. Pochwała przy serii ≥ 2 → `{form, streak, average}` w `QuizFeedback.praise` i jako zdarzenie `praise` w dzienniku (D61).
- Przykład (Marta): V 80, V 100, V 80 → „3 lekcje z rzędu zaliczone w formie wzrokowej, średnio 87%”.

### R5. Quiz niezaliczony — „przerób w formie X” — `retry_suggestion(failed, percentages, stats, survey, results)`
- Kandydaci: dwie formy różne od formy, w której uczeń właśnie przerabiał lekcję (może to być forma inna niż styl).
- Jeśli któryś kandydat jest **potwierdzony** (R3): X = potwierdzony z najwyższym bieżącym procentem → remis: wyższa `average` → remis: V, A, K. `reason = "confirmed"`, `best` = najwyższy zaliczony wynik w X (z równych — najnowszy).
- Inaczej: X = kandydat z najwyższym procentem **w ankiecie** → remis: wyższy bieżący procent → V, A, K. `reason = "survey"`, `best = null`.
- Zawsze: `failed` = forma, wynik tego quizu i `previous` — poprzedni policzony wynik w tej formie w **innej** lekcji (`null`, gdy brak); `suggested.percent` (bieżący) i `survey_percent`.
- **Stopniowanie** — `strength`: `soft`, gdy **poprzedni policzony wynik w formie `failed.form`** (dowolna lekcja, bez bieżącego wyniku; niepoliczone pomijane) był zaliczony — pojedyncze potknięcie; w każdym innym przypadku (poprzedni policzony w tej formie niezaliczony = druga porażka z rzędu, albo brak poprzedniego policzonego wyniku w formie) — `strong`. Niepoliczona powtórka w tej samej formie porównuje się z policzonym wynikiem tej lekcji (pierwszym podejściem w formie). Ekran: `soft` — na pierwszym planie „Rozwiąż jeszcze raz”, pod nim zdanie z linkiem do formy X; `strong` — ramka z uzasadnieniem i przyciskiem „Przerób tę lekcję w formie X”. Zdarzenia zapisane przed wprowadzeniem pola (bez `strength`) czytamy jako `strong` (`RetrySuggestion.strength` ma domyślnie `strong`, np. w `StudyResponse.suggestion`).
- Funkcja przyjmuje cały wynik (`failed: Result`) i wyniki ucznia w kolejności zapisu (ostatni = `failed`). Sugestia trafia do dziennika przy **każdym** niezaliczonym podejściu.
- Przykłady stopniowania: V 80 (lekcja 1), V 40 (lekcja 2) → `soft`; V 40 (lekcja 2), V 40 (lekcja 3) → `strong`; pierwsza porażka w formie bez wcześniejszych wyników → `strong`.
- Przykład (Kuba, V 45 / A 40 / K 15, lekcja 3 w V na 40%, `strong` — lekcja 2 w V też 40%): A i K niepotwierdzone → A (40% w ankiecie > 15%) → „Wzrokowe: ten quiz 40%, poprzednia lekcja 40%. Słuchowe były drugie w Twojej ankiecie (40%), nie mamy jeszcze o nich wyników – warto sprawdzić.” Przy potwierdzonej formie: „Słuchowe zaliczyłeś w lekcji „Wzór i wykres” na 80%.”

### R6. Propozycja zmiany stylu na stałe — `switch_proposal(style, percentages, stats, rejections, trial_active)`
- Kandydaci: formy Y ≠ aktywny styl, **potwierdzone** (R3) i z **wyższym procentem** niż aktywny styl. Kilka → najwyższy procent → wyższa `average` → V, A, K.
- Brak propozycji: bez stylu, w trakcie okresu próbnego, gdy otwarta jest propozycja `revert`, oraz gdy najlepszy kandydat był odrzucony i od odrzucenia uczeń ma mniej niż 2 nowe policzone wyniki (`total − counted_at_decision < RENEW_AFTER`). Wtedy **nie** przechodzimy do drugiego kandydata.
- Dowód: `{from: {form, lessons, average, percent}, to: {...}}` (`form_evidence`).
- Przykład (Kuba po lekcji 3 w A na 80%, V 28 / A 57 / K 15): A potwierdzona i 57 > 28 → propozycja V → A: „Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%” (V: 80, 40, 40 → 53,3 → 53).
- Ocena przy każdym wyniku (`hooks._update_switch_proposal`): otwarta `switch`, której warunek przestał obowiązywać albo wskazuje inną formę → `expired` (+ zdarzenie); nowa tworzona, gdy nie ma otwartej tej samej formy.
- Decyzja ucznia: przyjęcie → styl = Y, `style_source = proposal`, start okresu próbnego (tylko `switch`); odrzucenie → `rejected`, `counted_at_decision` = liczba policzonych wyników ucznia. Ręczna zmiana stylu zamyka otwartą propozycję (`superseded`).
- **Czyszczenie wyborów formy** — `forms_to_clear(chosen_forms, passed_lesson_ids)`: przy **każdej** zmianie stylu (przyjęte `switch` i `revert`, zmiana ręczna) usuwane są wiersze `lesson_forms` w lekcjach jeszcze niezaliczonych; w zaliczonych wybór zostaje jako zapis historii. Lista (`lesson_id`, `lesson_title`, `form`) trafia do `cleared_lessons` w zdarzeniu.

### R7. Okres próbny — `trial_baseline(results, previous_style)`, `trial_outcome(before, form, after_results)`, `trial_progress(form, after_results)`
- Start: przyjęta propozycja `switch` albo zmiana ręczna (także w trakcie innego okresu — poprzedni po policzonych lekcjach kończy się bez wyniku, przed nimi patrz R7a). Po przyjęciu `revert` okresu nie ma (bez pętli).
- `before_average` = średnia z ostatnich ≤ 2 policzonych wyników w **poprzednim** stylu (`null`, gdy brak).
- Liczą się policzone wyniki w **nowym** stylu (`to_style`) zapisane od `started_at`; wyniki w innej formie (np. lekcja przerabiana w wybranej formie) się nie liczą. Po 2 → `after_average` (średnia dwóch pierwszych), `diff = after − before`:
  - `diff ≥ +10` → `helped` („Zmiana pomogła: średnia 40% → 90%”),
  - `−10 < diff < +10` → `neutral` („Bez wyraźnej różnicy: średnia 60% → 65%”),
  - `diff ≤ −10` → `worse` + propozycja **powrotu** (`kind = revert`, do `from_style`, bez wymogu potwierdzenia; dowód `{from, to, before_average, after_average}`; wcześniejsza otwarta propozycja → `expired`),
  - `before = null` → `no_baseline` („Średnia w nowej formie: 85%”).
- Przykład (Marta): K 40% → propozycja K → V przyjęta (`before` = 40), lekcje 2 i 3 w V: 100%, 80% → `after` = 90, `diff` = +50 → `helped`.

### R8. Podpowiedź z kursu — `course_hint(course_results, student_id)`
- Tylko dla ucznia **bez żadnego wyniku w kursie**. Policzone wyniki innych uczniów tego kursu pogrupowane po formie; formy z ≥ 2 uczniami; najwyższa średnia → więcej uczniów → V, A, K → `{form, average, students, results}`; `null` bez danych. Bez automatycznej zmiany stylu.
- Przykład (demo, Matematyka, Zosia po przyjęciu): „W tym kursie najlepiej wypada forma słuchowa (średnio 86%, 3 uczniów)”.

### R7a. Zmiana stylu w trakcie okresu próbnego — `trial_on_style_change(active, counted_in_trial, new_style, previous_style, before_average, *, starts_trial)` (D60)
- Wejście: trwający okres (`TrialInfo`: `id`, `from_style`, `to_style`, `before_average`) albo `None`, liczba policzonych wyników w jego nowej formie (`trial_progress`), nowy i poprzedni styl, `before_average` = `trial_baseline` poprzedniego stylu; `starts_trial = false` dla przyjętego `revert`. Wynik `TrialDecision(action, from_style, before_average)`.
- Trwa okres i **0** policzonych lekcji w nowej formie (zmiana nie była sprawdzona):
  - nowy styl = `from_style` okresu → `cancel`: okres `result = cancelled`, `finished_at`; nowy okres **nie** startuje; w dzienniku `style_change_reverted` **zamiast** `manual_style_change` / `proposal_accepted`;
  - inny (trzeci) styl → `replace`: stary okres `cancelled`, nowy startuje z **tym samym** punktem odniesienia (`from_style`, `before_average` starego okresu), `trial_started` z `replaced_trial_id`.
- Były policzone lekcje albo brak okresu → `start` (jak dotąd: stary okres zamknięty z `result = null`, nowy od poprzedniego stylu); `starts_trial = false` → `none` (bez nowego okresu).
- Przykłady: A (2 lekcje po 100%) → ręcznie V → bez lekcji ręcznie A → `cancel` (nie ma okresu „V → A” ani komunikatu „brak wyników do porównania”); A → V → K bez lekcji → `replace`, okres A → K z `before_average` = 100.
- `LearningProfileResponse.trial` nie pokazuje okresu `cancelled`: trwający albo ostatni zakończony niecofnięty (albo null).

### R12. Seria porażek — `attention(results) -> Attention | None`
- Wejście: wyniki ucznia ze **wszystkich kursów** w kolejności zapisu. Liczą się tylko policzone wyniki, od najnowszego wstecz: niepoliczone pomijane, pierwszy policzony zaliczony kończy serię (forma bez znaczenia).
- Seria ≥ `ATTENTION_STREAK` (3) → `Attention(streak, results)`: `streak` = długość serii (może być > 3), `results` = 3 ostatnie policzone wyniki w kolejności chronologicznej ({`lesson_id`, `lesson_title`, `form`, `percent`}). Krótsza seria → `null`. Stan znika po pierwszym zaliczonym policzonym wyniku.
- Zdarzenie `attention_needed` zapisywane, gdy policzony niezaliczony wynik daje serię **dokładnie 3** — raz na serię (czwarta porażka nie dopisuje wpisu; po zaliczeniu nowa seria może dać nowy wpis).
- Komunikat u ucznia: „Trzy ostatnie lekcje poniżej progu (55%, 40%, 50%). Spróbuj innej formy albo poproś nauczyciela o pomoc.”; u nauczyciela przy uczniu „wymaga uwagi” z tymi wynikami. Bez automatycznej zmiany stylu.
- Przykład: lekcja 1 w V 40%, w A 20%, w K 60% → seria 3, zdarzenie; niepoliczona powtórka w K na 80% nie kończy serii; zaliczony policzony wynik w lekcji 2 → `attention = null`.

Reguły R9 (losowanie, `assessment/drawing.py`), R10 (blokada, `curriculum/progress.py`) i R11 (gotowość, `*/readiness.py`) — w modułach `05`, `02`, `07`.

## Kolejność w `hooks.record_quiz_result`

Jedno wywołanie z `assessment.submit_attempt` po ocenie zestawu (wynik liczy serwer; nie ma endpointu, przez który przeglądarka zgłasza wynik). Jeden `commit` na końcu.

1. `require_style`; forma = `lesson_form` (wybór lekcji albo aktywny styl) w chwili wysłania.
2. `counted = is_counted(formy wcześniejszych wyników tej lekcji, forma)`; zapis `quiz_results`; jeśli policzony → `apply_result`, nowe procenty w profilu. `form_stats` z wyników łącznie z bieżącym.
3. Zaliczony → `course_progress` przed i po `curriculum.mark_lesson_passed` (odblokowanie, `course_completed`), `praise`. Zdarzenie `quiz_attempt`; przy policzonym — punkt `style_history`; przy pochwale — zdarzenie `praise`.
4. Niezaliczony → `retry_suggestion` (z procentami **po** zmianie i procentami ankiety, ze `strength`), zdarzenie `retry_suggestion`. Potem `attention` (R12) z wyników łącznie z bieżącym; policzony wynik, który daje serię dokładnie 3 → zdarzenie `attention_needed`.
5. Trwający okres próbny → `trial_outcome`; po 2 wynikach: zakończenie, `trial_finished`, przy `worse` propozycja `revert` (`proposal_created`).
6. `switch_proposal` (pomijane, gdy otwarta jest `revert`): wygaszenie nieaktualnej (`proposal_expired`), utworzenie nowej (`proposal_created`).
7. `commit`; `QuizFeedback`: `form`, `counted`, `percentages_before`, `percentages_after`, `passed`, `unlocked_lesson` {`id`, `title`, `number`} / null, `course_completed`, `praise` / null, `suggestion` / null, `proposal` (otwarta po podejściu) / null, `trial` (trwający albo zakończony tym podejściem) / null, `attention` (R12, stan po tym podejściu) / null.

## Dziennik decyzji — typy zdarzeń i `data`

| `type` | `data` | `course_id` / `lesson_id` |
|---|---|---|
| `survey_completed` | `points`, `percentages`, `style` (null przy remisie), `tie_styles` | — |
| `tie_resolved` | `style`, `tie_styles` | — |
| `quiz_attempt` | `draw_id`, `form`, `percent`, `passed`, `counted`, `percentages_before`, `percentages_after`, `unlocked_lesson` ({`id`, `title`, `number`} / null) | kurs, lekcja |
| `praise` | `form`, `streak`, `average` (R4, seria ≥ 2) | kurs, lekcja |
| `retry_suggestion` | `failed`: {`form`, `percent`, `previous`: {`lesson_id`, `lesson_title`, `percent`} / null}, `suggested`: {`form`, `reason`, `percent`, `survey_percent`, `best`: {…} / null}, `strength` (`soft` / `strong`; brak w starszych wpisach = `strong`) | kurs, lekcja |
| `attention_needed` | `streak` (3), `results`: [{`lesson_id`, `lesson_title`, `form`, `percent`}] — 3 ostatnie policzone wyniki, chronologicznie (R12) | kurs, lekcja (wynik, który dał serię) |
| `lesson_form_changed` | `from`, `to`, `source` (`manual` / `suggestion`) | kurs, lekcja |
| `proposal_created` | `proposal_id`, `kind`, `from`, `to`, `evidence` | kurs, lekcja (z quizu) |
| `proposal_accepted` | `proposal_id`, `kind`, `from`, `to`, `cleared_lessons` ([{`lesson_id`, `lesson_title`, `form`}]) | — |
| `proposal_rejected`, `proposal_expired` | `proposal_id`, `kind`, `from`, `to` | `expired`: kurs, lekcja |
| `manual_style_change` | `from`, `to`, `cleared_lessons`, `superseded_proposal_id` (null, gdy nie było otwartej) | — |
| `trial_started` | `trial_id`, `from`, `to`, `source`, `before_average`, `replaced_trial_id` (okres zastąpiony przez R7a albo null) | — |
| `style_change_reverted` | `from`, `to`, `trial_id` (cofnięty okres), `source` (`manual` / `proposal`), `cleared_lessons` — cofnięcie zmiany przed pierwszą lekcją (R7a), zamiast `manual_style_change` / `proposal_accepted` | — |
| `trial_finished` | `trial_id`, `from`, `to`, `before_average`, `after_average`, `result` | kurs, lekcja |

Punkt `style_history` (z `event_id`) zapisują: `survey_completed`, `tie_resolved`, policzony `quiz_attempt`, `proposal_accepted`, `manual_style_change`, `style_change_reverted`.

## Statystyki (`stats.py`, czyste funkcje)

Każda statystyka odpowiada na jedno pytanie. Poniżej progu danych udział jest `null`, a obok zostaje liczebność (`n`, `started`, `first_try_lessons`), z której by wynikał — frontend pisze „za mało danych (n = 2)”. „Pierwsze podejście” = policzony wynik (R2). Średnie: `rules.average`, udziały: `rules.rate` (połówka w górę), liczba podejść do zaliczenia: 1 miejsce po przecinku (`mean_tenths`, połówka w górę). Bez nowych tabel: dane z `quiz_results`, `lesson_completions` i `learning_profiles`.

| Stała | Wartość | Gdzie |
|---|---|---|
| `FIRST_TRY_MIN_LESSONS` | 2 | tabela form: `first_try_rate` |
| `LESSON_MIN_STUDENTS` | 3 | statystyki lekcji: `pass_rate`, `first_average`, najtrudniejsza lekcja |
| `MATRIX_MIN_RESULTS` | 2 | macierz lekcja × forma: średnia komórki i wnioski |
| `FORM_GAP` | 20 | wniosek macierzy: najlepsza − najsłabsza forma (pkt) |

Stałe powtórzone we frontendzie (`explain.ts`) do tekstów.

- `student_summary(results)` (uczeń, wszystkie kursy) → `attempts` (wszystkie wyniki), `average` (średnia policzonych, `null` bez nich), `counted`, `streak` — kolejne zaliczone policzone wyniki od najnowszego wstecz do pierwszego niezaliczonego policzonego (niepoliczone pomijane, forma bez znaczenia). `passed_lessons` dokłada serwis z `curriculum` (`lesson_completions` lekcji, w których uczeń ma wyniki — wszystkie kursy).
  - Przykład: L1 V 40 (policzony), L1 V 80 (niepoliczony), L2 V 100, L2 A 60 → `attempts` 4, `counted` 3, `average` 67, `streak` 0, `passed_lessons` 2.
- `form_table(results, percentages)` → dla V / A / K `FormTableRow`: `lessons` (różne lekcje z podejściem w formie), `attempts`, `passed_lessons` (różne lekcje z zaliczonym podejściem w formie), `first_try_lessons` (policzone wyniki w formie), `first_try_passed`, `first_try_rate` (`null`, gdy `first_try_lessons < 2`), `average` (policzonych), `best` (najwyższy wynik, każde podejście), `confirmed` (R3), `percent` (procent profilu; `null` bez profilu). Ten sam wiersz w „Moich postępach” i w szczegółach ucznia u nauczyciela.
  - Przykład (jak wyżej): V — 2 lekcje, 3 podejścia, 2 zaliczone lekcje, za pierwszym razem 1 z 2 (50%), średnio 70%, najlepszy 100%, potwierdzona; A — 1 lekcja, `first_try_rate = null`.
- `lesson_stats(lessons, results)` (kurs, opublikowane lekcje w kolejności kursu) → `LessonStatsRow`: `started` (uczniów z ≥ 1 podejściem), `passed` (uczniów z zaliczonym podejściem), `pass_rate` (% `passed / started`), `first_average` (średnia policzonych wyników lekcji) — oba `null`, gdy `started < 3`; `first_results` (liczba policzonych), `attempts_to_pass` (średnia liczba podejść do pierwszego zaliczenia włącznie wśród uczniów, którzy zaliczyli; `null`, gdy nikt).
  - Przykład: 4 uczniów — V 80, V 100, A 20 → A 80 (powtórka), A 60 → `started` 4, `passed` 3, `pass_rate` 75, `first_average` 65, `attempts_to_pass` 1,3.
- `hardest_lesson(rows)` — najniższy `pass_rate` wśród lekcji z `started ≥ 3`; remis → niższa `first_average` → wcześniejsza lekcja; `null`, gdy żadna lekcja nie ma 3 uczniów albo wszystkie takie mają 100%.
- `lesson_form_matrix(lessons, results)` → wiersz na lekcję z komórkami V / A / K: `{average, n}` — średnia policzonych wyników w formie, `average = null` przy `n < 2`.
- `form_gaps(matrix)` — lekcje, w których najlepsza i najsłabsza forma (obie z `average`, czyli `n ≥ 2`) różnią się o ≥ 20 pkt: `{lesson_id, title, number, best: {form, average, n}, worst: {…}}`; remis form → V, A, K; kolejność kursu. Przykład: V 90 (n 2), A 40 (n 2) → wniosek; V 90, A 71 → brak (19 pkt).
- `form_effectiveness(course_results)` → dla V / A / K: `average` (policzonych), `counted_results`, `attempts` (wszystkie), `students` (z co najmniej jednym podejściem w formie).
- `style_distribution(styles)` → `{V, A, K, none}` (`none` = bez ankiety albo remis nierozstrzygnięty).
- `counted_average(results)` — średnia policzonych wyników ucznia (np. w kursie).
- `lesson_results(lessons, attempts, passed_ids)` — lekcje z co najmniej jednym podejściem, w kolejności kursu, ze wszystkimi podejściami (`at`, `form`, `percent`, `passed`, `counted`).

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /survey/questions` | zalogowany | aktywne pytania z odpowiedziami **bez stylu** odpowiedzi | 401 |
| `POST /survey/answers` | uczeń | `{answers: [{question_id, answer_id}]}` → `LearningProfileResponse` | 409 `SURVEY_ALREADY_DONE` / `SURVEY_EMPTY`; 400 `SURVEY_DUPLICATE_ANSWER` / `SURVEY_INCOMPLETE` / `SURVEY_ANSWER_MISMATCH`; 403 `FORBIDDEN` |
| `GET /profile/learning-style` | zalogowany | `LearningProfileResponse` (nie-uczeń i uczeń bez ankiety: `survey_completed = false`, reszta pusta) | 401 |
| `POST /profile/learning-style/tie-choice` | uczeń | `{style}` przy nierozstrzygniętym remisie | 403 `SURVEY_REQUIRED`, 409 `NO_TIE`, 400 `STYLE_NOT_TIED`, 422 |
| `PUT /profile/learning-style` | uczeń | `{style}` → zmiana ręczna: procenty bez zmian, otwarta propozycja `superseded`, czyszczenie wyborów formy, nowy okres próbny albo cofnięcie / zastąpienie trwającego (R7a) | 403 `SURVEY_REQUIRED`, 409 `SAME_STYLE`, 422 |
| `POST /profile/learning-style/proposals/{id}/accept` | uczeń | przyjęcie → `LearningProfileResponse` | 404 `PROPOSAL_NOT_FOUND` (także cudza), 409 `PROPOSAL_NOT_OPEN`, 403 `SURVEY_REQUIRED` |
| `POST /profile/learning-style/proposals/{id}/reject` | uczeń | odrzucenie → `LearningProfileResponse` | jak wyżej |
| `GET /lessons/{id}/study` | uczeń | `StudyResponse` | 403 `SURVEY_REQUIRED` / `ENROLLMENT_REQUIRED` / `LESSON_LOCKED` (+ `required_lesson`), 404 `LESSON_NOT_FOUND`; 403 `FORBIDDEN` dla innych ról |
| `PUT /lessons/{id}/study/form` | uczeń | `{form, source: "manual" \| "suggestion"}` → `StudyResponse`; forma różna od stylu → zapis wyboru, równa stylowi → usunięcie wyboru (powrót do stylu); zdarzenie `lesson_form_changed`, gdy forma lekcji się zmienia (ta sama forma → bez zmian) | jak wyżej, 422 |
| `GET /courses/{id}/study-states` | uczeń przyjęty | `LessonStudyState[]` — opublikowane lekcje w kolejności kursu (przycisk „Rozpocznij” / „Kontynuuj” / „Powtórz”, D57) | 404 `COURSE_NOT_FOUND`, 403 `ENROLLMENT_REQUIRED` / `FORBIDDEN` |
| `GET /courses/{id}/hint` | uczeń przyjęty | `CourseHint` albo `null` | 404 `COURSE_NOT_FOUND`, 403 `ENROLLMENT_REQUIRED` / `FORBIDDEN` |
| `GET /me/progress` | uczeń | `ProgressResponse` | 403 `FORBIDDEN` |
| `GET /me/journal` | uczeń | `JournalEntry[]`, od najnowszego | 403 `FORBIDDEN` |
| `GET /me/stats` | uczeń | `StudentStatsResponse` (wszystkie kursy ucznia; także bez ankiety — wtedy `percent = null`) | 403 `FORBIDDEN` |
| `GET /courses/{id}/stats` | autor (zatwierdzony) | `CourseStatsResponse` | 404 `COURSE_NOT_FOUND`, 403 `FORBIDDEN` / `TEACHER_NOT_APPROVED` |
| `GET /courses/{id}/students/{student_id}` | autor | `StudentDetailResponse` (tylko uczeń przyjęty do kursu) | 404 `STUDENT_NOT_FOUND` / `COURSE_NOT_FOUND`, 403 |

Schematy:
- `LearningProfileResponse`: `survey_completed`, `style`, `style_source`, `tie_styles` (niepuste tylko przy nierozstrzygniętym remisie), `percentages`, `forms` ({`V`: {`confirmed`, `lessons`, `average`}, …}), `survey` ({`points`, `percentages` z R1, `created_at`}), `open_proposal`, `trial` (trwający albo ostatni zakończony, bez `cancelled`).
- `Proposal`: `id`, `kind`, `from`, `to`, `evidence`, `created_at`. `Trial`: `id`, `from`, `to`, `source`, `before_average`, `after_average`, `result`, `done` (policzone wyniki w nowej formie, ≤ 2), `needed` (2), `started_at`, `finished_at`.
- `StudyResponse`: `lesson_id`, `form`, `form_source` (`style` / `choice` — tylko wybór różny od aktywnego stylu), `style`, `blocks` (wersja w formie `form`; pusta lista, gdy wersji nie ma), `other_forms`, `suggestion` (z ostatniego podejścia w lekcji, gdy było niezaliczone i uczeń nie przeszedł jeszcze na sugerowaną formę), `last_result` ({`percent`, `passed`, `form`} / null).
- `LessonStudyState`: `lesson_id`, `started` (jest wynik w lekcji albo jawny wybór formy), `passed` (zaliczenie z `curriculum`), `best_percent` / `last_percent` (najlepszy / ostatni wynik w lekcji, null bez wyników), `chosen_form` (jawny wybór formy różny od aktywnego stylu albo null). Blokadę lekcji podaje `CourseResponse.lessons[].state`.
- `CourseHint`: `form`, `average`, `students`, `results`.
- `ProgressResponse`: `history` ([{`at`, `percentages`, `style`, `event`}] — `event`: `JournalEntry` zdarzenia, które zapisało punkt (`style_history.event_id`; D62: wykres odróżnia ankietę i policzone quizy od zmian stylu i cofnięć); punkty są tylko dla zdarzeń zmieniających profil albo styl), `courses` (przyjęte: `id`, `title`, `passed`, `total`, `next_lesson`), `lessons` (`course_id`, `course_title`, `lesson_id`, `lesson_title`, `number`, `passed`, `attempts`).
- `JournalEntry`: `id`, `type`, `at`, `course` {`id`, `title`} / null, `lesson` {`id`, `title`, `number`} / null (`number` wśród opublikowanych lekcji, null dla nieopublikowanej — etykiety „L1 · A”), `data`.
- `CourseStatsResponse`: `forms` ({`V`: {`average`, `counted_results`, `attempts`, `students`}, …}), `styles` ({`V`, `A`, `K`, `none`} przyjętych uczniów), `students` ([{`id`, `display_name`, `email`, `style`, `percentages`, `passed`, `total`, `average` (policzone w kursie), `last_activity` (ostatni wynik w kursie), `open_proposal` {`to`, `kind`} / null, `attention` (R12 ucznia ze wszystkich jego kursów) / null}]), `pending_requests`, `lessons` (`LessonStatsRow[]`: `lesson_id`, `title`, `number`, `started`, `passed`, `pass_rate`, `first_average`, `first_results`, `attempts_to_pass` — opublikowane lekcje w kolejności kursu), `hardest` (`LessonStatsRow` / null), `matrix` ([{`lesson_id`, `title`, `number`, `cells`: {`V` | `A` | `K`: {`average`, `n`}}}]), `form_gaps` ([{`lesson_id`, `title`, `number`, `best`: {`form`, `average`, `n`}, `worst`: {…}}]). Liczby lekcji i macierzy — tylko z wyników uczniów obecnie przyjętych.
- `StudentDetailResponse`: `student`, `profile`, `history` (jak w `ProgressResponse`, z `event`), `lessons` (tylko ten kurs), `journal` (zdarzenia tego kursu + zdarzenia globalne: ankieta, wybór remisu, zmiany stylu, okresy próbne), `forms` (`{V | A | K: FormTableRow}` ze wszystkich kursów ucznia), `attention` / null.
- `StudentStatsResponse`: `summary` {`passed_lessons`, `attempts`, `average`, `counted`, `streak`}, `forms` (`{V | A | K: FormTableRow}`: `lessons`, `attempts`, `passed_lessons`, `first_try_lessons`, `first_try_passed`, `first_try_rate`, `average`, `best`, `confirmed`, `percent`), `attention` / null.
- `Attention` (`AttentionResponse`): `streak`, `results` ([{`lesson_id`, `lesson_title`, `form`, `percent`}], 3 ostatnie policzone, chronologicznie). `RetrySuggestion`: `failed`, `suggested`, `strength` (`soft` / `strong`).

Usunięte endpointy v2 (testowane jako 404): `GET /survey/results`, `DELETE /profile/learning-style`, `POST /profile/learning-style/proposal/accept|reject`, `GET /lessons/{id}/personalized-blocks`, `POST /lessons/{id}/blocks/{block_id}/open`.

## Frontend

Zdania decyzji składa wyłącznie `features/learning-style/explain.ts` (kody i liczby → polskie zdania: wynik quizu i „Co to zmieniło”, pochwała, sugestia, propozycja i jej dowód, okres próbny, podpowiedź, stany form, wyczyszczone wybory, każdy typ dziennika; głos „ucznia” albo neutralny dla nauczyciela). Stałe reguł (`PASS_THRESHOLD`, `STEP`, `TRIAL_LESSONS`, progi) są tam powtórzone do tekstów.

- `features/learning-style/components`:
  - `SurveyGate` (layouty `(app)` i `(focus)`): uczeń bez ankiety → `/survey`, z nierozstrzygniętym remisem → `/survey/result`; inne role przechodzą.
  - `SurveyForm` (`/survey`: pasek postępu, odpowiedzi w stałej mieszanej kolejności, przewinięcie do brakującego pytania); `SurveyResult` (`/survey/result`: procenty jako `StyleBars`, styl i opis; przy remisie `RadioGroup` z remisującymi stylami i „Wybieram ten styl”).
  - `LearningStylePanel` (`/profile`, „Mój styl”): aktywny styl i źródło, `FormPercentages` (procent i stan każdej formy z R3), otwarta propozycja (`StyleProposalBanner`), `TrialNote` („1 z 2 lekcji w nowej formie” albo wynik), ręczna zmiana (`RadioGroup` + `AlertDialog`: procenty się nie zmienią, zmiana trafi do dziennika), wynik ankiety.
  - `LessonFormBar` („Przerabiasz tę lekcję w formie: Słuchowej (A)” + menu z dwiema formami), `RetrySuggestionBox` (R5: uzasadnienie i „Przerób tę lekcję w formie X”), `QuizFeedbackPanel` (wynik quizu: „Co to zmieniło”, reguła, pochwała, sugestia, propozycja, okres próbny), `StyleProposalBanner` („Przełącz na stałe” / „Zostaję przy swoim”), `FormMark` (kwadrat w kolorze formy z literą i nazwą), `form-tones.ts`.
- `features/progress`: `ProgressPage` (`/progress`, „Moje postępy”: `PercentChart`, postęp kursów, `LessonResultsTable`, `DecisionJournal`); `PercentChart` — własny wykres SVG (trzy linie w kolorach form z wzorem kreskowania, litera i nazwa przy końcu linii, oś 0–100%, punkt po każdej zmianie profilu, pod spodem tabela tych samych danych); `LessonResultsTable` (podejścia pogrupowane po lekcji, pierwsze policzone oznaczone); `DecisionJournal` (data, rodzaj, zdanie z `explain.ts`, kurs / lekcja); `FormPercentages`. Te komponenty używa też `teach/StudentDetailPage`.
- Klucze: `["learning-style", "profile"]`, `["learning-style", "questions"]`, `["lessons", id, "study"]`, `["courses", id, "hint"]`, `["me", "progress"]`, `["me", "journal"]`. Zmiany profilu (ankieta, remis, zmiana ręczna, propozycja) zapisują profil i unieważniają wszystkie zapytania `study` oraz `["me"]`; zmiana formy lekcji zapisuje `study` i unieważnia quiz lekcji i dziennik.

## Testy
`backend/tests/learning_style/`:
- `test_rules.py` (86 przypadków z parametryzacją): `rate` (połówka w górę), R1 (przykłady, minimum 5%, reszty przy remisie, brak punktów, właściwość „suma 100 i każda 5–90” na siatce, liderzy), R2 (przykłady ze specyfikacji, ścieżki Kuby i Marty, limit 90, minimum 5, proporcja, właściwość na siatce), `is_counted`, R3 (potwierdzenie niepoliczonym zaliczeniem, porażka nie potwierdza), R4 (Marta, seria ≥ 2, przerwanie inną formą i porażką, pomijanie niepoliczonych), R5 (ankieta, potwierdzony kandydat, remisy procentu / średniej / kolejności, oblanie w formie innej niż styl, poprzedni wynik z innej lekcji; `strength`: `soft` po zaliczonym poprzednim, `strong` po niezaliczonym i bez poprzedniego, najnowszy wynik w formie w obu kierunkach, pomijanie niepoliczonych, niepoliczona powtórka w tej samej formie, porażka w formie z wyboru), R6 (Kuba z dowodem, niepotwierdzona / niewyższa forma, okres próbny, wybór kandydata, powrót odrzuconej po 2 wynikach, niepoliczone nie odnawiają, odrzucenie innej formy nie blokuje), `forms_to_clear`, R7 (Marta, granice +10 / +9 / −9 / −10, `no_baseline`, czekanie na 2 wyniki w nowej formie, dwa pierwsze wyniki, `trial_baseline`), R7a (start, cofnięcie, zastąpienie z punktem odniesienia, po policzonych lekcjach jak dotąd, `revert` bez okresu), R8 (min. 2 uczniów, remisy, uczeń z wynikami), R12 (3 porażki → seria z wynikami, 2 → brak, seria > 3 z trzema ostatnimi wynikami, pomijanie niepoliczonych, zaliczenie kończy serię).
- `test_scoring.py`, `test_stats.py` (czyste funkcje: `mean_tenths`, podsumowanie ucznia i seria, tabela form z progiem 2 lekcji i potwierdzeniem niepoliczonym zaliczeniem, statystyki lekcji z progiem 3 uczniów i podejściami do zaliczenia, najtrudniejsza lekcja z remisami i brakiem, macierz z progiem 2 wyników, wnioski od 20 pkt, remisy form); `test_survey_api.py` (20 pytań, brak klucza, procenty i styl, minimum, ankieta raz, remis i wybór, walidacja, role, usunięte endpointy v2, dziennik tylko własny); `test_survey_wording.py`.
- `test_adaptation_flow.py` (przez API): tylko pierwsze podejście w formie zmienia procenty, forma z wyboru lekcji, zdarzenie `quiz_attempt` z danymi, zdarzenie `praise` przy serii, odblokowanie i ukończenie kursu, sugestie (ankieta, potwierdzona), ścieżka Kuby do propozycji i okresu próbnego, brak propozycji dla niepotwierdzonej formy, powrót odrzuconej po 2 wynikach, wygaszenie, cudza propozycja → 404, Marta `helped`, `worse` → propozycja powrotu bez nowego okresu, `no_baseline`, wyniki w innej formie poza okresem, zmiana ręczna (`superseded` + okres próbny, nowy okres w trakcie starego, błędy), czyszczenie wyborów formy przy zmianie ręcznej i przyjęciu propozycji; R7a: ścieżka Patryka A (2 × 100%) → V → A bez lekcji (cofnięcie, okres `cancelled`, brak okresu „V → A”, profil bez okresu) i A → V → K (okres A → K z punktem odniesienia z A, `replaced_trial_id`), zmiana po policzonej lekcji jak dotąd, cofnięcie po przyjęciu propozycji; R5 `strength` w odpowiedzi, zdarzeniu i `study` (niepoliczona powtórka → `strong`, starsze zdarzenie bez pola → `strong`); R12: `attention` po trzeciej porażce, jedno zdarzenie `attention_needed` na serię, niepoliczone podejścia bez zmian, seria 4, zaliczenie kończy serię.
- `test_study_api.py` (wersja stylu, wybór innej formy, powrót do formy stylu usuwa wybór, wybór w zaliczonej lekcji równy nowemu stylowi → `style`, brak wersji, sugestia do zmiany formy, dostęp), `test_insights_api.py` (punkty historii ze zdarzeniami: ankieta, policzone quizy, zmiana ręczna, cofnięcie, wybór remisu, przyjęta propozycja, bez punktów dla niepoliczonych wyników i pochwały, numer lekcji; stany lekcji ucznia: nowa, z wyborem formy, niezaliczona, zaliczona z najlepszym i ostatnim wynikiem, tylko opublikowane, dostęp; podpowiedź i dostęp, postępy, dziennik od najnowszego z kursem i lekcją, tylko uczeń; statystyki kursu, otwarta propozycja w tabeli, tylko autor; szczegóły ucznia tylko dla przyjętego; `/me/stats` — podsumowanie, tabela form, seria i `attention`, uczeń bez wyników i bez ankiety, tylko uczeń; statystyki lekcji, najtrudniejsza lekcja, macierz i wnioski bez ucznia odrzuconego, tylko opublikowane lekcje, brak najtrudniejszej przy 100%, `attention` w tabeli uczniów i w szczegółach ucznia z innego kursu, `forms` w szczegółach).

## Jak sprawdzić ręcznie
Na kontach demo (`moduly/06-demo.md`, hasło `Demo123!`):
- `uczen.nowy@imsu.pl`: wejście na `/courses` → przekierowanie na ankietę → wynik z procentami → „Mój styl”.
- `uczen.demo@imsu.pl` (V 45 / A 40 / K 15): Matematyka → lekcja 3 w V, quiz na 40% (3 błędne) → „Wzrokowe 45% → 35%”, sugestia A z ankiety → „Przerób tę lekcję w formie słuchowej” → quiz na 80% → „Słuchowe 47% → 57%”, propozycja „Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%” → „Przełącz na stałe” → „Mój styl”: okres próbny „0 z 2 lekcji”, średnia przed 40%.
- `uczen.zmiana@imsu.pl`: „Moje postępy” — wykres (K spada, V rośnie po przyjęciu propozycji), tabela wyników (lekcja 1 w K i w V), dziennik z sugestią, propozycją, okresem próbnym i „Zmiana pomogła: średnia 40% → 90%”; „Mój styl” — wynik okresu próbnego.
- `nauczyciel.demo@imsu.pl`: Matematyka → „Panel kursu” → skuteczność form, wiersz ucznia → szczegóły z dziennikiem.
- Po pokazie: `python -m app.demo.seed --reset-students`.

## Ograniczenia
- **Druga szansa jest łatwiejsza:** po porażce uczeń zna część pytań i ich wyjaśnienia, więc pierwsze podejście w nowej formie tej samej lekcji może zawyżać jej procent. Łagodzą to: inne pytania przy powtórce (R9), liczenie tylko pierwszego podejścia w formie i wymóg potwierdzenia formy przed propozycją (R6) — reguły nie usuwają tego efektu.
- Model VAK i dopasowanie formy do stylu (*meshing*) nie mają mocnego potwierdzenia empirycznego (Pashler i in., 2008): ankieta to hipoteza startowa, którą system sprawdza wynikami, a decyzję zostawia uczniowi (`02-koncepcja.md` §8).
- Ankieta raz — bez ponownego wypełnienia; statystyki form i propozycje liczone ze wszystkich kursów ucznia.
- Okres próbny przerwany kolejną zmianą stylu **po** policzonych lekcjach kończy się bez wyniku (w dzienniku tylko nowy `trial_started`); przed nimi — cofnięcie albo zastąpienie (R7a).
- Zmiana formy lekcji przy otwartym zestawie pytań losuje nowy zestaw (`quiz_draws.form`, `moduly/05-assessment.md`), ale wynik zawsze dostaje formę z chwili wysłania.
- Statystyki kursu i podpowiedź R8 liczą wyniki tylko uczniów obecnie przyjętych na kurs (uczeń odrzucony po fakcie wypada ze statystyk); tabela i rozkład stylów — też tylko przyjęci.
- W szczegółach ucznia widać zdarzenia kursu i globalne; propozycja powstała po quizie w innym kursie jest tam niewidoczna, choć jej przyjęcie (globalne) widać. Tak samo `attention_needed` — wpis ma kurs i lekcję wyniku, który dał serię; stan `attention` (z wszystkich kursów) widać zawsze.
- Statystyki ucznia (`/me/stats`, tabela form) liczą wszystkie jego wyniki, także z kursu, z którego został potem odrzucony; statystyki kursu — tylko uczniów obecnie przyjętych.
