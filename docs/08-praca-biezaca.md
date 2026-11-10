# Praca bieżąca

Specyfikacja tego, co teraz robimy. Po zakończeniu: wynik trafia do `moduly/<nr>-<moduł>.md`, decyzje do `04-decyzje.md`, status do `05-plan-etapow.md` i `00-START.md`, a ten plik czyścimy (historia w gicie).

---

# Etap 5 — poprawki stylu i quizów   (10.11.2026)
Status: **zaakceptowana** (10.11.2026)

Praca bezpośrednio na `main` (D4). Źródło uwag: przegląd etapu 4 (10.11, niżej). Decyzje: D17, D18, D19 (zmienione 10.11).

## Uwagi z przeglądu etapu 4
1. Materiały innych stylów są **ukryte**, więc uczeń traci do nich dostęp, a lekcja może zostać bez załączników → zwijanie (D17).
2. Propozycja „Lepiej Ci idzie z materiałami X” nie wynika z wyników w stylu X (wagi innych stylów stoją na punktach ankiety) → zmiana tekstu i styl efektywny z rozwinięć (D18).
3. Podgląd nauczyciela czyta bloki spod klucza `learning-style`; po zapisie w edytorze podgląd może być nieaktualny przez 60 s → nauczyciel korzysta z `useLessonBlocks`.
4. `prettier --check` nie przechodzi (14 plików), natywne kontrolki zamiast shadcn (radio, checkbox, select, `window.confirm`), `buttonVariants` bez `cn`, `dirty = true` w pustym edytorze quizu, techniczny tekst w opisie quizu, brak linku do quizu w edytorze lekcji, przyklejony pasek postępu ankiety do sprawdzenia.

## Odpowiedzialność
- Drobne poprawki frontendu po przeglądzie.
- Kontrolki formularzy na komponentach shadcn/ui (spójność z etapami 1–3).
- Materiały innych stylów **zwinięte w miejscu** zamiast ukrytych; zapis pierwszego rozwinięcia; **styl efektywny** lekcji w adaptacji i w doborze pytań quizu.

## Kroki

| Krok | Zakres | Commit (propozycja) |
|---|---|---|
| **K1** Drobne poprawki | `npm run format`; `cn(buttonVariants(…))` w `LessonQuiz` i `QuizEditor`; `useState(false)` dla `dirty` w `QuizEditor`; opis quizu „Po sprawdzeniu zobaczysz poprawne odpowiedzi.”; przycisk „Quiz” w pasku `LessonEditor` obok „Podgląd” (na telefonie same ikony); `.gitattributes`: `*.pdf`, `*.mp4`, `*.webm` jako binarne | `style(frontend): format learning-style and assessment` + `fix(frontend): …` |
| **K2** Kontrolki shadcn | `npx shadcn add radio-group select alert-dialog` (jeśli brak); ankieta i quiz — `RadioGroup` w kafelkach 44 px; profil — `Checkbox`; edytor quizu — `Select` formy i `RadioGroup` poprawnej odpowiedzi; usunięcie quizu — `AlertDialog` zamiast `window.confirm`; sprawdzenie przyklejonego paska postępu ankiety pod nagłówkiem `AppShell` | `refactor(frontend): use shadcn controls in survey, profile and quiz` |
| **K3** Backend: zwijanie i rozwinięcia | tabela, endpoint i styl efektywny (niżej); nowy tekst propozycji; testy | `feat(learning-style): collapse other-style materials and record openings` |
| **K4** Frontend: zwijanie | zwinięty załącznik w miejscu, rozwinięcie zapisywane raz, odświeżenie quizu; nowy tekst `PersonalizationNote` | `feat(frontend): show other-style materials collapsed in the lesson` |
| **K5** Dokumentacja | aktualizacja `moduly/04-learning-style.md`, `05-assessment.md`, decyzji i statusu; poprawki `SCENARIUSZ-POKAZU.md` (zwijanie, tekst propozycji, zdania o filtrowaniu „przez serwer”, liczba testów) | `docs: update learning style docs and the presentation script` |

## Model danych (K3)

Nowa migracja, tabela `material_openings` (moduł `learning_style`):

| Kolumna | Typ | Uwagi |
|---|---|---|
| `id` | PK | |
| `user_id` | FK → `users` (CASCADE) | |
| `lesson_id` | FK → `lessons` (CASCADE) | |
| `block_id` | varchar(40) | identyfikator bloku z `lesson_contents` |
| `forms` | varchar(3) | formy załącznika w chwili rozwinięcia, w kolejności V, A, K |
| `created_at` | timestamptz | |

Ograniczenie unikalności (`user_id`, `lesson_id`, `block_id`) — rozwinięcie zapisuje się raz.

## API (K3)

| Endpoint | Kto | Działanie |
|---|---|---|
| `POST /lessons/{id}/blocks/{block_id}/open` | uczeń z ankietą (inne role: 403 `FORBIDDEN`) | zapisuje rozwinięcie, jeśli blok jest załącznikiem lekcji i **żadna** jego forma nie należy do stylu ucznia (zwinięty); w przeciwnym razie nic nie robi. Formy bierze z bloku na serwerze. 204; `SURVEY_REQUIRED` 403; nieznany blok `BLOCK_NOT_FOUND` 404; niewidoczna lekcja 404 |
| `GET /lessons/{id}/personalized-blocks` (zmiana) | zalogowany | uczeń dostaje **wszystkie** bloki oraz `collapsed_block_ids` (załączniki bez formy ze stylu) i `opened_block_ids` (już rozwinięte); `hidden_count` znika; nauczyciel / admin: obie listy puste |

## Logika (K3)

- **Styl efektywny lekcji** = litery stylu ucznia ∪ formy rozwiniętych w tej lekcji załączników (kolejność V, A, K). Funkcja czysta `effective_style(style, opened_forms)` w `personalization.py`; serwis `learning_style.effective_style(db, user, lesson_id)`.
- `record_quiz_result` liczy wagi i zapisuje `quiz_attempts.style` dla **stylu efektywnego** (reguła pierwszego sukcesu / porażki działa na parze lekcja + styl efektywny).
- `assessment`: pytania o formy stylu efektywnego (uczeń, który rozwinął nagranie, dostaje pytanie A).
- Propozycja bez zmian w regułach (D19); tekst: „Wagi wskazują na materiały {słuchowe} – przełączyć?”, uzasadnienie („Wagi stylów po quizach: …”) bez zmian.
- Rozwinięcia z czasu po próbie wpływają tylko na kolejne próby.

## Frontend (K4)

- **Podział widoku lekcji** (uwaga 3 z przeglądu): `features/courses/components/LessonFrame.tsx` — wspólna rama (stany ładowania / 404 / błędu, `LessonHeader`, `<main>`, quiz, nawigacja poprzednia / następna); `LessonView` (uczeń) — `usePersonalizedBlocks`, `PersonalizationNote`, zwinięte materiały; `features/teach/components/LessonPreview.tsx` (nauczyciel, administrator) — `useLessonBlocks` (klucz edytora, więc podgląd zawsze aktualny), `PreviewBanner`, wszystkie bloki rozwinięte. Strona `(focus)/courses/[courseId]/lessons/[lessonId]` wybiera komponent według roli; adresy bez zmian.
- `LessonView` (uczeń): zwinięty załącznik — karta z ikoną typu, tytułem, plakietkami form i przyciskiem „Pokaż materiał” (`outline`, 44 px). Po kliknięciu blok się rozwija (`BlockView`), a przy pierwszym rozwinięciu idzie `POST …/open`; po sukcesie odświeżane są quiz lekcji i spersonalizowane bloki. Bloki z `opened_block_ids` są od razu rozwinięte. Rozwinięty można zwinąć („Zwiń”) — tylko w widoku.
- `PersonalizationNote`: „Lekcja dopasowana do stylu: …”; zamiast „Ukryto N…” — „N materiałów dla innych stylów jest zwiniętych — możesz je rozwinąć.” (odmiana jak dotąd).
- Klucz quizu: styl ucznia zostaje w kluczu, a rozwinięcie unieważnia `["quiz", lessonId]`.

## Testy

- Czyste funkcje: `effective_style` (bez rozwinięć, jedno, kilka, powtórzone litery, kolejność).
- API: rozwinięcie zwiniętego zapisuje się raz; rozwinięcie pasującego / bloku tekstu — bez zapisu; nieznany blok 404; nauczyciel i administrator — 403; `personalized-blocks` zwraca wszystkie bloki i poprawne listy.
- Adaptacja: uczeń V rozwija nagranie A i zalicza quiz → V i A +1; quiz po rozwinięciu zawiera pytanie A; reguła pierwszego sukcesu dla stylu efektywnego.
- Istniejące testy personalizacji i quizu dostosowane do zwijania.
- Frontend: `npm run lint`, `npm run format:check`, `npx tsc --noEmit`, `npm run build`; ręcznie: konto `uczen.demo` — zwinięte materiały, rozwinięcie, quiz z nowym pytaniem, wagi po quizie.

## Poza zakresem
Baza pytań z losowaniem (O5), powtórka w innym stylu, panel nauczyciela ze stylami uczniów (O3).

## Rozstrzygnięcia (10.11)
1. Uczeń może zwinąć z powrotem rozwinięty materiał („Zwiń”) — tylko w widoku, bez zapisu.
2. Endpoint rozwinięcia dla nauczyciela i administratora: 403 `FORBIDDEN`.
