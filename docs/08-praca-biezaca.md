# Praca bieżąca

Specyfikacja tego, co teraz robimy. Po zakończeniu: wynik trafia do `moduly/<nr>-<moduł>.md`, decyzje do `04-decyzje.md`, status do `05-plan-etapow.md` i `00-START.md`, a ten plik czyścimy (historia w gicie).

---

## Etap 10 — statystyki „premium”, stopniowanie podpowiedzi, seria porażek, język komunikatów (15.11)

Zlecenie: `..\ZADANIE-CLAUDE-CODE-IMSU-v3-statystyki.md` (punkty 1–10; punkt 11 zrobiony 15.11 przed pushem v3). Gałąź `feat/statystyki` od `main`. Jak w etapie 9 (D54): kod pisze i commituje AI za wyraźną zgodą Patryka („wykonaj w całości, bez czekania”), równolegle kilku agentów w osobnych worktree, integracja i weryfikacja przez AI. Bez pushu i merge do `main`.

### Zasada
Każda statystyka odpowiada na konkretne pytanie. Nagłówek sekcji mówi, co pokazuje; pod nim jedno zdanie, jak czytać liczby. Poniżej progu danych backend zwraca `null` zamiast procentu **razem z liczebnością `n`**, a frontend pisze „za mało danych (n = 2)”. Wszystko z istniejących tabel (`quiz_results`, `quiz_draws.answers`, `lesson_completions`, `learning_profiles`), bez nowych tabel i migracji.

### Stałe (backend: `learning_style/stats.py`, `assessment/stats.py`; frontend: powtórzone w `explain.ts`)
| Stała | Wartość | Gdzie |
|---|---|---|
| `FIRST_TRY_MIN_LESSONS` | 2 | tabela form: „Za pierwszym razem” |
| `LESSON_MIN_STUDENTS` | 3 | statystyki lekcji: zaliczalność, średnia, wniosek o najtrudniejszej |
| `MATRIX_MIN_RESULTS` | 2 | macierz lekcja × forma: komórka i wnioski |
| `FORM_GAP` | 20 | wniosek macierzy: różnica najlepsza − najsłabsza forma (pkt) |
| `QUESTION_MIN_DRAWS` | 5 | analiza pytań: % poprawnych, % złej odpowiedzi, ocena |
| `HARD_BELOW` / `EASY_ABOVE` | 40 / 90 | ocena pytania: `hard` (< 40), `easy` (> 90), `normal` |
| `REVIEW_LIMIT` | 5 | „Do powtórki” |
| `ATTENTION_STREAK` (`rules.py`) | 3 | seria porażek (R12) |

„Pierwsze podejście” = **policzony wynik** (`counted`, pierwsze podejście w danej formie w danej lekcji — te, które zmieniają profil, R2). Średnie: `rules.average` (połówka w górę). Liczba podejść do zaliczenia: 1 miejsce po przecinku (`float`).

### Kontrakt API

**1. `GET /me/stats`** (uczeń, `learning_style`) → `StudentStatsResponse`:
- `summary`: `passed_lessons` (zaliczone lekcje we wszystkich kursach), `attempts` (wysłane podejścia = wiersze `quiz_results`), `average` (średnia policzonych, `null` bez nich), `counted` (ich liczba), `streak` (kolejne zaliczone policzone wyniki od najnowszego wstecz do pierwszego niezaliczonego policzonego; niepoliczone pomijane).
- `forms`: `{V|A|K: FormTableRow}` — `FormTableRow`: `lessons` (różne lekcje z podejściem w formie), `attempts` (podejścia w formie), `passed_lessons` (różne lekcje z zaliczonym podejściem w formie), `first_try_lessons` (policzone wyniki w formie = lekcje z pierwszym podejściem w niej), `first_try_passed` (z nich zaliczone), `first_try_rate` (`round` % zaliczonych; `null`, gdy `first_try_lessons < 2`), `average` (średnia policzonych; `null` przy 0), `best` (najwyższy wynik w formie, każde podejście; `null` bez podejść), `confirmed` (R3), `percent` (procent profilu; `null` bez profilu).
- `attention`: `Attention | null` (R12, stan bieżący).

**2. `GET /me/review-questions`** (uczeń, `assessment`) → `ReviewQuestionResponse[]`: dla każdej lekcji bierzemy **ostatni wysłany zestaw** (`quiz_draws` z `submitted_at`); pytania odpowiedziane w nim źle (i nadal obecne w puli) to pytania do powtórki. Tylko lekcje kursów, na które uczeń jest przyjęty. Najnowsze pierwsze (po `submitted_at`, potem kolejność w zestawie), maks. 5. Pola: `course_id`, `course_title`, `lesson_id`, `lesson_title`, `number`, `question_id`, `text`, `chosen_answer` {`id`, `text`}, `correct_answer` {`id`, `text`}, `explanation`, `answered_at`.

**3. `GET /courses/{id}/stats`** (autor) — `CourseStatsResponse` dostaje nowe pola (stare bez zmian):
- `lessons`: `LessonStatsRow[]` — opublikowane lekcje w kolejności kursu: `lesson_id`, `title`, `number`, `started` (uczniów z ≥ 1 podejściem), `passed` (uczniów z zaliczonym podejściem), `pass_rate` (% `passed / started`; `null`, gdy `started < 3`), `first_average` (średnia policzonych wyników w lekcji; `null`, gdy `started < 3`), `first_results` (liczba policzonych wyników), `attempts_to_pass` (średnia liczba podejść do pierwszego zaliczenia włącznie, wśród uczniów, którzy zaliczyli; `null`, gdy `passed = 0`).
- `hardest`: `LessonStatsRow | null` — najniższe `pass_rate` wśród lekcji z `started ≥ 3`; remis → niższa `first_average` → wcześniejsza lekcja; `null`, gdy żadna lekcja nie ma 3 uczniów **albo** wszystkie mają 100%.
- `matrix`: `[{lesson_id, title, number, cells: {V|A|K: {average: int | null, n: int}}}]` — średnia policzonych wyników w formie; `average = null`, gdy `n < 2`.
- `form_gaps`: `[{lesson_id, title, number, best: {form, average, n}, worst: {form, average, n}}]` — lekcje, w których najlepsza i najsłabsza forma (obie `n ≥ 2`) różnią się o ≥ 20 pkt; remis form → V, A, K; kolejność kursu.
- `students[].attention`: `Attention | null` (R12 ucznia, wszystkie jego kursy).

**4. `GET /courses/{id}/question-stats`** (autor, `assessment`) → `[{lesson_id, title, number, questions: QuestionStatsRow[]}]` dla opublikowanych lekcji; z wysłanych zestawów uczniów obecnie przyjętych. `QuestionStatsRow`: `question_id`, `text`, `drawn` (w ilu wysłanych zestawach), `correct` (ile razy dobrze), `correct_percent` (`null`, gdy `drawn < 5`), `top_wrong` (`{answer_id, text, count, percent}` najczęściej wybranej złej odpowiedzi — remis → kolejność odpowiedzi w pytaniu; `percent` = `count / drawn`, `null`, gdy `drawn < 5`; całość `null`, gdy nikt nie odpowiedział źle), `rating` (`hard` / `easy` / `normal`; `null`, gdy `drawn < 5`). Kolejność w lekcji: `correct_percent` rosnąco, `null` na końcu, potem kolejność w puli. Błędy: 404 `COURSE_NOT_FOUND`, 403 `FORBIDDEN` / `TEACHER_NOT_APPROVED`.

**5. `GET /courses/{id}/students/{student_id}`** — `StudentDetailResponse` dostaje `forms` (`{V|A|K: FormTableRow}`, jak w `/me/stats`, ze wszystkich kursów ucznia) i `attention`.

**6. R5 — stopniowanie podpowiedzi (zmiana reguły).** `rules.retry_suggestion` zwraca dodatkowo `strength`: `soft`, gdy **poprzedni policzony wynik w tej formie** (dowolna lekcja, bez bieżącego wyniku) był zaliczony; w każdym innym przypadku (poprzedni policzony w formie niezaliczony = druga porażka z rzędu, albo brak poprzedniego policzonego w formie) — `strong`. Pole `strength` w `RetrySuggestion` (`QuizFeedback.suggestion`, `StudyResponse.suggestion`) i w `data` zdarzenia `retry_suggestion`. Starsze zdarzenia bez pola frontend traktuje jak `strong`. Ekran: `soft` — na pierwszym planie „Rozwiąż jeszcze raz”, pod nim spokojne zdanie z linkiem „Możesz też przerobić tę lekcję w formie X.” (bez ramki); `strong` — ramka jak dotąd (neutralna, nie czerwona), uzasadnienie z liczb, przycisk „Przerób tę lekcję w formie X”.

**7. R12 — seria porażek (nowa reguła).** `rules.attention(results) -> Attention | None`: policzone wyniki ucznia (wszystkie kursy, w kolejności zapisu) liczone od najnowszego wstecz; ≥ 3 kolejne niezaliczone → `Attention(streak, results)`, gdzie `results` = 3 ostatnie policzone wyniki w kolejności chronologicznej (`lesson_id`, `lesson_title`, `form`, `percent`). Znika po pierwszym zaliczonym policzonym wyniku. `QuizFeedback.attention` (stan po tym podejściu). Zdarzenie dziennika `attention_needed` (`data`: `streak`, `results`) zapisywane, gdy policzony niezaliczony wynik daje serię **dokładnie 3** (raz na serię). Komunikat u ucznia: „Trzy ostatnie lekcje poniżej progu (55%, 40%, 50%). Spróbuj innej formy albo poproś nauczyciela o pomoc.”; u nauczyciela przy uczniu słowa „wymaga uwagi” z tymi wynikami (bez plakietki).

### Frontend
- **Uczeń — „Moje postępy”** (nad wykresem i dziennikiem): (1) podsumowanie — jeden wiersz, 4 liczby z podpisem; (2) „W której formie idzie Ci najlepiej” — tabela form `FormTable` (wiersz stylu z dopiskiem „Twój styl”, status słowami) + jedno zdanie wniosku z `explain.ts` (tylko fakty z tabeli); (3) „Do powtórki” (maks. 5, link „Wróć do lekcji”; pusto: „Nie masz pytań do powtórki.”); komunikat R12, gdy `attention`. `FormTable` także w szczegółach ucznia u nauczyciela.
- **Nauczyciel — „Panel kursu”**: (4) „Które lekcje sprawiają trudność” + wniosek o najtrudniejszej; (5) „Które pytania są za trudne albo źle ułożone” — sekcje rozwijane po lekcjach, zdanie o złej odpowiedzi wybieranej przez większość; (6) „W jakiej formie działa każda lekcja” — macierz „88% · 4”, „—” przy `n < 2`, wnioski albo „Formy działają podobnie we wszystkich lekcjach.”; „wymaga uwagi” w tabeli uczniów.
- Wygląd wg `07-design.md`: liczby `tabular-nums` do prawej, cienkie paski w kolorach form tylko tam, gdzie ułatwiają porównanie, bez plakietek, kafelków i wykresów kołowych; telefon 390 px — tabela przewijana w obrębie sekcji.
- Pkt 10: kolumna „Wyniki lekcji” bez ucinania (komputer i telefon); dziennik — okres próbny cofnięty (`style_change_reverted.trial_id`) albo zastąpiony (`trial_started.replaced_trial_id`) oznaczony jako anulowany w swoim wpisie.
- Pkt 9: przegląd wszystkich tekstów (po scaleniu powyższych): rzeczowy nauczyciel, bez opisu mechaniki u ucznia, pełne zdania, bez „warto…”, bez form rodzajowych, podpowiedzi w neutralnej ramce, **formy w UI: wzrokowa / słuchowa / praktyczna**; tabela „przed → po” w raporcie.

### Dane demo
Matematyka: ≥ 10 uczniów z historią (dobudowani nowi uczniowie demo), część z kilkoma podejściami; w każdej lekcji co najmniej jedno pytanie wyraźnie trudne (ta sama zła odpowiedź) i jedno łatwe; jedna lekcja z wyraźną różnicą form (wniosek macierzy). Kuba, Marta, Zosia i stany ze scenariusza bez zmian; liczby kursu, które się przesuną, poprawione w `SCENARIUSZ-POKAZU.md`. Idempotencja i `--reset-students` jak dotąd.

### Podział pracy
| Część | Kto | Pliki |
|---|---|---|
| A. Backend: `stats.py`, `assessment/stats.py`, R5 `strength`, R12, endpointy, testy | agent A | `backend/app/modules/learning_style/*`, `backend/app/modules/assessment/*`, `backend/tests/learning_style/*`, `backend/tests/assessment/*` |
| B. Frontend ucznia: pkt 1–3, `FormTable` (też w `StudentDetailPage`), R5 soft/strong, R12, pkt 10 | agent B | `frontend/src/features/progress/*`, `features/learning-style/*`, `features/assessment/*`, `features/teach/components/StudentDetailPage.tsx` |
| C. Frontend nauczyciela: pkt 4–6, „wymaga uwagi” | agent C | `frontend/src/features/teach/*` (bez `StudentDetailPage`), sekcja „Course panel” na końcu `explain.ts` |
| D. Dane demo | agent D | `backend/app/demo/*`, `backend/tests/demo/*` |
| E. Język komunikatów (pkt 9), po scaleniu A–D | agent E | teksty frontendu, treść kursów demo |
| Integracja, Playwright, dokumentacja, raport | integrator | `docs/`, `frontend/e2e/demo-tour.mjs` |

### Stan
- [ ] A · [ ] B · [ ] C · [ ] D · [ ] scalenie · [ ] E · [ ] weryfikacja (pytest, ruff, lint, format, build, seed 2×, reset, Playwright) · [ ] dokumentacja i raport
