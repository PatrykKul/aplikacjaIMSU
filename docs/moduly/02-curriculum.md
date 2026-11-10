# Moduł `curriculum`

Kursy i lekcje, autor kursu, publikacja, widoczność. Od etapu 6 — klasy (specyfikacja w `08-praca-biezaca.md`, potem tutaj). Decyzje: D10, D11, D26, D27.

## Odpowiedzialność
- Kurs: tytuł, opis, wstęp (dokument TipTap), **autor**, prywatny / opublikowany, archiwizacja.
- Lekcje kursu: tytuł, kolejność, archiwizacja.
- Reguły widoczności i własności dla innych modułów: `get_visible_course`, `get_owned_course`, `get_visible_lesson`, `get_owned_lesson`, `active_lessons` (`service.py`).

## Model danych

| Tabela | Kolumny |
|---|---|
| `courses` | `id`, `owner_id` → `users` (indeks), `title` (120), `description` (tekst ≤ 500), `introduction` (JSONB, dokument TipTap albo `null`), `is_published` (false), `is_archived` (false), `created_at`, `updated_at` |
| `lessons` | `id`, `course_id` → `courses` (indeks), `title` (120), `position` (nowa lekcja: max + 1), `is_archived`, `created_at`, `updated_at` |

Migracja `6eb66f0c665b`. „Usuń” = archiwizacja (znika z list, historia uczniów zostaje).

## Widoczność (stan przed etapem 6)
- Uczeń: kursy **opublikowane** i niezarchiwizowane.
- Nauczyciel: **tylko swoje** (także jako podgląd); cudzy kurs → 404.
- Administrator: wszystkie, łącznie z zarchiwizowanymi (tylko odczyt).
- Niewidoczny kurs / lekcja → 404 (`COURSE_NOT_FOUND`, `LESSON_NOT_FOUND`), nigdy 403 — nie zdradzamy istnienia.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /courses` | zalogowany | kursy według widoczności, od najnowszego | 401 |
| `POST /courses` | nauczyciel | `{title, description?}` → 201, kurs prywatny | 403, 422 |
| `GET /courses/{id}` | widzący kurs | kurs, wstęp, lekcje (`id`, `title`) | 404 |
| `PATCH /courses/{id}` | autor | `title?`, `description?`, `introduction?`, `is_published?` | 404 |
| `DELETE /courses/{id}` | autor | archiwizacja, 204 | 404 |
| `POST /courses/{id}/lessons` | autor | `{title}` → 201, lekcja na końcu | 404 |
| `PUT /courses/{id}/lessons/order` | autor | `{lesson_ids}` — każda aktywna lekcja dokładnie raz | 400 `LESSON_ORDER_MISMATCH` |
| `GET /lessons/{id}` | widzący kurs | lekcja z kursem (`id`, `title`, `owner_id`) i `previous_lesson_id` / `next_lesson_id` | 404 |
| `PATCH /lessons/{id}` | autor | `{title}` | 404 |
| `DELETE /lessons/{id}` | autor | archiwizacja, 204 | 404 |

`curriculum` nie zależy od `content` — bloki lekcji są pod `/lessons/{id}/blocks` w module `content`.

## Frontend
- `features/teach`: `/teach` („Moje kursy”: karty z plakietką Prywatny / Opublikowany, „+ Nowy kurs”), `/teach/courses/[courseId]` (edytor kursu: tytuł, opis, wstęp TipTap, przełącznik publikacji z potwierdzeniem wycofania, lista lekcji — dodaj, zmień nazwę, w górę / w dół, usuń, „Podgląd kursu”, archiwizacja kursu).
- `features/courses`: `/courses` (uczeń, admin), `/courses/[courseId]` (opis, wstęp, ponumerowane lekcje), lekcja w trybie skupienia `(focus)/courses/[courseId]/lessons/[lessonId]`: `LessonScreen` wybiera widok według roli — uczeń `LessonView` (bloki z `learning-style`, zwinięte materiały), nauczyciel i administrator `LessonPreview` (bloki z `useLessonBlocks`, czyli z klucza edytora — podgląd aktualny zaraz po zapisie; wszystkie materiały rozwinięte); oba w `LessonFrame` (`LessonHeader`, stany ładowania / 404 / błędu, pasek podglądu autora „Podgląd: tak uczeń widzi…”, „Wróć do edycji”, lista bloków, quiz, nawigacja „Poprzednia / Następna lekcja”).

## Testy
`backend/tests/curriculum/`: uprawnienia (tworzy tylko nauczyciel; cudzy prywatny kurs 404; uczeń tylko opublikowane; admin wszystkie), CRUD, publikacja, archiwizacja, kolejność (zła lista → 400), lekcja z sąsiadami z pominięciem zarchiwizowanych, lekcje zarchiwizowanego kursu niewidoczne.

## Jak sprawdzić ręcznie
Nauczyciel: nowy kurs → wstęp ze wzorem `$…$`, tabelą i linkiem → lekcje (dodanie, kolejność, nazwa, usunięcie) → podgląd → publikacja. Uczeń: kurs prywatny niewidoczny, po publikacji na liście. Drugi nauczyciel nie widzi cudzego kursu. Admin widzi wszystkie ze statusem.

## Ograniczenia
Dostęp tylko „opublikowany = wszyscy uczniowie” do czasu klas (etap 6); brak moderacji kursów przez administratora (O6).
