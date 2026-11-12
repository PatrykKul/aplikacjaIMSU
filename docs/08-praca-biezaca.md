# Praca bieżąca

Specyfikacja tego, co teraz robimy. Po zakończeniu: wynik trafia do `moduly/<nr>-<moduł>.md`, decyzje do `04-decyzje.md`, status do `05-plan-etapow.md` i `00-START.md`, a ten plik czyścimy (historia w gicie).

---

# Etap 9 — IMSU v3: przebudowa adaptacji (12.11.2026)
Status: **szkic — do akceptacji Patryka**

Zlecenie: `..\ZADANIE-CLAUDE-CODE-IMSU-v3.md` (12.11). Przebudowa uzgodniona z Bartkiem: wolno zmieniać cały kod (także `curriculum`, `content`, `identity`, frontend), usuwać klasy i przebudować edytor. Dla tego etapu **nie obowiązuje D5** (kod pisze i commituje AI na gałęzi `feat/v3-adaptacja`, bez pushu). Zmiana cudzego kodu (moduły `learning_style` i `assessment` Bartka, etap 4) — w całości, opisana niżej.

## Odpowiedzialność

System, który da się w całości zrozumieć i obronić na pokazie:
- uczy w **jednym** stylu VAK naraz (bez mieszania i bez zwiniętych materiałów),
- każda lekcja ma tę samą treść w **trzech wersjach** (V / A / K) i jeden quiz z **puli** pytań,
- widzi, że w danej formie uczniowi nie idzie, i proponuje zmianę **z argumentami z danych**,
- zapisuje statystyki i **każdą decyzję** w dzienniku; nauczyciel widzi skuteczność form w swoim kursie.

Zasada nadrzędna: **zero decyzji „z niczego”** — każda reakcja systemu wynika z reguły w czystej funkcji (`learning_style/rules.py`) i niesie liczby, z których wynika.

## Analiza (obecny kod, co zmieniamy)

| Obszar | Teraz (v2) | v3 |
|---|---|---|
| Dostęp do kursów | katalog opublikowanych + klasy (`classrooms`, D10, D34–D38) | **zapisy na kurs** z akceptacją nauczyciela; **klasy usunięte w całości** |
| Konto nauczyciela | działa od razu | **wymaga zatwierdzenia przez administratora** |
| Lekcja | bloki tekstu i załączniki z formami ⊆ {V, A, K}, materiały innych stylów zwinięte | zarys + **3 wersje** (V / A / K) + wnioski; uczeń widzi jedną wersję; załącznik bez `forms` |
| Kolejność | wszystkie lekcje dostępne | **lekcja n+1 po zaliczeniu quizu lekcji n** (serwer) |
| Quiz | stały zestaw do 20 pytań, pytania o formy | **pula ≥ 5 pytań** z wyjaśnieniami, losowo **5** na podejście, zestaw zapisany na serwerze |
| Styl | `V`, `VA`, `VAK`…, wagi 0–30, styl efektywny z rozwinięć | **jeden** styl (V, A albo K) + **profil procentowy** (suma 100, min. 5%) |
| Adaptacja | ±1 do wag, propozycja przy samodzielnym liderze wag | reguły z tabeli §7 zadania: sugestia „przerób w formie X”, propozycja zmiany na stałe (tylko forma **potwierdzona wynikami**), okres próbny 2 lekcji, podpowiedź z kursu |
| Uzasadnienia | gotowe polskie zdania z backendu (wyjątek od D3) | backend zwraca **kody i liczby**, zdania składa frontend — wyjątek od D3 znika |
| Dziennik | brak (tylko próby quizów) | `decision_events` — każde zdarzenie z danymi; uczeń i nauczyciel go widzą |
| Statystyki | brak | „Moje postępy” ucznia, panel kursu nauczyciela |

Co usuwamy:
- backend: `curriculum/classrooms.py`, `classrooms_router`, modele i tabele `classrooms`, `classroom_students`, `classroom_courses`, `GET /students?email=` (służył tylko klasom), `learning_style/personalization.py` (zwijanie, styl efektywny), `adaptation.py` (zastępuje `rules.py`), tabele `material_openings` i `quiz_attempts` (stara postać), endpointy `personalized-blocks`, `blocks/{id}/open`, `GET/PUT /lessons/{id}/blocks`, testy tych funkcji;
- frontend: `features/classes`, komponenty klas w `features/teach`, trasy `/classes/**`, `/teach/classes/**`, `CollapsedMaterial`, `PersonalizationNote`, `FormBadge` przy załącznikach (zostaje jako etykieta formy w zakładkach i quizie, jeśli potrzebna), pole „Formy” w oknie załącznika;
- dane demo: klasa „Klasa 7a”, stare kursy 7-lekcyjne (zastępuje je nowy zestaw 3 × 4 lekcje);
- dokumentacja: opisy klas i zwijania (decyzje D10, D13 w części form, D15–D19, D34–D38 oznaczone jako zastąpione).

Bez zmian: rejestracja/logowanie i sesja (D8), administracja kont i blokada (D9), edytor TipTap (D12, D23, D25), pliki (D24, D28), ankieta 20 pytań z neutralnymi formami, palety i zasady wyglądu (`07-design.md`), struktura modułów i katalogów.

## Model danych (tabele, pola, migracje)

Jedna migracja `v3_adaptation` (po `f3c3eff41f5a`), z `downgrade` przywracającym strukturę v2 (bez danych usuniętych tabel). Dane v2 **nie są przenoszone** poza kontami, kursami, lekcjami, plikami i ankietami: lokalne bazy obu autorów przebudowujemy (`alembic downgrade base`, `alembic upgrade head`, seed). Przy migracji istniejące bloki lekcji stają się wersją V (z `forms` usuniętym z załączników), lekcje są nieopublikowane, profile i próby quizów v2 są usuwane (niezgodne z nowym modelem — styl wieloliterowy, wagi).

### `identity`
| Tabela | Zmiana |
|---|---|
| `users` | + `approval_status` (`approved` / `pending` / `rejected`, `CHECK`, domyślnie `approved`); rejestracja nauczyciela ustawia `pending`; uczeń, administrator i nauczyciel założony przez administratora — `approved` |

### `curriculum`
| Tabela | Kolumny |
|---|---|
| `courses` | + `summary` (JSONB, TipTap albo `null`) — „Podsumowanie i wnioski” kursu |
| `lessons` | + `outline` (JSONB, „Zarys”), + `conclusions` (JSONB, „Wnioski”), + `is_published` (false) |
| `enrollments` (nowa) | `id`, `course_id` → `courses` (CASCADE), `student_id` → `users` (CASCADE, indeks), `status` (`pending` / `accepted` / `rejected`, `CHECK`), `requested_at`, `decided_at` (null); unikalne (`course_id`, `student_id`) |
| `lesson_completions` (nowa) | `user_id` → `users` (CASCADE), `lesson_id` → `lessons` (CASCADE), `passed_at`; PK (`user_id`, `lesson_id`) — pierwsze zaliczenie lekcji (podstawa odblokowania) |
| `classrooms`, `classroom_students`, `classroom_courses` | **usunięte** |

### `content`
| Tabela | Kolumny |
|---|---|
| `lesson_contents` | + `form` (`V` / `A` / `K`, `CHECK`); unikalne (`lesson_id`, `form`) zamiast unikalnego `lesson_id` — jeden wiersz na wersję lekcji |

Blok `attachment` traci pole `forms` (formę wyznacza wersja). Rodzaje i walidacja plików bez zmian.

### `assessment`
| Tabela | Kolumny |
|---|---|
| `lesson_quizzes` | `questions` (JSONB) — pytanie: `id`, `text`, `answers` (3–4), `correct_answer_id`, **`explanation`** (1–1000 znaków, wymagane); bez `form`; pula 1–50 pytań (do publikacji min. 5) |
| `quiz_draws` (nowa) | `id`, `user_id` → `users` (CASCADE), `lesson_id` → `lessons` (CASCADE), `question_ids` (JSONB, 5 identyfikatorów w kolejności pokazania), `answers` (JSONB, null do wysłania), `percent` (null do wysłania), `created_at`, `submitted_at` (null = podejście otwarte); indeks (`user_id`, `lesson_id`) — wylosowany zestaw: klucz zostaje na serwerze, ocena tylko wobec tego zestawu |

### `learning_style`
| Tabela | Kolumny |
|---|---|
| `survey_questions`, `survey_answers`, `survey_results` | bez zmian (`dominant_style` przy remisie zapisuje litery remisu, np. `VA`) |
| `learning_profiles` | `user_id` (PK), `style` (`V` / `A` / `K` albo `null` = remis nierozstrzygnięty), `style_source` (`survey` / `tie_choice` / `manual` / `proposal`), `percent_v`, `percent_a`, `percent_k` (`CHECK` każde 5–90 i suma = 100), `updated_at`; usunięte `weight_*`, `rejected_proposal` |
| `style_history` (nowa) | `id`, `user_id`, `percent_v/a/k`, `style`, `event_id` → `decision_events` (SET NULL), `created_at` — stan profilu po każdej zmianie (wykres) |
| `quiz_results` (nowa, zastępuje `quiz_attempts`) | `id`, `user_id`, `course_id`, `lesson_id`, `draw_id` → `quiz_draws` (SET NULL), `form`, `percent`, `passed`, `counted` (czy zmieniło procenty), `created_at`; indeksy (`user_id`, `lesson_id`), (`course_id`) — **wynik w modelu ucznia** (S z wykładu) |
| `lesson_forms` (nowa) | `user_id`, `lesson_id`, `form`, `updated_at`; PK (`user_id`, `lesson_id`) — jawny wybór formy lekcji („Przerób tę lekcję w innej formie”); brak wiersza = forma = aktywny styl |
| `style_proposals` (nowa) | `id`, `user_id`, `kind` (`switch` / `revert`), `from_style`, `to_style`, `evidence` (JSONB), `status` (`open` / `accepted` / `rejected` / `expired` / `superseded`), `counted_at_decision` (liczba policzonych wyników ucznia w chwili decyzji), `created_at`, `decided_at`; częściowy indeks unikalny: najwyżej jedna `open` na ucznia |
| `style_trials` (nowa) | `id`, `user_id`, `from_style`, `to_style`, `source` (`proposal` / `manual`), `before_average` (null = brak danych), `after_average`, `result` (`helped` / `neutral` / `worse` / `no_baseline`, null do końca), `started_at`, `finished_at` (null = trwa) |
| `decision_events` (nowa) | `id`, `user_id` (CASCADE), `type` (40), `course_id` (SET NULL), `lesson_id` (SET NULL), `data` (JSONB), `created_at`; indeksy (`user_id`, `created_at`), (`course_id`) — **dziennik decyzji** |
| `material_openings`, `quiz_attempts` | **usunięte** |

Zasady zależności bez zmian (`03-architektura.md` §3): `core` ← `identity` ← `curriculum` ← `content` ← `learning_style` ← `assessment` ← **`authoring`** (nowy, cienki moduł publikacji lekcji). Klucze obce między modułami — tylko w bazie. Odblokowanie lekcji należy do `curriculum` (`lesson_completions`), więc blokada nie wymaga zależności „w górę”: `learning_style.hooks` po zaliczeniu woła `curriculum.service.mark_lesson_passed`.

## Logika (reguły, algorytmy)

Wszystkie reguły adaptacji w **jednym** module czystych funkcji `backend/app/modules/learning_style/rules.py` (bez SQLAlchemy i FastAPI; wejście: proste struktury, wyjście: decyzja + dane uzasadnienia). Losowanie pytań — `assessment/drawing.py`, braki do publikacji — `content/readiness.py`, `assessment/readiness.py`, `curriculum/readiness.py`, agregaty statystyk — `learning_style/stats.py`.

### Stałe
```
FORMS = ("V", "A", "K")          # kolejność rozstrzygania remisów
PASS_THRESHOLD = 70              # zaliczenie: percent >= 70
STEP = 10                        # zmiana procentu formy po policzonym wyniku
MIN_PERCENT = 5                  # każda forma >= 5, więc maks. 90
QUIZ_SIZE = 5                    # pytań na podejście; pula do publikacji >= 5
TRIAL_LESSONS = 2                # okres próbny po zmianie stylu
REVERT_DROP = 10                 # spadek średniej (pkt proc.), od którego proponujemy powrót
RENEW_AFTER = 2                  # nowe policzone wyniki, po których wraca odrzucona propozycja
HINT_MIN_STUDENTS = 2            # podpowiedź z kursu: min. uczniów w danej formie
```
Wynik quizu przy 5 pytaniach: 0, 20, 40, 60, 80, 100% → zaliczenie od 4/5.

### R1. Profil z ankiety — `survey_percentages(points) -> Percentages`
- `raw[f] = points[f] / suma * 100`; formy z `raw < 5` dostają 5, reszta (100 − 5·m) dzielona proporcjonalnie do `raw` pozostałych; zaokrąglenie **metodą największych reszt** (podłoga, brakujące jednostki dla największych części ułamkowych; remis reszt → kolejność V, A, K). Suma zawsze 100.
- Przykłady: A 11 / V 6 / K 3 → **A 55, V 30, K 15**; V 9 / A 8 / K 3 → V 45, A 40, K 15; V 20 / A 0 / K 0 → V 90, A 5, K 5.
- `survey_leaders(points) -> list[str]`: formy z maksimum punktów. Jedna → styl = ta forma (`style_source = survey`). Kilka → `style = null`, uczeń wybiera jeden z remisujących na ekranie wyniku (`tie_choice`); do wyboru kursy są niedostępne (`SURVEY_REQUIRED`).

### R2. Zmiana po quizie — `apply_result(percentages, form, passed) -> Percentages`
- `new[form] = clamp(p[form] ± 10, 5, 90)`; pozostałe dwie formy dzielą `100 − new[form]` **proporcjonalnie do swoich poprzednich wartości**; forma poniżej 5 → 5, druga bierze resztę; zaokrąglenie jak w R1.
- Przykłady (sprawdzane w testach):
  - V 45 / A 40 / K 15, V niezaliczone → **V 35 / A 47 / K 18** (A 47,27 → 47, K 17,73 → 18);
  - V 35 / A 47 / K 18, A zaliczone → **V 28 / A 57 / K 15**;
  - V 85 / A 10 / K 5, V zaliczone → V 90 / A 5 / K 5 (limit 90 i min. 5);
  - V 5 przy niezaliczeniu w V → bez zmian (już minimum) — wynik zapisany jako policzony, delta 0.
- `is_counted(previous_forms_in_lesson, form) -> bool`: liczy się **tylko pierwsze podejście w danej formie w danej lekcji** (zaliczone albo nie). Kolejne podejścia w tej samej formie — zapisane, bez zmiany procentów.

### R3. Statystyki form ucznia — `form_stats(results) -> dict[form, FormStats]`
- Na podstawie **policzonych** wyników ucznia ze wszystkich kursów: `lessons` (liczba lekcji), `average` (średnia procentów, zaokrąglona, `null` bez danych).
- `confirmed[f]`: co najmniej jedno **zaliczone** podejście w formie `f` (także niepoliczone) → „potwierdzona wynikami”, inaczej „tylko z ankiety”.

### R4. Quiz zaliczony — odblokowanie i pochwała
- Każde zaliczone podejście (≥ 70%, dowolne) zapisuje `lesson_completions` (raz); następna **opublikowana** lekcja kursu staje się dostępna.
- `praise(counted_results) -> Praise | None`: końcowa seria policzonych wyników **zaliczonych w tej samej formie** co bieżący; pochwała, gdy bieżący wynik jest zaliczony, policzony i seria ≥ 2 → `{form, streak, average}`, np. „3 lekcje z rzędu zaliczone w formie wzrokowej, średnio 87%” (80, 100, 80).

### R5. Quiz niezaliczony — sugestia „przerób w formie X” — `retry_suggestion(failed_form, percentages, stats, survey_percentages, results) -> RetrySuggestion`
- Kandydaci: dwie formy ≠ formy, w której uczeń właśnie przerabiał lekcję.
- Jeśli któryś kandydat jest **potwierdzony** (R3): X = potwierdzony z najwyższym procentem; remis → wyższa `average`; remis → V, A, K. `reason = "confirmed"`, dowód: najlepszy zaliczony wynik w X (`lesson_title`, `percent`) i procent X.
- Inaczej: X = kandydat z najwyższym procentem **w ankiecie** (druga forma ankiety); remis → wyższy bieżący procent; remis → V, A, K. `reason = "survey"`, dowód: procent X w ankiecie.
- Zawsze dołączone dane formy oblanej: wynik tego quizu i poprzedni policzony wynik w tej formie w innej lekcji (`null`, gdy brak).
- Teksty (frontend): „Wzrokowe: ten quiz 40%, poprzednia lekcja 40%. Słuchowe zaliczyłeś w lekcji 1 na 80%” / „Słuchowe były drugie w Twojej ankiecie (40%), nie mamy jeszcze o nich wyników – warto sprawdzić”.
- Akcja: jeden przycisk „Przerób tę lekcję w formie X” → zapis wyboru formy lekcji (`source = suggestion`) i nowy zestaw pytań. Sugestia trafia do dziennika przy każdym niezaliczonym podejściu.

### R6. Propozycja zmiany stylu na stałe — `switch_proposal(style, percentages, stats, rejections, trial_active) -> ProposalDraft | None`
- Warunek: istnieje forma Y ≠ aktywny styl, **potwierdzona** (R3) i z **wyższym procentem** niż aktywny styl. Kilka → najwyższy procent, remis → wyższa `average`, remis → V, A, K.
- Nie proponujemy: w trakcie okresu próbnego (R7); gdy Y było odrzucone i od odrzucenia uczeń ma **mniej niż 2 nowe policzone wyniki** (`RENEW_AFTER`); gdy jest już otwarta propozycja tej samej formy.
- Dowód: `{from: {form, lessons, average, percent}, to: {form, lessons, average, percent}}` → „Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%”.
- Otwarta propozycja, której warunek przestał obowiązywać (albo wskazuje inną formę), dostaje status `expired` przy następnej ocenie. Ręczna zmiana stylu zamyka otwartą propozycję (`superseded`).
- Uczeń przyjmuje (styl = Y, `style_source = proposal`, start okresu próbnego) albo odrzuca (status `rejected`, `counted_at_decision` = bieżąca liczba policzonych wyników).

### R7. Okres próbny — `trial_outcome(before_average, after_results) -> TrialOutcome | None`
- Start przy **każdej** zmianie aktywnego stylu: przyjęta propozycja `switch` albo zmiana ręczna (bez okresu po przyjęciu propozycji powrotu — żeby nie było pętli).
- `before_average`: średnia z ostatnich ≤ 2 policzonych wyników w **poprzednim** stylu sprzed zmiany (`null`, gdy brak).
- Liczą się policzone wyniki w **nowym** stylu po starcie; po 2 → koniec: `after_average`, `diff = after − before`:
  - `diff > 0` → `helped` („Zmiana pomogła: średnia 40% → 90%”),
  - `−10 < diff ≤ 0` → `neutral` („Bez wyraźnej różnicy: 60% → 55%”),
  - `diff ≤ −10` → `worse` + **propozycja powrotu** (`kind = revert`, do poprzedniego stylu, bez wymogu potwierdzenia; odrzucona — jak w R6),
  - `before = null` → `no_baseline` („Średnia w nowej formie: 85%”).

### R8. Podpowiedź z kursu — `course_hint(course_results_of_others) -> CourseHint | None`
- Dla ucznia **bez żadnego wyniku w kursie**: policzone wyniki innych uczniów tego kursu pogrupowane po formie; formy z ≥ 2 uczniami; najwyższa średnia, remis → więcej uczniów → V, A, K → `{form, average, students}`: „W tym kursie najlepiej wypada forma słuchowa (średnio 85%, 3 uczniów)”. Bez automatycznej zmiany; `null`, gdy brak danych.

### R9. Losowanie pytań — `assessment/drawing.py: draw_questions(pool_ids, last_ids, k=5, rng) -> list[str]`
- Najpierw pytania spoza ostatniego wysłanego zestawu (losowo), potem uzupełnienie z ostatniego (losowo), razem `min(k, len(pool))`. Pula 8: powtórka daje 3 nowe + 2 z poprzedniego. `rng` wstrzykiwany (testy deterministyczne).
- Otwarty zestaw (niewysłany) jest zwracany ponownie — odświeżenie strony nie losuje od nowa.

### R10. Blokada lekcji (`curriculum/progress.py`)
- `lesson_states(published_lessons, passed_ids) -> list[state]`: lekcja jest `passed`, gdy uczeń ją zaliczył; `available`, gdy jest pierwsza albo poprzednia opublikowana jest zaliczona; inaczej `locked` (z numerem wymaganej lekcji). Zaliczona lekcja zostaje dostępna także po zmianie kolejności przez nauczyciela.
- Egzekwowane na serwerze przy każdym dostępie ucznia do treści i quizu lekcji: `403 LESSON_LOCKED` z danymi wymaganej lekcji.

### R11. Gotowość lekcji do publikacji
- `curriculum`: `OUTLINE_MISSING`, `CONCLUSIONS_MISSING` (pusty dokument TipTap = brak).
- `content`, dla każdej wersji: `VERSION_EMPTY`; V — `V_VISUAL_MISSING` (min. 1 tekst i 1 obraz albo wideo); A — `A_AUDIO_MISSING` (min. 1 nagranie: plik albo tekst lektora) i `A_DESCRIPTION_MISSING` (min. 1 blok tekstu — krótki opis); K — `K_INSTRUCTION_MISSING` (min. 1 blok tekstu z instrukcją) i `K_WORKSHEET_MISSING` (min. 1 PDF — karta zadania).
- `assessment`: `QUIZ_TOO_FEW_QUESTIONS` (`count`, `min = 5`).
- Opublikowana lekcja nie może stać się niekompletna: zapis, który wprowadziłby brak, → `409 PUBLISHED_LESSON_INCOMPLETE` z listą braków (najpierw wycofanie publikacji).

### Kolejność w `hooks.record_quiz_result` (jedno wywołanie z `assessment` po ocenie)
1. Forma = forma lekcji w chwili wysłania (`lesson_forms` albo aktywny styl).
2. `counted = is_counted(...)`; zapis `quiz_results`; jeśli `counted` → `apply_result`, zapis profilu i `style_history`.
3. Zaliczone → `curriculum.mark_lesson_passed` (odblokowanie następnej), `praise`.
4. Niezaliczone → `retry_suggestion`.
5. Okres próbny: aktualizacja / zakończenie (R7), ewentualna propozycja powrotu.
6. `switch_proposal` (R6) — wygaszenie nieaktualnej, utworzenie nowej.
7. Zdarzenia w dzienniku (każde z danymi), jeden `commit`, zwrot `QuizFeedback`.

### Dziennik decyzji — typy zdarzeń i `data`
| `type` | `data` |
|---|---|
| `survey_completed` | `points`, `percentages`, `style` (null przy remisie), `tie_styles` |
| `tie_resolved` | `style`, `tie_styles` |
| `quiz_attempt` | `draw_id`, `form`, `percent`, `passed`, `counted`, `percentages_before`, `percentages_after`, `unlocked_lesson` (`id`, `title`, `number`) / null |
| `retry_suggestion` | `failed`: {`form`, `percent`, `previous`: {`lesson_id`, `lesson_title`, `percent`} / null}, `suggested`: {`form`, `reason`, `percent`, `survey_percent`, `best`: {`lesson_id`, `lesson_title`, `percent`} / null} |
| `lesson_form_changed` | `from`, `to`, `source` (`manual` / `suggestion`) |
| `proposal_created` | `proposal_id`, `kind`, `from`, `to`, `evidence` |
| `proposal_accepted` / `proposal_rejected` / `proposal_expired` | `proposal_id`, `kind`, `from`, `to` |
| `manual_style_change` | `from`, `to` |
| `trial_started` | `trial_id`, `from`, `to`, `source`, `before_average` |
| `trial_finished` | `trial_id`, `from`, `to`, `before_average`, `after_average`, `result` |

Każde zdarzenie ma `course_id` / `lesson_id`, gdy dotyczy kursu / lekcji; zmiany stylu i ankieta są globalne (`null`).

### Statystyki (`learning_style/stats.py`, czyste funkcje)
- Uczeń: historia procentów (`style_history`), postęp kursów (zaliczone / opublikowane lekcje), wyniki lekcji (wszystkie podejścia z formą, pierwsze policzone wyróżnione).
- Kurs: **skuteczność form** — dla V / A / K: średnia policzonych wyników, liczba policzonych wyników, liczba wszystkich podejść, liczba uczniów; **rozkład stylów** zapisanych uczniów (V / A / K / bez stylu); tabela uczniów: styl, procenty, postęp, średnia policzonych wyników w kursie, ostatnia aktywność (ostatni wynik w kursie), otwarta propozycja.

## API (endpointy, uprawnienia, kody błędów)

Format błędów: `AppError(status, code, **params)` → `{"code": "...", ...params}` (rozszerzenie `core/errors.py`). Teksty dla użytkownika składa frontend z kodów i liczb (D3 bez wyjątku). `Percentages` = `{"V": int, "A": int, "K": int}`; `Form` = `"V" | "A" | "K"`; daty ISO 8601. Wszystkie odpowiedzi w snake_case.

### `identity`
| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `POST /auth/register` | każdy | jak dotąd; nauczyciel dostaje `approval_status = pending` | 409, 422 |
| `POST /auth/login` | każdy | także nauczyciel `pending` / `rejected` (frontend pokazuje ekran oczekiwania / odrzucenia) | 401 |
| `GET /auth/me` | zalogowany | `UserResponse` + `approval_status` | 401 |
| `GET /users?role=&approval=` | admin | jak dotąd; opcjonalny filtr `approval` (`pending` / `approved` / `rejected`) | 403, 422 |
| `POST /users`, `PATCH /users/{id}` | admin | jak dotąd (nauczyciel od administratora — `approved`) | 404, 409, 422 |
| `POST /users/{id}/approve` | admin | nauczyciel → `approved`, `UserResponse` (powtórka bez zmian) | 404 `USER_NOT_FOUND` (nie nauczyciel) |
| `POST /users/{id}/reject` | admin | nauczyciel → `rejected` | 404 |
| ~~`GET /students?email=`~~ | — | usunięty | |

`TeacherUser` wymaga `approval_status = approved`, inaczej `403 TEACHER_NOT_APPROVED` (dla każdego endpointu nauczyciela).

### `curriculum`
| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /courses` | zalogowany | uczeń: katalog (opublikowane + te, na które jest przyjęty) `CourseSummaryResponse[]`; nauczyciel: swoje; admin: wszystkie | 401 |
| `POST /courses` | nauczyciel | `{title, description?}` → 201 | 403, 422 |
| `GET /courses/{id}` | widzący kurs | `CourseResponse` | 404 |
| `PATCH /courses/{id}` | autor | `title?`, `description?`, `introduction?`, `summary?`, `is_published?` | 404, 409 `COURSE_HAS_NO_PUBLISHED_LESSONS` |
| `DELETE /courses/{id}` | autor | archiwizacja, 204 | 404 |
| `POST /courses/{id}/lessons` | autor | `{title}` → 201, lekcja nieopublikowana na końcu | 404 |
| `PUT /courses/{id}/lessons/order` | autor | `{lesson_ids}` | 400 `LESSON_ORDER_MISMATCH` |
| `GET /lessons/{id}` | widzący, uczeń: przyjęty + odblokowana | `LessonResponse` | 404, 403 `ENROLLMENT_REQUIRED`, 403 `LESSON_LOCKED` + `required_lesson` {`id`, `title`, `number`} |
| `PATCH /lessons/{id}` | autor | `title?`, `outline?`, `conclusions?` | 404, 409 `PUBLISHED_LESSON_INCOMPLETE` + `issues` |
| `DELETE /lessons/{id}` | autor | archiwizacja, 204 | 404 |
| `POST /courses/{id}/enrollment` | uczeń | prośba o zapis → 201 `EnrollmentResponse` (`pending`); ponowna przy `pending` → 200 bez zmian; po `rejected` → znów `pending` | 404, 409 `ALREADY_ENROLLED` |
| `GET /courses/{id}/enrollments?status=` | autor | `[{student: {id, display_name, email}, status, requested_at, decided_at}]`, od najstarszej prośby | 404 |
| `POST /courses/{id}/enrollments/{student_id}/accept` / `reject` | autor | decyzja → `EnrollmentResponse` (powtórka bez zmian) | 404 `ENROLLMENT_NOT_FOUND` |

Schematy:
- `CourseSummaryResponse`: `id`, `title`, `description`, `owner` {`id`, `display_name`}, `is_published`, `is_archived`, `lesson_count` (opublikowane; autor: wszystkie), `enrollment_status` (uczeń: `null` / `pending` / `accepted` / `rejected`), `progress` (uczeń przyjęty: {`passed`, `total`}, inaczej `null`), `pending_requests` (autor: liczba próśb, inaczej `null`), `updated_at`.
- `CourseResponse`: pola podsumowania + `introduction`, `summary`, `lessons`: [{`id`, `title`, `number` (1…), `outline`, `is_published` (autor), `state` (uczeń przyjęty: `passed` / `available` / `locked`, inaczej `null`), `required_lesson_number` (gdy `locked`)}]. Uczeń widzi tylko opublikowane lekcje (streszczenie kursu = wstęp + zarysy lekcji).
- `LessonResponse`: `id`, `title`, `number`, `outline`, `conclusions`, `is_published`, `course` {`id`, `title`, `owner_id`}, `previous_lesson_id`, `next_lesson_id` (sąsiednie opublikowane dla ucznia), `next_lesson_unlocked` (uczeń).
- `EnrollmentResponse`: `course_id`, `status`, `requested_at`, `decided_at`.

Widoczność: uczeń widzi kurs opublikowany albo taki, na który jest przyjęty (niezarchiwizowany); treść lekcji tylko przy `accepted` i lekcji odblokowanej. Serwis dla innych modułów: `get_visible_course`, `get_owned_course`, `get_study_lesson(db, lesson_id, user)` (uczeń: przyjęty + opublikowana + odblokowana; autor i admin — zawsze), `get_owned_lesson`, `mark_lesson_passed(db, user_id, lesson_id) -> UnlockedLesson | None`, `accepted_student_ids(db, course_id)`, `course_progress(db, course_id, user_id)`, `lesson_issues(lesson)`.

### `content`
| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/versions` | autor, admin | `{"V": {"blocks": [...]}, "A": {...}, "K": {...}}` (pusta lista dla brakującej wersji) | 404 |
| `PUT /lessons/{id}/versions/{form}` | autor | `{blocks}` → `{blocks}` | 422, 400 `FILE_NOT_FOUND` / `FILE_KIND_MISMATCH`, 409 `PUBLISHED_LESSON_INCOMPLETE` + `issues` |
| `POST /files`, `GET /files/{id}` | jak dotąd | | |

Serwis: `get_version(db, lesson_id, form) -> list[Block]`, `version_issues(db, lesson_id) -> list[Issue]`. Uczeń dostaje wersję przez `learning_style` (`/study`).

### `assessment`
| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/quiz/edit` | autor, admin (odczyt) | `{questions: [{id, text, answers, correct_answer_id, explanation}]}` | 404 |
| `PUT /lessons/{id}/quiz` | autor | zapis puli (1–50 pytań) | 422, 404, 409 `PUBLISHED_LESSON_INCOMPLETE` (< 5 przy opublikowanej) |
| `DELETE /lessons/{id}/quiz` | autor | 204 | 404, 409 (opublikowana) |
| `GET /lessons/{id}/quiz` | uczeń (ankieta, przyjęty, odblokowana) | otwarte podejście albo nowe losowanie: `{draw_id, questions: [{id, text, answers}], pool_size, form}` — **bez klucza** | 403 `SURVEY_REQUIRED` / `ENROLLMENT_REQUIRED` / `LESSON_LOCKED`, 404 `QUIZ_NOT_FOUND`, 403 `FORBIDDEN` (inne role) |
| `POST /lessons/{id}/quiz/attempts` | uczeń | `{draw_id, answers: {question_id: answer_id}}` → `AttemptResponse` | 409 `DRAW_NOT_OPEN`, 400 `QUIZ_INCOMPLETE` / `QUIZ_ANSWER_MISMATCH` |

`AttemptResponse`: `draw_id`, `percent`, `correct_count`, `total`, `passed`, `results`: [{`question_id`, `text`, `answers`, `chosen_answer_id`, `correct_answer_id`, `correct`, `explanation`}], `feedback`: `QuizFeedback`.

### `learning_style`
| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /survey/questions` | zalogowany | bez zmian (bez klucza) | |
| `POST /survey/answers` | uczeń | wynik → `LearningProfileResponse`; ankieta **raz** | 409 `SURVEY_ALREADY_DONE`, 400 jak dotąd |
| `GET /profile/learning-style` | zalogowany | `LearningProfileResponse` (nie-uczeń: `survey_completed = false`) | |
| `POST /profile/learning-style/tie-choice` | uczeń | `{style}` — tylko przy nierozstrzygniętym remisie i stylu z remisu | 409 `NO_TIE`, 400 `STYLE_NOT_TIED` |
| `PUT /profile/learning-style` | uczeń | `{style}` → zmiana ręczna (procenty bez zmian, okres próbny, otwarta propozycja → `superseded`) | 403 `SURVEY_REQUIRED`, 409 `SAME_STYLE` |
| `POST /profile/learning-style/proposals/{id}/accept` / `reject` | uczeń | decyzja → `LearningProfileResponse` | 404 `PROPOSAL_NOT_FOUND`, 409 `PROPOSAL_NOT_OPEN` |
| `GET /lessons/{id}/study` | uczeń (jak quiz), autor/admin: 403 `FORBIDDEN` | `StudyResponse` | 403 `SURVEY_REQUIRED` / `ENROLLMENT_REQUIRED` / `LESSON_LOCKED`, 404 |
| `PUT /lessons/{id}/study/form` | uczeń | `{form, source: "manual" \| "suggestion"}` → `StudyResponse` (zdarzenie `lesson_form_changed`; ta sama forma → bez zmian) | jak wyżej |
| `GET /courses/{id}/hint` | uczeń przyjęty | `CourseHint` albo `null` (R8) | 404, 403 `ENROLLMENT_REQUIRED` |
| `GET /me/progress` | uczeń | `ProgressResponse` | 403 `FORBIDDEN` |
| `GET /me/journal` | uczeń | `JournalEntry[]` od najnowszego | 403 |
| `GET /courses/{id}/stats` | autor | `CourseStatsResponse` | 404 |
| `GET /courses/{id}/students/{student_id}` | autor (uczeń przyjęty w kursie) | `StudentDetailResponse` | 404 `STUDENT_NOT_FOUND` |

Schematy:
- `LearningProfileResponse`: `survey_completed`, `style` (`Form` / null), `style_source`, `tie_styles` (lista, niepusta tylko przy nierozstrzygniętym remisie), `percentages`, `forms`: {`V`: {`confirmed`, `lessons`, `average`}, …}, `survey`: {`points`, `percentages`, `created_at`} / null, `open_proposal`: `Proposal` / null, `trial`: `Trial` / null (trwający albo ostatni zakończony).
- `Proposal`: `id`, `kind`, `from`, `to`, `evidence`, `created_at`. `Trial`: `id`, `from`, `to`, `source`, `before_average`, `after_average`, `result`, `done` (liczba wyników w okresie), `needed` (2), `started_at`, `finished_at`.
- `StudyResponse`: `lesson_id`, `form`, `form_source` (`style` / `choice`), `style`, `blocks` (wersja w formie `form`), `other_forms`, `suggestion`: `RetrySuggestion` / null (z ostatniego niezaliczonego podejścia w tej lekcji, gdy jego forma ≠ bieżąca), `last_result`: {`percent`, `passed`, `form`} / null.
- `QuizFeedback`: `form`, `counted`, `percentages_before`, `percentages_after`, `passed`, `unlocked_lesson` {`id`, `title`, `number`} / null, `course_completed`, `praise` {`form`, `streak`, `average`} / null, `suggestion`: `RetrySuggestion` / null, `proposal`: `Proposal` / null (otwarta po tym podejściu), `trial`: `Trial` / null (trwający lub zakończony tym podejściem).
- `RetrySuggestion`: jak `data` zdarzenia `retry_suggestion`.
- `CourseHint`: `form`, `average`, `students`, `results`.
- `ProgressResponse`: `history`: [{`at`, `percentages`, `style`}], `courses`: [{`id`, `title`, `passed`, `total`, `next_lesson` {`id`, `title`, `number`} / null}], `lessons`: [{`course_id`, `course_title`, `lesson_id`, `lesson_title`, `number`, `passed`, `attempts`: [{`at`, `form`, `percent`, `passed`, `counted`}]}].
- `JournalEntry`: `id`, `type`, `at`, `course` {`id`, `title`} / null, `lesson` {`id`, `title`} / null, `data`.
- `CourseStatsResponse`: `forms`: {`V`: {`average`, `counted_results`, `attempts`, `students`}, …}, `styles`: {`V`, `A`, `K`, `none`}, `students`: [{`id`, `display_name`, `email`, `style`, `percentages`, `passed`, `total`, `average`, `last_activity`, `open_proposal` {`to`, `kind`} / null}], `pending_requests`.
- `StudentDetailResponse`: `student` {`id`, `display_name`, `email`}, `profile` (`LearningProfileResponse`), `history`, `lessons` (jak w `ProgressResponse`, tylko ten kurs), `journal` (zdarzenia tego kursu + globalne zmiany stylu i ankieta).

### `authoring` (nowy moduł, najwyżej w zależnościach)
| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/readiness` | autor | `{ready, issues: [{area: "lesson" \| "V" \| "A" \| "K" \| "quiz", code, count?, min?}]}` | 404 |
| `PUT /lessons/{id}/publication` | autor | `{is_published}` → `LessonResponse` | 409 `LESSON_NOT_READY` + `issues`, 409 `LAST_PUBLISHED_LESSON` (wycofanie ostatniej opublikowanej lekcji opublikowanego kursu) |

### Usuwane endpointy
`/classrooms/**`, `GET /students`, `GET`/`PUT /lessons/{id}/blocks`, `GET /lessons/{id}/personalized-blocks`, `POST /lessons/{id}/blocks/{block_id}/open`, `DELETE /profile/learning-style`, `POST /profile/learning-style/proposal/accept|reject`.

## Frontend (ekrany, komponenty)

Zasady bez zmian: `06-konwencje.md`, `07-design.md` (paleta, tokeny form, kontrolki shadcn, karty tylko tam, gdzie były; statystyki jako **tabele i wykres liniowy**, bez kolorowych badge'y i kafelków wszędzie). Wykres procentów — własny komponent SVG (bez nowej biblioteki): trzy linie w kolorach form z literą i nazwą przy końcu linii, oś 0–100%, punkty po zdarzeniach, pod spodem tabela tych samych danych (dostępność). Teksty decyzji składa jeden moduł `features/learning-style/explain.ts` (kody → zdania), używany przez ucznia i nauczyciela.

### Uczeń (menu: „Kursy”, „Moje postępy”, „Mój styl”)
| Ekran | Zawartość i przepływ |
|---|---|
| `/survey`, `/survey/result` | ankieta jak dotąd; wynik: procenty V / A / K (`StyleBars`), styl; **remis** → `RadioGroup` z remisującymi stylami i „Wybieram ten styl”; bez stylu nie ma dostępu do kursów (`SurveyGate`) |
| `/courses` (katalog) | sekcja „Moje kursy” (przyjęty: pasek postępu „2 z 4 lekcji”, „Kontynuuj”) i „Katalog” (tytuł, opis, nauczyciel, liczba lekcji, stan prośby: „Zapisz się” / „Prośba wysłana – czeka na nauczyciela” / „Prośba odrzucona” + „Poproś ponownie”) |
| `/courses/[id]` | wstęp, „Streszczenie kursu” — ponumerowana lista lekcji z zarysami i stanem (✓ zaliczona z wynikiem, „Dostępna”, kłódka + „Najpierw zalicz lekcję n”), podpowiedź z kursu (R8) dla ucznia bez wyników, „Podsumowanie i wnioski”; bez zapisu — przycisk zapisu / stan prośby zamiast stanów lekcji |
| lekcja (tryb skupienia) | nagłówek; „Zarys”; pasek formy: „Przerabiasz tę lekcję w formie: Słuchowej (A)” + „Przerób tę lekcję w innej formie” (menu z dwiema formami); wersja (bloki: tekst, obraz, nagranie, PDF…); „Wnioski”; „Sprawdź się” — 5 pytań (`RadioGroup`), „Sprawdź”; zablokowana → komunikat z kłódką i linkiem do wymaganej lekcji |
| wynik quizu | wynik słownie i liczbowo; przy każdym pytaniu wybrana i poprawna odpowiedź + wyjaśnienie; „Co to zmieniło”: „Słuchowe 47% → 57% · Lekcja 4 odblokowana” (albo „To kolejne podejście w tej formie – procenty bez zmian”); pochwała z danymi; **niezaliczony**: ramka sugestii z uzasadnieniem i przyciskiem „Przerób tę lekcję w formie X”; „Rozwiąż jeszcze raz” (nowe losowanie); propozycja zmiany stylu i wynik okresu próbnego — baner z „Przełącz na stałe” / „Zostaję przy swoim” |
| `/profile` („Mój styl”) | aktywny styl i skąd się wziął; procenty V / A / K z opisem przy każdej formie: „potwierdzona wynikami (2 lekcje, średnio 88%)” / „tylko z ankiety”; otwarta propozycja z dowodem; okres próbny („1 z 2 lekcji w nowej formie”) albo jego wynik; ręczna zmiana stylu (`RadioGroup` + `AlertDialog`: „Procenty się nie zmienią, zmiana trafi do dziennika”); wynik ankiety |
| `/progress` („Moje postępy”) | wykres procentów w czasie; postęp kursów (pasek, „następna: Lekcja 3”); tabela wyników lekcji (kurs, lekcja, forma, wynik, podejścia; pierwsze policzone oznaczone); dziennik decyzji (lista: data, zdanie z `explain.ts`, kurs / lekcja) |

### Nauczyciel (menu: „Moje kursy”)
| Ekran | Zawartość |
|---|---|
| `/pending` | konto `pending`: „Konto czeka na zatwierdzenie przez administratora” + „Wyloguj”; `rejected`: „Konto nauczyciela nie zostało zatwierdzone”; `RoleGate`/guard kieruje tu każdy ekran nauczyciela |
| `/teach` | karty kursów (tytuł, opublikowany / prywatny tekstem, „3 z 4 lekcji opublikowanych”, „2 prośby o zapis”) |
| `/teach/courses/[id]` | ustawienia (tytuł, opis, wstęp, **podsumowanie i wnioski**), publikacja kursu (blokada z wyjaśnieniem bez opublikowanej lekcji), lista lekcji z kolejnością i stanem („Opublikowana” / „Szkic – brakuje: wersja K, 2 pytania”), link „Panel kursu” |
| `/teach/courses/[id]/lessons/[lessonId]` | tytuł; **zakładki** „Zarys i wnioski”, „Wzrokowa (V)”, „Słuchowa (A)”, „Kinestetyczna (K)”, „Quiz (pula)”; w zakładce wersji edytor bloków (jak dotąd, bez form w oknie załącznika) i podpowiedź, co wersja musi zawierać; zakładka quizu: pytania z odpowiedziami, poprawną i **wyjaśnieniem**, licznik „8 pytań w puli (min. 5)”; panel **gotowości** z listą braków i „Opublikuj lekcję” / „Wycofaj publikację”; ostrzeżenie o niezapisanych zmianach |
| `/teach/courses/[id]/panel` („Panel kursu”) | sekcje: **Prośby o zapis** (imię, e-mail, data, „Przyjmij” / „Odrzuć”); **Uczniowie** (tabela: imię, styl, procenty V/A/K, postęp, średnia, ostatnia aktywność, otwarta propozycja; wiersz → szczegóły); **Skuteczność form** (tabela V / A / K: średnia, wyniki, podejścia, uczniowie + poziome paski w kolorach form); **Rozkład stylów** (liczby i paski) |
| `/teach/courses/[id]/students/[studentId]` | to samo, co uczeń widzi w „Moich postępach” (wykres, wyniki lekcji tego kursu, procenty z potwierdzeniem) + jego dziennik |
| podgląd lekcji | `LessonPreview`: zarys, przełącznik wersji V / A / K, wnioski, pula pytań (z poprawnymi i wyjaśnieniami, bez rozwiązywania) |

### Administrator (menu: „Użytkownicy”, „Kursy”)
- `/admin/users`: zakładki Nauczyciele / Uczniowie; u nauczycieli kolumna „Konto” (Zatwierdzone / Czeka na zatwierdzenie / Odrzucone — tekst, nie kolorowa plakietka), filtr „Czekające (n)”, akcje „Zatwierdź” / „Odrzuć” (odrzucenie z `AlertDialog`); reszta bez zmian.
- `/courses`: wszystkie kursy (odczyt), podgląd lekcji jak u nauczyciela.

### Klucze TanStack Query
`["auth","me"]`; `["courses"]`, `["courses", id]`, `["courses", id, "enrollments"]`, `["courses", id, "hint"]`, `["courses", id, "stats"]`, `["courses", id, "students", studentId]`; `["lessons", id]`, `["lessons", id, "study"]`, `["lessons", id, "quiz"]`, `["lessons", id, "versions"]`, `["lessons", id, "quiz-edit"]`, `["lessons", id, "readiness"]`; `["learning-style","profile"]`, `["me","progress"]`, `["me","journal"]`. Wysłanie quizu unieważnia profil, `study`, kurs (stany lekcji), postępy i dziennik.

## Dane demo (`backend/app/demo`)

Hasło wszystkich kont: `Demo123!`. Seed idempotentny (drugie uruchomienie nic nie zmienia, wypisuje „bez zmian”); `--reset-students` przywraca stan startowy **wszystkich** kont demo (uczniowie: usuwa ankiety, profile, wyniki, zestawy pytań, zapisy, dziennik, propozycje, okresy próbne i odtwarza historię; nauczyciel `pending` wraca do `pending`). Historie uczniów powstają **przez prawdziwe serwisy** (ankieta, losowanie, wysłanie odpowiedzi poprawnych/błędnych do zadanego wyniku, decyzje), więc dziennik i procenty są prawdziwe; seed tylko cofa daty zdarzeń o dni (wykres w czasie). Nowa baza: `alembic upgrade head` + `python -m app.demo.seed`.

### Kursy (nauczyciel Anna Nowak, wszystkie opublikowane)
| Kurs | Lekcje |
|---|---|
| Matematyka: funkcja liniowa | 1. Wzór i wykres · 2. Współczynnik kierunkowy a · 3. Miejsce zerowe · 4. Funkcja liniowa w zadaniach |
| Angielski: Present Perfect | 1. Budowa zdania · 2. ever, never, already, yet · 3. for i since · 4. Present Perfect czy Past Simple? |
| Programowanie: pętle w Pythonie | 1. Pętla for · 2. range() · 3. Pętla while · 4. break i continue |

Każda lekcja: zarys (2–3 zdania), wnioski (3–4 punkty), **V** — tekst + 1–2 schematy/wykresy PNG, **A** — nagranie MP3 głosem neuronowym pl-PL (edge-tts, objaśnienie lektorskie albo dialog dwóch głosów; wymaga internetu przy generowaniu) + krótki opis, **K** — instrukcja krok po kroku + karta PDF do wykonania, **pula 8 pytań** z wyjaśnieniami. Każdy kurs: wstęp, podsumowanie i wnioski. Zasoby w `app/demo/assets/` (generatory jak dotąd, osobny venv narzędziowy).

### Konta i stany
| Konto | Rola | Stan startowy | Na pokazie |
|---|---|---|---|
| `admin.demo@imsu.pl` (Adam Admin) | admin | — | zatwierdza nauczyciela `pending` |
| `nauczyciel.demo@imsu.pl` (Anna Nowak) | nauczyciel, zatwierdzony | właściciel 3 kursów | przyjmuje prośbę o zapis, panel kursu |
| `nauczyciel.nowy@imsu.pl` (Piotr Zieliński) | nauczyciel `pending` | — | ekran „Konto czeka na zatwierdzenie” |
| `uczen.nowy@imsu.pl` (Ola Kowalska) | uczeń | bez ankiety | wymuszenie ankiety, wynik, katalog, prośba o zapis |
| `uczen.zapis@imsu.pl` (Zosia Mazur) | uczeń | ankieta V 6 / A 10 / K 4 → A 50 / V 30 / K 20, styl A; **prośba o zapis** do Matematyki | nauczyciel przyjmuje na żywo → uczennica widzi podpowiedź z kursu |
| `uczen.demo@imsu.pl` (Kuba Wiśniewski) | uczeń | ankieta V 9 / A 8 / K 3 → 45 / 40 / 15, styl V; Matematyka: L1 w V 80% (V 55 / A 33 / K 12), L2 w V 40% (sugestia A z ankiety — zignorowana) → 45 / 40 / 15, L2 w V ponownie 80% (niepoliczone, zaliczone) — **„tuż przed sugestią”** | L3 w V oblewa (40%) → V 35 / A 47 / K 18 + „Przerób w formie A” (A druga w ankiecie, 40%) → L3 w A 80% → V 28 / A 57 / K 15 → **propozycja zmiany na A** („Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%”) → przyjmuje → okres próbny (przed: 40%) |
| `uczen.zmiana@imsu.pl` (Marta Lewandowska) | uczeń | ankieta K 10 / V 7 / A 3 → K 50 / V 35 / A 15, styl K; Programowanie: L1 w K 40% → sugestia V → L1 w V 80% → propozycja V przyjęta → L2 w V 100%, L3 w V 80% → **„Zmiana pomogła: średnia 40% → 90%”**, pochwała „3 lekcje z rzędu w formie wzrokowej, średnio 87%” | pokaz dziennika i wykresu |
| `uczen1…6@imsu.pl` (6 uczniów z imionami) | uczniowie | różne style (2 × V, 2 × A, 2 × K), przyjęci do Matematyki (część także do pozostałych), wyniki tak dobrane, że w Matematyce A ≈ 85%, K ≈ 70%, V ≈ 60%; jeden z otwartą propozycją | panel kursu ma sensowne statystyki; podpowiedź „forma słuchowa (średnio 85%, 3 uczniów)” |

Dokładne liczby kont 1–6 ustala agent danych; test seeda sprawdza stany z tabeli (procenty, propozycje, okres próbny, prośba `pending`, nauczyciel `pending`).

### Scenariusz
Nowy `docs/SCENARIUSZ-POKAZU.md` (12–15 min): przygotowanie (reset), przebieg na kontach w kolejności: strona startowa → `uczen.nowy` (ankieta, procenty, katalog, prośba) → `nauczyciel.nowy` (oczekuje) → `admin` (zatwierdza) → `nauczyciel.demo` (edytor lekcji: 3 wersje i pula, gotowość; prośba Zosi → przyjmuje; panel kursu) → `uczen.zapis` (podpowiedź z kursu) → `uczen.demo` (sugestia → zmiana formy → propozycja → przyjęcie) → `uczen.zmiana` (okres próbny, dziennik, wykres) → nauczyciel: szczegóły ucznia. Przy każdym kroku: która reguła (R1–R11) i co powiedzieć; na końcu odpowiedzi na pytania: skąd system wie, dlaczego jeden styl naraz, dlaczego +10 tylko za pierwsze podejście, *meshing* i krytyka VAK (Pashler i in., 2008) — system traktuje ankietę jako hipotezę startową, sprawdza ją wynikami i zostawia decyzję uczniowi.

## Testy (scenariusze)

Backend (pytest, baza z migracji):
- **`rules.py` (jednostkowe, każda reguła z liczbami ze specyfikacji):** R1 (przykłady, min. 5%, suma 100, remisy punktów, reszty przy remisie); R2 (przykłady, limit 90, minimum 5, brak zmiany na minimum, proporcja przy różnych wartościach — właściwość: suma = 100 i każda ≥ 5 dla wszystkich profili z siatki); `is_counted` (pierwsze w formie, powtórka, inna forma tej samej lekcji); R3 (potwierdzona przez niepoliczone zaliczenie, brak danych → `null`); R4 (seria, przerwanie serią innej formy, niezaliczonym, niepoliczonym); R5 (potwierdzony kandydat, dwa potwierdzone — procent, remis procentu — średnia, brak potwierdzonych — ankieta, remis ankiety, oblanie w formie innej niż styl, poprzedni wynik `null`); R6 (warunek, niepotwierdzona wyższa forma → brak, okres próbny → brak, odrzucona → brak do 2 nowych wyników, potem wraca, wygaszenie); R7 (`helped`, `neutral`, `worse` + powrót, `no_baseline`, wyniki w innej formie się nie liczą); R8 (min. 2 uczniów, remisy, uczeń z wynikami → brak); R9 (preferencja nowych, pula = 5, pula < 5 przy podglądzie, determinizm z `rng`); R10 (pierwsza, po zaliczeniu, zmiana kolejności, zaliczona zostaje dostępna); R11 (każdy kod braku).
- **API i uprawnienia:** zatwierdzanie nauczycieli (rejestracja → `pending`, `TEACHER_NOT_APPROVED` na endpointach nauczyciela, approve / reject, tylko admin); zapisy (prośba, powtórka, odrzucenie i ponowna prośba, akceptacja tylko przez autora, `ENROLLMENT_REQUIRED` dla treści / quizu / `study`); blokada (`LESSON_LOCKED` z danymi, odblokowanie po zaliczeniu dowolnego podejścia, nieopublikowane lekcje pominięte); wersje (zapis, walidacja, brak `forms`, `PUBLISHED_LESSON_INCOMPLETE`); gotowość i publikacja (`LESSON_NOT_READY` z brakami, `LAST_PUBLISHED_LESSON`, kurs bez opublikowanej lekcji); quiz (5 z puli, brak klucza w `GET`, ten sam otwarty zestaw po odświeżeniu, inne pytania przy powtórce, `DRAW_NOT_OPEN`, odpowiedzi spoza zestawu, wyjaśnienia w wyniku); `record_quiz_result` (forma z wyboru lekcji, tylko pierwsze podejście w formie zmienia procenty, historia procentów, zdarzenia dziennika z danymi, sugestia przy porażce, propozycja przy potwierdzonej wyższej formie, przyjęcie / odrzucenie / powrót po 2 wynikach, okres próbny do końca, ręczna zmiana = okres próbny + `superseded`); remis w ankiecie i wybór; ankieta raz; statystyki kursu i szczegóły ucznia (tylko autor, tylko przyjęty uczeń); dziennik ucznia; usunięte endpointy → 404.
- **Migracja:** `downgrade base` + `upgrade head` na pustej bazie i na bazie z danymi v2 (test w `tests/test_migrations.py` albo ręcznie z zapisem w raporcie).
- **Seed:** stany kont z tabeli, idempotencja (drugie uruchomienie bez zmian w liczbach wierszy), `--reset-students` przywraca stan po symulowanym pokazie.

Frontend: `npm run lint`, `npm run format:check`, `npm run build`. Przejście **Playwright** (skrypt w `frontend/e2e/demo-tour.mjs`, uruchamiany ręcznie) przez scenariusz pokazu na wszystkich kontach demo, zrzut każdego ekranu do `docs/zrzuty-v3/` (szerokość komputera; wybrane także telefon 390 px). Na końcu: `--reset-students`.

## Kroki implementacji (pliki, commity)

### Etap A (teraz)
1. Ta specyfikacja — `docs: add v3 adaptation specification` → **STOP do akceptacji**.

### Etap B0 — fundament (integrator, przed agentami)
Wspólne pliki, które inaczej zderzyłyby się między agentami:
- `core/errors.py` (parametry błędu), modele wszystkich modułów i migracja `v3_adaptation`, usunięcie klas i zwijania z backendu (kod i testy), szkielet modułu `authoring`, rejestracja routerów w `main.py`, wspólne fixture'y w `tests/conftest.py` (`make_course` z lekcjami, zapis ucznia, ankieta);
- interfejsy serwisów używane przez innych agentów (sygnatury z tej specyfikacji, implementacja minimalna, testy dopisuje agent 1): `curriculum.service.get_study_lesson`, `mark_lesson_passed`, `accepted_student_ids`, `course_progress`, `content.service.get_version`;
- testowe bazy agentów (`imsu_test_a1`, `imsu_test_a2`, `imsu_test_a5`) w kontenerze.
- Commity: `feat(core): add error parameters`, `refactor(backend): remove classrooms and material collapsing`, `feat(backend): add v3 data model and migration`.

### Etap B — agenci równolegle (osobne worktree i gałęzie `feat/v3-a<n>` z B0; integrator scala do `feat/v3-adaptacja`)
| Agent | Obszar plików (wyłącznie) | Zakres | Weryfikacja agenta |
|---|---|---|---|
| **1. backend: dostęp i treść** | `modules/identity/**`, `modules/curriculum/**`, `modules/content/**`, `modules/authoring/**`, `tests/{identity,curriculum,content,authoring}/**` | zatwierdzanie nauczycieli, kursy (`summary`), lekcje (`outline`, `conclusions`, publikacja), zapisy, blokada (R10), wersje V/A/K, gotowość (R11), publikacja | `pytest` swoich testów + całość, `ruff check`, `ruff format --check` |
| **2. backend: silnik** | `modules/learning_style/**`, `modules/assessment/**`, `tests/{learning_style,assessment}/**` | `rules.py` (R1–R8), `stats.py`, `drawing.py` (R9), pula pytań, zestawy, `record_quiz_result`, propozycje, okres próbny, dziennik, `study`, statystyki, `/me/*`, `/courses/{id}/stats`, szczegóły ucznia | jak wyżej; `rules.py` w 100% przetestowane |
| **3. frontend: uczeń** | `features/{courses,learning-style,assessment,content,progress}/**`, trasy `app/(app)/{courses,survey,profile,progress}/**`, `app/(focus)/**` | katalog i zapisy, strona kursu z blokadą, lekcja z wersjami i zmianą formy, quiz z informacją zwrotną, „Mój styl”, „Moje postępy”, `explain.ts`, wykres, dziennik, podgląd lekcji nauczyciela; eksport `PercentChart`, `DecisionJournal`, `LessonResultsTable`, `FormPercentages` dla agenta 4 | `lint`, `format:check`, `build` |
| **4. frontend: nauczyciel i admin** | `features/{teach,users,auth,dashboard}/**`, usunięcie `features/classes`, trasy `app/(app)/{teach,admin,dashboard,pending}/**`, `app/(auth)/**`, nawigacja w `AuthenticatedShell` | ekran oczekiwania, zatwierdzanie, edytor kursu i lekcji (zakładki, pula, gotowość, publikacja), panel kursu, szczegóły ucznia (komponenty agenta 3), dashboard | jak wyżej |
| **5. dane demo** | `app/demo/**`, `tests/demo/**`, `docs/SCENARIUSZ-POKAZU.md` | faza 1 (równolegle): treść 12 lekcji, PNG, MP3, PDF, pule pytań, wstępy i podsumowania; faza 2 (po scaleniu agentów 1–2): seed, konta, historie, `--reset-students`, test seeda, scenariusz | generatory działają, seed 2 ×, test seeda |

Zasady dla agentów: tylko swój obszar plików; zmiana poza nim (np. `shared/`, `core/`, `conftest.py`) — przez integratora; kontrakt API i reguły z tej specyfikacji są nienegocjowalne (rozbieżność → pytanie do integratora); commit po każdym podetapie (Conventional Commits, po angielsku); bez pushu; własna baza testowa; bez uruchamiania serwerów na portach 8001 / 3001. Frontend pracuje na kontrakcie (typy z tej specyfikacji), test na żywo robi integrator.

### Etap C — integracja i weryfikacja (integrator)
1. Scalenie gałęzi agentów (kolejność: 1, 2, 5, 3, 4), rozwiązanie konfliktów, zgodność z kontraktem (typy frontendu ↔ schematy).
2. Pełna weryfikacja: `pytest`, `ruff check .`, `ruff format --check .`, `npm run lint`, `npm run format:check`, `npm run build`, `alembic downgrade base` + `upgrade head`, seed 2 ×, Playwright na wszystkich kontach ze zrzutami.
3. Dokumentacja: `moduly/` (nowy `07-authoring.md`, przepisane pozostałe), `02-koncepcja.md`, `03-architektura.md`, `04-decyzje.md` (nowe decyzje, stare oznaczone jako zastąpione), `05-plan-etapow.md`, `00-START.md`, `README.md`, `docs/tex/` (architektura, reguły adaptacji, UML), wyczyszczenie tego pliku.
4. `docs/RAPORT-v3.md`: co zrobione, jak sprawdzone (liczby testów, zrzuty), co nie działa, decyzje podjęte samodzielnie, ściąga „jak działa system” na 1 stronę.
5. Aplikacja uruchomiona lokalnie (http://localhost:3001), komenda resetu kont demo.

## Poza zakresem
Ponowna ankieta (procenty startują z ankiety raz), test końcowy kursu, wirtualny mentor, LLM, pytania inne niż jednokrotnego wyboru, powiadomienia (e-mail) o prośbach i zatwierdzeniu, moderacja kursów przez administratora, anulowanie własnej prośby o zapis, przenoszenie danych v2 (profile, próby quizów).

## Pytania do autora
Rozwiązania domyślne — obowiązują, jeśli w akceptacji nie napiszesz inaczej:
1. **Ankieta raz** (bez ponownej): procenty startują z ankiety, potem zmieniają je tylko wyniki. Inaczej nowa ankieta kasowałaby dane z quizów.
2. **Ręczna zmiana stylu też uruchamia okres próbny** (2 lekcje) i zamyka otwartą propozycję. Po przyjęciu propozycji powrotu okresu próbnego nie ma (bez pętli).
3. **Wersja K wymaga karty PDF** (instrukcja tekstem + PDF); wersja A — nagranie (plik albo tekst dla lektora przeglądarki) + krótki opis; V — tekst + obraz lub film.
4. **Odrzucony uczeń może poprosić ponownie**; przyjęty uczeń zachowuje dostęp także po wycofaniu publikacji kursu.
5. **Okres próbny:** „pomogła” przy średniej wyższej niż przed zmianą, spadek o ≥ 10 pkt → propozycja powrotu, pomiędzy → „bez wyraźnej różnicy”; „przed” = średnia z ostatnich 2 policzonych wyników w poprzednim stylu.
6. **Statystyki form ucznia i propozycje — ze wszystkich kursów** (styl jest jeden dla ucznia); podpowiedź R8 — z danego kursu.
7. Znane ograniczenie do omówienia na pokazie: druga szansa w innej formie jest łatwiejsza (uczeń zna już część pytań i wyjaśnienia), więc +10 dla formy „drugiej szansy” może zawyżać jej procent. Łagodzą to: losowanie innych pytań przy powtórce (R9), liczenie tylko pierwszego podejścia w formie i wymóg potwierdzenia formy przed propozycją. Zostawiamy regułę z zadania i opisujemy to uczciwie w dokumentacji.

---
## Stan realizacji
Kroki zrobione (commity) · Decyzje w trakcie · Weryfikacja · Do zrobienia

- Etap A: specyfikacja — czeka na akceptację.
