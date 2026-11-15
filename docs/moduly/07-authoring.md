# Moduł `authoring`

Publikacja lekcji: gotowość (R11) zebrana z trzech modułów i zmiana stanu publikacji. Najwyżej w zależnościach (`core` ← `identity` ← `curriculum` ← `content` ← `learning_style` ← `assessment` ← `authoring`). Decyzje: D49, D29 (uzupełnienie), D53 (seed publikuje lekcje tą drogą).

## Odpowiedzialność
- Odpowiedź na pytanie „czy tę lekcję można opublikować i czego brakuje” — w stałej kolejności: zarys i wnioski, wersje V, A, K, pula pytań.
- Publikacja lekcji tylko kompletnej; wycofanie publikacji (z ochroną ostatniej opublikowanej lekcji opublikowanego kursu).
- Moduł nie ma tabel ani własnych reguł: braki liczą czyste funkcje modułów, które znają dane (`curriculum/readiness.py`, `content/readiness.py`, `assessment/readiness.py`), stan publikacji zmienia `curriculum.service.set_lesson_published`.
- Interfejs (`service.py`): `lesson_readiness(db, lesson) -> list[Issue]` (używa go seed i test seeda), `get_readiness`, `set_publication`.

## Logika

### R11. Gotowość lekcji — `lesson_readiness`
Lista braków `Issue = {area, code, count?, min?}`, pusta = lekcja gotowa:

| `area` | Kody | Skąd |
|---|---|---|
| `lesson` | `OUTLINE_MISSING`, `CONCLUSIONS_MISSING` (pusty dokument TipTap = brak) | `curriculum.service.lesson_issues` |
| `V` | `VERSION_EMPTY` albo `V_VISUAL_MISSING` (tekst + obraz lub wideo) | `content.service.version_issues` |
| `A` | `VERSION_EMPTY` albo `A_AUDIO_MISSING` (nagranie: plik lub tekst lektora), `A_DESCRIPTION_MISSING` (blok tekstu) | jw. |
| `K` | `VERSION_EMPTY` albo `K_INSTRUCTION_MISSING` (blok tekstu), `K_WORKSHEET_MISSING` (PDF) | jw. |
| `quiz` | `QUIZ_TOO_FEW_QUESTIONS` z `count` i `min = 5` | `assessment.readiness.quiz_issues(question_count)` |

Przykład — nowa lekcja „Lekcja 5” bez treści: `OUTLINE_MISSING`, `CONCLUSIONS_MISSING`, `VERSION_EMPTY` × 3 (V, A, K), `QUIZ_TOO_FEW_QUESTIONS` (`count` 0, `min` 5). Po dodaniu zarysu, wniosków, kompletnych wersji i 3 pytań zostaje `{area: "quiz", code: "QUIZ_TOO_FEW_QUESTIONS", count: 3, min: 5}` → „W puli są 3 pytania, potrzeba co najmniej 5 (brakuje 2).”

### Publikacja — `set_publication(db, lesson_id, user, is_published)`
- Autor (zatwierdzony) przez `curriculum.get_owned_lesson` (inaczej 404 / `403 TEACHER_NOT_APPROVED`).
- Publikacja lekcji nieopublikowanej: niepusta lista braków → `409 LESSON_NOT_READY` z `issues`; ponowna publikacja opublikowanej — bez zmian.
- Wycofanie: bez sprawdzania gotowości; ostatnia opublikowana lekcja **opublikowanego** kursu → `409 LAST_PUBLISHED_LESSON` (lekcja szkicu kursu — wycofywana zawsze). Ta sama ochrona przy archiwizacji lekcji (`DELETE /lessons/{id}` w `curriculum`).
- Opublikowana lekcja nie może stać się niekompletna: zapisy zarysu / wniosków (`curriculum`), wersji (`content`) i puli (`assessment`), które wprowadziłyby **nowy** brak, kończą się `409 PUBLISHED_LESSON_INCOMPLETE` z `issues` — najpierw trzeba wycofać publikację.
- Kurs można opublikować dopiero z ≥ 1 opublikowaną lekcją (`409 COURSE_HAS_NO_PUBLISHED_LESSONS`, `curriculum`). Uczeń widzi tylko opublikowane lekcje; wycofana lekcja znika z jego listy (numeracja przesuwa się), a jej zaliczenie zostaje w `lesson_completions`.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/readiness` | autor | `{ready, issues: [{area, code, count?, min?}]}` (`count` / `min` tylko dla puli) | 404 `LESSON_NOT_FOUND`, 403 `TEACHER_NOT_APPROVED`, 401 |
| `PUT /lessons/{id}/publication` | autor | `{is_published}` → `LessonResponse` (`curriculum`) | 409 `LESSON_NOT_READY` + `issues`, 409 `LAST_PUBLISHED_LESSON`, 404, 422 (inne pola) |

## Frontend (`features/teach`)
- Edytor lekcji `/teach/courses/[courseId]/lessons/[lessonId]?tab=` — `LessonEditor`: tytuł, zakładki (`editor-tabs.ts`: „Zarys i wnioski”, „Wzrokowa (V)”, „Słuchowa (A)”, „Praktyczna (K)”, „Quiz (pula)”; zakładka w adresie), `OutlineEditor` (zarys i wnioski, wspólne dla wersji), `VersionEditor` (`moduly/03-content.md`), `PoolEditor` (`moduly/05-assessment.md`), ostrzeżenie o niezapisanych zmianach.
- `ReadinessPanel`: stan („Opublikowana – uczniowie zapisani na kurs ją widzą.” / „Szkic – wszystko gotowe do publikacji.” / „Szkic – do publikacji brakuje:”), `IssueList` (braki pogrupowane po zakładkach, przejście do zakładki, w której brak się poprawia — `tabOfArea`), „Opublikuj lekcję” / „Wycofaj publikację” (z `AlertDialog`); błąd 409 pokazuje listę braków.
- `readiness.ts`: kody R11 → zdania (`issueText`), skrót na liście lekcji (`issuesSummary`: „Szkic – brakuje: wersja K, 2 pytania”), grupowanie po zakładkach; ta sama reguła wersji sprawdzana na żywo na niezapisanych blokach w `VersionEditor`.
- `hooks.ts`: klucz `["lessons", id, "readiness"]`, `useLessonsReadiness(ids)` (stany wszystkich lekcji na stronie kursu), publikacja zapisuje lekcję i unieważnia gotowość, kurs i listę kursów; zapisy zarysu, wersji i puli unieważniają gotowość.

## Testy
`backend/tests/authoring/test_publication.py`: nowa lekcja zgłasza każdy brak, kompletna lekcja jest gotowa, mała pula z `count` i `min`, niekompletnej nie da się opublikować (`LESSON_NOT_READY` z brakami), gotowa lekcja publikuje się i kurs może być opublikowany, opublikowana lekcja zostaje kompletna (zapisy z nowym brakiem → 409), lekcję szkicu kursu można wycofać, ostatnia opublikowana lekcja opublikowanego kursu zostaje (`LAST_PUBLISHED_LESSON`), tylko autor, niezatwierdzony nauczyciel, nieistniejąca lekcja i brak logowania, walidacja treści żądania. Test seeda sprawdza, że każda lekcja demo ma pustą listę braków.

## Jak sprawdzić ręcznie
`nauczyciel.demo@imsu.pl`: Matematyka → „Tytuł nowej lekcji”: „Lekcja 5” → „Dodaj lekcję” → edytor: panel gotowości z 6 brakami → kolejno zarys i wnioski, tekst + obraz w V, nagranie (tekst lektora) + opis w A, instrukcja + PDF w K, 5 pytań z wyjaśnieniami → „Opublikuj lekcję” → uczeń przyjęty widzi lekcję 5 (z kłódką do zaliczenia lekcji 4). Wycofanie publikacji jedynej lekcji kursu opublikowanego → komunikat `LAST_PUBLISHED_LESSON`. Po próbach: zarchiwizować „Lekcję 5” (seed jej nie usuwa).

## Ograniczenia
Gotowość sprawdza obecność elementów (tekst, rodzaj załącznika, liczba pytań), nie jakość ani zgodność treści trzech wersji; brak historii publikacji i harmonogramu (publikacja działa od razu).
