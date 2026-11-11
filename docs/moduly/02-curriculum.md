# Moduł `curriculum`

Kursy, lekcje i klasy: autor kursu, publikacja, klasy nauczyciela, widoczność. Decyzje: D10, D11, D26, D27, D34–D37.

## Odpowiedzialność
- Kurs: tytuł, opis, wstęp (dokument TipTap), **autor**, prywatny / opublikowany, archiwizacja.
- Lekcje kursu: tytuł, kolejność, archiwizacja.
- **Klasy** nauczyciela: nazwa, uczniowie (wiele do wielu), przypisane kursy (wiele do wielu, tylko kursy nauczyciela klasy). Logika w `classrooms.py` (korzysta z `service.py`, nie odwrotnie).
- Reguły widoczności i własności dla innych modułów: `get_visible_course`, `get_owned_course`, `get_visible_lesson`, `get_owned_lesson`, `active_lessons` (`service.py`).
- Dane uczniów i nauczycieli (imię, e-mail) pobiera przez `identity.service` (`get_users`, `get_active_student`), bez złączeń z tabelą `users`.

## Model danych

| Tabela | Kolumny |
|---|---|
| `courses` | `id`, `owner_id` → `users` (indeks), `title` (120), `description` (tekst ≤ 500), `introduction` (JSONB, dokument TipTap albo `null`), `is_published` (false), `is_archived` (false), `created_at`, `updated_at` |
| `lessons` | `id`, `course_id` → `courses` (indeks), `title` (120), `position` (nowa lekcja: max + 1), `is_archived`, `created_at`, `updated_at` |
| `classrooms` | `id`, `teacher_id` → `users` (indeks), `name` (80), `created_at`, `updated_at` |
| `classroom_students` | `classroom_id` → `classrooms` (CASCADE), `student_id` → `users` (CASCADE, indeks), `added_at`; PK (`classroom_id`, `student_id`) |
| `classroom_courses` | `classroom_id` → `classrooms` (CASCADE), `course_id` → `courses` (CASCADE, indeks), `assigned_at`; PK (`classroom_id`, `course_id`) |

Migracje `6eb66f0c665b` (kursy, lekcje), `249e835bc4e5` (klasy). „Usuń” kurs / lekcję = archiwizacja (znika z list, historia uczniów zostaje). Klasę się **usuwa** — baza usuwa jej powiązania (`ON DELETE CASCADE`), kursy i konta zostają. W kodzie „klasa” = `classroom` (`class` jest zarezerwowane w Pythonie).

## Widoczność kursu (`can_view_course`)
- Administrator: wszystkie kursy, łącznie z zarchiwizowanymi (tylko odczyt).
- Nauczyciel: **tylko swoje** (także jako podgląd); cudzy kurs → 404.
- Uczeń: kurs niezarchiwizowany i (**opublikowany** albo **przypisany do klasy, do której należy** — zapytanie `EXISTS` na `classroom_courses` × `classroom_students`, tylko dla kursów prywatnych).
- `GET /courses` dla ucznia to **katalog**: tylko kursy opublikowane; kursy klas uczeń widzi na stronie klasy.
- Niewidoczny kurs / lekcja / klasa → 404 (`COURSE_NOT_FOUND`, `LESSON_NOT_FOUND`, `CLASSROOM_NOT_FOUND`), nigdy 403 — nie zdradzamy istnienia.
- Z `get_visible_lesson` korzystają `content`, `learning_style` i `assessment`, więc bloki, lekcja spersonalizowana, quiz i adaptacja działają dla kursów klasy bez zmian w tych modułach.

## Widoczność klasy
- Nauczyciel: swoje klasy (zmiany — tylko on).
- Uczeń: klasy, do których należy — nazwa, nauczyciel (imię i **e-mail do kontaktu**), kursy bez zarchiwizowanych; **bez listy uczniów** (`students` i `student_count` = `null`).
- Administrator: bez klas (403, O6).

## API

Kursy i lekcje:

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /courses` | zalogowany | kursy według widoczności (uczeń: katalog), od najnowszego | 401 |
| `POST /courses` | nauczyciel | `{title, description?}` → 201, kurs prywatny | 403, 422 |
| `GET /courses/{id}` | widzący kurs | kurs, wstęp, lekcje (`id`, `title`) | 404 |
| `PATCH /courses/{id}` | autor | `title?`, `description?`, `introduction?`, `is_published?` | 404 |
| `DELETE /courses/{id}` | autor | archiwizacja, 204 | 404 |
| `POST /courses/{id}/lessons` | autor | `{title}` → 201, lekcja na końcu | 404 |
| `PUT /courses/{id}/lessons/order` | autor | `{lesson_ids}` — każda aktywna lekcja dokładnie raz | 400 `LESSON_ORDER_MISMATCH` |
| `GET /lessons/{id}` | widzący kurs | lekcja z kursem (`id`, `title`, `owner_id`) i `previous_lesson_id` / `next_lesson_id` | 404 |
| `PATCH /lessons/{id}` | autor | `{title}` | 404 |
| `DELETE /lessons/{id}` | autor | archiwizacja, 204 | 404 |

Klasy (`classrooms_router`):

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /classrooms` | nauczyciel, uczeń | nauczyciel: swoje klasy z `student_count` i `course_count` (wszystkie przypisane); uczeń: swoje klasy, `course_count` bez zarchiwizowanych; wg nazwy | 403 `FORBIDDEN` (administrator) |
| `POST /classrooms` | nauczyciel | `{name}` → 201, klasa | 403, 422 |
| `GET /classrooms/{id}` | nauczyciel klasy, uczeń klasy | `id`, `name`, `teacher` (`id`, `display_name`, `email`), `courses` (podsumowania, wg tytułu; nauczyciel także zarchiwizowane), `students` (`id`, `display_name`, `email`, wg imienia; tylko nauczyciel) | 404 `CLASSROOM_NOT_FOUND`, 403 (administrator) |
| `PATCH /classrooms/{id}` | nauczyciel klasy | `{name}` → klasa | 404, 422 |
| `DELETE /classrooms/{id}` | nauczyciel klasy | usunięcie z powiązaniami, 204 | 404 |
| `PUT /classrooms/{id}/students/{student_id}` | nauczyciel klasy | dodanie **aktywnego** ucznia, 204 (ponowne — bez zmian) | 404 `CLASSROOM_NOT_FOUND`, 404 `STUDENT_NOT_FOUND` |
| `DELETE /classrooms/{id}/students/{student_id}` | nauczyciel klasy | usunięcie z klasy, 204 (nie-członek — bez zmian) | 404 |
| `PUT /classrooms/{id}/courses/{course_id}` | nauczyciel klasy | przypisanie swojego niezarchiwizowanego kursu, 204 (ponowne — bez zmian) | 404 `COURSE_NOT_FOUND` |
| `DELETE /classrooms/{id}/courses/{course_id}` | nauczyciel klasy | odpięcie (także zarchiwizowanego), 204 (nieprzypisany — bez zmian) | 404 |

Ponowne dodanie / przypisanie: `INSERT … ON CONFLICT DO NOTHING`. Uczeń zablokowany po dodaniu zostaje w klasie. `curriculum` nie zależy od `content` — bloki lekcji są pod `/lessons/{id}/blocks` w module `content`.

## Frontend
- `features/teach`: `/teach` („Moje kursy”: karty z plakietką Prywatny / Opublikowany, „+ Nowy kurs”), `/teach/courses/[courseId]` (edytor kursu: tytuł, opis, wstęp TipTap, przełącznik publikacji z potwierdzeniem wycofania, lista lekcji — dodaj, zmień nazwę, w górę / w dół, usuń, „Podgląd kursu”, archiwizacja kursu).
- `features/teach` — klasy nauczyciela: `/teach/classes` (`TeacherClassroomsPage`: karty „N uczniów · M kursów”, „Nowa klasa” w `ClassroomNameDialog`, po utworzeniu przejście do klasy), `/teach/classes/[classroomId]` (`ClassroomEditor`: „Zmień nazwę”; `ClassroomStudents` — lista, „Usuń z klasy” bez potwierdzenia, „Dodaj ucznia” w `AddStudentDialog`; `ClassroomCourses` — lista z plakietką Prywatny / Opublikowany / Usunięty, „Odepnij” bez potwierdzenia, „Przypisz kurs” w `AssignCourseDialog` (swoje nieprzypisane kursy); `DeleteClassroomSection` — usunięcie z potwierdzeniem).
- **Wyszukiwanie ucznia na żywo** (`AddStudentDialog`): zapytanie `GET /students?email=` po 300 ms przerwy w pisaniu (`useDebouncedValue`), od 3 znaków; tekst w kluczu zapytania (cache), wyniki poprzedniego tekstu przygaszone do nadejścia nowych (`keepPreviousData`), nieaktualne zapytanie anulowane (`signal` w `api.get`); przy uczniu „Dodaj” albo „W klasie”; okno zostaje otwarte.
- `features/classes`: wspólne `types.ts`, `api.ts`, `hooks.ts` (klucze `["classrooms"]`, `["classrooms", id]`; zmiany uczniów / kursów odświeżają cały prefiks — klasę i liczniki listy; usunięcie klasy najpierw usuwa ją z cache), `errors.ts` (`CLASSROOM_NOT_FOUND`, `STUDENT_NOT_FOUND`); ekrany ucznia: `/classes` („Moje klasy”: karty „Nauczyciel: … · N kursów”, pusty stan), `/classes/[classroomId]` (nazwa, nauczyciel z e-mailem `mailto:`, kursy jako karty katalogu `CourseCard`).
- `features/courses`: `/courses` (uczeń: katalog; admin: wszystkie), `/courses/[courseId]` (ścieżka: uczeń na kursie prywatnym — „Moje klasy”, poza tym „Kursy”; opis, wstęp, ponumerowane lekcje), lekcja w trybie skupienia `(focus)/courses/[courseId]/lessons/[lessonId]`: `LessonScreen` wybiera widok według roli — uczeń `LessonView` (bloki z `learning-style`, zwinięte materiały), nauczyciel i administrator `LessonPreview` (bloki z `useLessonBlocks`, czyli z klucza edytora — podgląd aktualny zaraz po zapisie; wszystkie materiały rozwinięte); oba w `LessonFrame` (`LessonHeader`, stany ładowania / 404 / błędu, pasek podglądu autora „Podgląd: tak uczeń widzi…”, „Wróć do edycji”, lista bloków, quiz, nawigacja „Poprzednia / Następna lekcja”).
- Wspólne: `shared/lib/plural.ts` (odmiana liczebników), `shared/hooks/use-debounced-value.ts`; w `AppShell` aktywna pozycja menu to najdłuższy pasujący adres (`/teach/classes` przed `/teach`).

## Testy
`backend/tests/curriculum/`:
- `test_courses.py`, `test_lessons.py`: uprawnienia (tworzy tylko nauczyciel; cudzy prywatny kurs 404; uczeń tylko opublikowane; admin wszystkie), CRUD, publikacja, archiwizacja, kolejność (zła lista → 400), lekcja z sąsiadami z pominięciem zarchiwizowanych, lekcje zarchiwizowanego kursu niewidoczne.
- `test_classrooms.py`: tworzenie i walidacja nazwy, role (uczeń / admin nie tworzą, admin bez klas), lista własnych klas z licznikami, cudza i nieistniejąca klasa → 404, zmiana nazwy, usunięcie (kursy i konta zostają), dodawanie i usuwanie uczniów (powtórki bez błędu, tylko aktywni uczniowie), przypisywanie kursów (prywatne i opublikowane, powtórka, cudzy / zarchiwizowany → 404, zarchiwizowany po przypisaniu widoczny dla nauczyciela i do odpięcia).
- `test_classroom_access.py`: uczeń klasy otwiera prywatny kurs (kurs, lekcja, bloki, lekcja spersonalizowana, quiz, podejście); traci dostęp po usunięciu z klasy, odpięciu kursu i usunięciu klasy; uczeń spoza klasy i inny nauczyciel — 404; zarchiwizowany kurs znika z klasy ucznia; katalog bez kursów prywatnych; lista i strona klasy ucznia bez uczniów, z e-mailem nauczyciela; uczeń spoza klasy — 404 bez danych; admin — 403; uczeń nie zmienia klasy (403).

## Jak sprawdzić ręcznie
- Nauczyciel: nowy kurs → wstęp ze wzorem `$…$`, tabelą i linkiem → lekcje (dodanie, kolejność, nazwa, usunięcie) → podgląd → publikacja. Uczeń: kurs prywatny niewidoczny, po publikacji na liście. Drugi nauczyciel nie widzi cudzego kursu. Admin widzi wszystkie ze statusem.
- Klasy (`nauczyciel.demo` / `uczen.demo`, moduł `demo`): „Klasy” → „Klasa 7a” (dwoje uczniów, kurs „Programowanie” prywatny) → „Dodaj ucznia” (wpisywanie e-maila, wyniki na bieżąco, „W klasie”) → „Przypisz kurs” / „Odepnij”; uczeń: „Kursy” bez „Programowania”, „Moje klasy” → „Klasa 7a” → kurs → lekcja i quiz; po usunięciu ucznia z klasy — kurs 404, lista klas pusta.

## Ograniczenia
- Brak moderacji kursów i podglądu klas przez administratora (O6); jeden nauczyciel na klasę, bez zaproszeń i kodów dołączenia.
- Wyszukiwanie uczniów po fragmencie e-maila przegląda tabelę `users` (`ILIKE '%…%'`); przy dużej liczbie kont — indeks trigramowy `pg_trgm`.
