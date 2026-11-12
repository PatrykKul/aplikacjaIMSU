# Moduł `curriculum`

Kursy i lekcje (autor, publikacja kursu, zarys i wnioski lekcji), zapisy na kurs, kolejność lekcji z blokadą, widoczność. Decyzje: D11, D26, D46, D48, D49 (część lekcji), D52 (panel kursu — dane z `learning_style`).

## Odpowiedzialność
- Kurs: tytuł, opis, wstęp i „Podsumowanie i wnioski” (dokumenty TipTap), **autor**, prywatny / opublikowany, archiwizacja.
- Lekcja: tytuł, kolejność, **zarys** i **wnioski** (TipTap; wspólne dla trzech wersji), `is_published`, archiwizacja. Treść wersji V / A / K jest w `content`, pula pytań w `assessment`, publikacja lekcji w `authoring`.
- **Zapisy** (D46): uczeń prosi o zapis, autor przyjmuje albo odrzuca.
- **Kolejność** (R10, D48): lekcja n+1 dostępna po zaliczeniu quizu lekcji n; zaliczenia w `lesson_completions`.
- Interfejs dla innych modułów (`service.py`): `get_visible_course`, `get_owned_course`, `get_visible_lesson` (bez reguł nauki), `get_owned_lesson`, `get_study_lesson(db, lesson_id, user)` (uczeń: przyjęty + opublikowana + odblokowana; autor i admin — każda widoczna), `mark_lesson_passed(db, user_id, lesson_id) -> UnlockedLesson | None` (bez `commit`), `is_accepted`, `accepted_student_ids`, `course_progress`, `passed_lesson_ids`, `published_lessons`, `active_lessons`, `lesson_number`, `lesson_issues(lesson)` (R11), `set_lesson_published` (dla `authoring`), `pending_request_count`, `list_courses`.
- Dane uczniów i autorów (imię, e-mail) bierze z `identity.service.get_users`, bez złączeń z `users`. Nie zależy od `content`, `learning_style` ani `assessment` — zaliczenie zapisuje `learning_style.hooks` przez `mark_lesson_passed`.

## Model danych

| Tabela | Kolumny |
|---|---|
| `courses` | `id`, `owner_id` → `users` (indeks), `title` (120), `description` (≤ 500), `introduction` (JSONB / null), `summary` (JSONB / null — „Podsumowanie i wnioski”), `is_published` (false), `is_archived` (false), `created_at`, `updated_at` |
| `lessons` | `id`, `course_id` → `courses` (indeks), `title` (120), `position`, `outline` (JSONB / null — „Zarys”), `conclusions` (JSONB / null — „Wnioski”), `is_published` (false), `is_archived`, `created_at`, `updated_at` |
| `enrollments` | `id`, `course_id` → `courses` (CASCADE), `student_id` → `users` (CASCADE, indeks), `status` (`pending` / `accepted` / `rejected`, `CHECK`), `requested_at`, `decided_at` (null); unikalne (`course_id`, `student_id`) |
| `lesson_completions` | `user_id` → `users` (CASCADE), `lesson_id` → `lessons` (CASCADE), `passed_at`; PK (`user_id`, `lesson_id`) — pierwsze zaliczenie lekcji |
| `course_owner_changes` | `id`, `course_id` → `courses` (CASCADE, indeks), `from_owner_id`, `to_owner_id`, `changed_by_id` → `users`, `changed_at` — zmiany właściciela przez administratora (D56) |

Migracje `6eb66f0c665b` (kursy, lekcje), `01324f58656d` (v3: `summary`, `outline`, `conclusions`, `lessons.is_published`, `enrollments`, `lesson_completions`; tabele klas z `249e835bc4e5` usunięte), `7d2e9b4c1a35` (`course_owner_changes`). „Usuń” kurs / lekcję = archiwizacja (historia uczniów zostaje). Nowa lekcja: na końcu (`max(position) + 1`), nieopublikowana.

## Logika

### Widoczność (`can_view_course`, `is_manager`)
- Administrator: wszystkie kursy, także zarchiwizowane (tylko odczyt, podgląd lekcji).
- Nauczyciel (zatwierdzony): tylko swoje niezarchiwizowane; cudzy kurs → 404.
- Uczeń: kurs niezarchiwizowany i (**opublikowany** albo **przyjęty** na niego) — przyjęty zachowuje dostęp po wycofaniu publikacji kursu.
- Uczeń widzi tylko **opublikowane** lekcje, ponumerowane wśród nich (`number`); autor i admin — wszystkie aktywne. Nieopublikowana lekcja dla ucznia → 404.
- Niewidoczny kurs / lekcja → 404 (`COURSE_NOT_FOUND`, `LESSON_NOT_FOUND`), nigdy 403 — nie zdradzamy istnienia. Niezatwierdzony nauczyciel → `403 TEACHER_NOT_APPROVED` także przy odczycie (`get_visible_*`, `get_owned_*`, `list_courses`).

### Dostęp do treści (`get_study_lesson`)
Uczeń: lekcja opublikowana (inaczej 404) → zapis `accepted` (inaczej `403 ENROLLMENT_REQUIRED`) → lekcja nie `locked` (inaczej `403 LESSON_LOCKED` z `required_lesson` {`id`, `title`, `number`}). Korzystają z tego `GET /lessons/{id}`, `learning_style` (`/study`, zmiana formy) i `assessment` (quiz, wysłanie odpowiedzi), więc blokadę egzekwuje serwer przy każdym dostępie.

### R10. Blokada lekcji (`progress.py`, czyste funkcje)
- `lesson_states(published_ids, passed_ids)`: lekcja `passed`, gdy zaliczona; `available`, gdy pierwsza albo poprzednia opublikowana jest zaliczona; inaczej `locked` z `required_lesson_id` i `required_number`. Zaliczona lekcja zostaje dostępna także po zmianie kolejności.
- `next_lesson_id(published_ids, lesson_id)`.
- Przykład: 4 lekcje, zaliczone 1 i 2 → `passed, passed, available, locked (najpierw lekcja 3)`. Nauczyciel przesuwa lekcję 4 na początek → nowa pierwsza jest `available`, zaliczone zostają `passed`.
- `mark_lesson_passed`: `INSERT … ON CONFLICT DO NOTHING` w `lesson_completions`; zwraca następną opublikowaną lekcję, gdy właśnie stała się dostępna (do `QuizFeedback.unlocked_lesson`).

### Zapisy
- `request_enrollment`: kurs musi być widoczny dla ucznia; brak wiersza → `pending` (201); `pending` → bez zmian (200); `rejected` → znów `pending` (nowe `requested_at`, `decided_at = null`); `accepted` → `409 ALREADY_ENROLLED`.
- `decide_enrollment`: autor ustawia `accepted` / `rejected` (powtórka bez zmian); może zmienić decyzję — także odrzucić przyjętego (traci dostęp do treści, wyniki zostają).

### Publikacja kursu i lekcji
- Kurs: `is_published = true` tylko z ≥ 1 opublikowaną lekcją (`409 COURSE_HAS_NO_PUBLISHED_LESSONS`); wycofanie zawsze dozwolone.
- Lekcja: publikuje `authoring` po sprawdzeniu gotowości (R11, `moduly/07-authoring.md`). Ostatniej opublikowanej lekcji opublikowanego kursu nie można wycofać ani zarchiwizować (`409 LAST_PUBLISHED_LESSON`).
- R11, część lekcji (`readiness.py`): `lesson_issues(outline, conclusions)` → `OUTLINE_MISSING`, `CONCLUSIONS_MISSING` (pusty dokument = `core.rich_text.is_empty_document`). `PATCH /lessons/{id}` opublikowanej lekcji, który wprowadziłby **nowy** brak → `409 PUBLISHED_LESSON_INCOMPLETE` z `issues`.
- `PATCH /lessons/{id}`: pominięte pole zostaje, `null` czyści zarys / wnioski (w szkicu). `PATCH /courses/{id}`: `null` w polu = bez zmiany.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /courses` | zalogowany | uczeń: opublikowane + przyjęte; nauczyciel: swoje; admin: wszystkie; od najnowszego → `CourseSummaryResponse[]` | 401, 403 `TEACHER_NOT_APPROVED` |
| `POST /courses` | nauczyciel | `{title, description?}` → 201, kurs prywatny | 403, 422 |
| `GET /courses/{id}` | widzący kurs | `CourseResponse` | 404 |
| `PATCH /courses/{id}` | autor | `title?`, `description?`, `introduction?`, `summary?`, `is_published?` | 404, 409 `COURSE_HAS_NO_PUBLISHED_LESSONS`, 422 |
| `DELETE /courses/{id}` | autor | archiwizacja, 204 | 404 |
| `POST /courses/{id}/lessons` | autor | `{title}` → 201, `LessonResponse` (nieopublikowana, na końcu) | 404, 422 |
| `PUT /courses/{id}/lessons/order` | autor | `{lesson_ids}` — każda aktywna lekcja dokładnie raz → `CourseResponse` | 400 `LESSON_ORDER_MISMATCH` |
| `GET /lessons/{id}` | widzący; uczeń: przyjęty + opublikowana + odblokowana | `LessonResponse` | 404, 403 `ENROLLMENT_REQUIRED`, 403 `LESSON_LOCKED` + `required_lesson` |
| `PATCH /lessons/{id}` | autor | `title?`, `outline?`, `conclusions?` | 404, 409 `PUBLISHED_LESSON_INCOMPLETE` + `issues`, 422 |
| `DELETE /lessons/{id}` | autor | archiwizacja, 204 | 404, 409 `LAST_PUBLISHED_LESSON` |
| `POST /courses/{id}/enrollment` | uczeń | prośba o zapis → 201 `EnrollmentResponse` (`pending`); powtórka przy `pending` → 200 | 404, 409 `ALREADY_ENROLLED`, 403 `FORBIDDEN` (inne role) |
| `GET /courses/{id}/enrollments?status=` | autor | `[{student: {id, display_name, email}, status, requested_at, decided_at}]`, od najstarszej prośby | 404, 422 |
| `POST /courses/{id}/enrollments/{student_id}/accept` / `reject` | autor | decyzja → `EnrollmentResponse` | 404 `ENROLLMENT_NOT_FOUND` / `COURSE_NOT_FOUND` |

„Autor” = właściciel kursu z zatwierdzonym kontem; inna rola przy endpointach autora dostaje 404 (kurs „nie istnieje”), a przy `POST /courses` — 403.

Schematy:
- `CourseSummaryResponse`: `id`, `title`, `description`, `owner` {`id`, `display_name`}, `is_published`, `is_archived`, `lesson_count` (uczeń: opublikowane; autor, admin: aktywne), `enrollment_status` (uczeń: `null` / `pending` / `accepted` / `rejected`), `progress` (uczeń przyjęty: {`passed`, `total`}), `pending_requests` (autor: liczba próśb), `updated_at`.
- `CourseResponse`: pola podsumowania + `introduction`, `summary`, `lessons`: [{`id`, `title`, `number`, `outline`, `is_published` (autor, admin), `state` (uczeń przyjęty: `passed` / `available` / `locked`), `required_lesson_number`}].
- `LessonResponse`: `id`, `title`, `number`, `outline`, `conclusions`, `is_published`, `course` {`id`, `title`, `owner_id`}, `previous_lesson_id`, `next_lesson_id` (wśród lekcji widocznych dla użytkownika), `next_lesson_unlocked` (uczeń; inni `null`).
- `EnrollmentResponse`: `course_id`, `status`, `requested_at`, `decided_at`.

Statystyki kursu i szczegóły ucznia (`/courses/{id}/stats`, `/courses/{id}/students/{id}`) oraz podpowiedź (`/courses/{id}/hint`) są w `learning_style` (`moduly/04-learning-style.md`).

## Frontend
- `features/courses` (uczeń, admin):
  - `/courses` — `CourseList`: uczeń — „Moje kursy” (przyjęte: `CourseProgressBar` „2 z 4 lekcji”, „Kontynuuj” do następnej lekcji z `/me/progress`) i „Katalog” (tytuł, opis, nauczyciel, liczba lekcji, `EnrollmentAction`: „Zapisz się” / „Prośba wysłana – czeka na nauczyciela” / „Prośba odrzucona” + „Poproś ponownie”); admin — wszystkie kursy (odczyt).
  - `/courses/[courseId]` — `CourseView`: wstęp, „Streszczenie kursu” (ponumerowane lekcje z zarysami i stanem: ✓ zaliczona, „Dostępna”, kłódka + „Najpierw zalicz lekcję n”), podpowiedź z kursu (R8) dla przyjętego ucznia bez wyników, „Podsumowanie i wnioski”; bez zapisu — `EnrollmentAction` zamiast stanów lekcji; autor / admin — podgląd (`PreviewBanner`).
  - Lekcja w trybie skupienia `(focus)/courses/[courseId]/lessons/[lessonId]`: `LessonScreen` wybiera `LessonStudy` (uczeń: zarys, `LessonFormBar`, wersja, wnioski, quiz, `LessonNav`) albo `LessonPreview` (autor, admin; `moduly/03-content.md`); `LessonMessage` — stany kłódki (`LESSON_LOCKED` z linkiem do wymaganej lekcji), brak zapisu, 404, błąd sieci; `LessonHeader`, `LessonParts` (`LessonSection`, `BlockList`, `LessonNav` — zablokowana następna lekcja odsyła do kursu).
  - Klucze: `["courses"]`, `["courses", id]`, `["lessons", id]`.
- `features/teach` (nauczyciel):
  - `/teach` — `TeacherCoursesPage`, `TeacherCourseCard` (tytuł, „Opublikowany” / „Prywatny” tekstem, „3 z 4 lekcji opublikowanych”, „2 prośby o zapis”), `NewCourseDialog`.
  - `/teach/courses/[courseId]` — `CourseEditor`: `CourseSettingsForm` (tytuł, opis, wstęp, podsumowanie i wnioski), `CoursePublishSwitch` (wyłączony bez opublikowanej lekcji, wycofanie z potwierdzeniem), `LessonList` (kolejność w górę / w dół, nazwa — `RenameLessonDialog`, usuwanie, stan z gotowości: „Opublikowana” / „Szkic – brakuje: wersja K, 2 pytania”), `AddLessonForm`, `ArchiveCourseSection`, link „Panel kursu”.
  - `/teach/courses/[courseId]/panel` — `CoursePanel`: `EnrollmentRequests` (imię, e-mail, data, „Przyjmij” / „Odrzuć”), `CourseStudentsTable` (imię, styl, procenty, postęp, średnia, ostatnia aktywność, otwarta propozycja; wiersz → szczegóły), `FormEffectiveness` (tabela V / A / K + paski w kolorach form z liczbą), `StyleDistribution`.
  - `/teach/courses/[courseId]/students/[studentId]` — `StudentDetailPage` (komponenty `features/progress` i `explain.ts`).
  - Klucze: `["courses", id, "enrollments"]`, `["courses", id, "stats"]`, `["courses", id, "students", studentId]`; decyzja o zapisie unieważnia prośby, statystyki i listę kursów.

## Testy
`backend/tests/curriculum/`:
- `test_courses.py`: tworzenie i walidacja, role, lista (nauczyciel — swoje, uczeń — opublikowane, admin — wszystkie z zarchiwizowanymi, kolejność), widoczność strony kursu, edycja częściowa, publikacja i wycofanie, kurs bez opublikowanej lekcji → 409, archiwizacja.
- `test_lessons.py`: dodawanie na końcu, kolejność (zła lista → 400, zarchiwizowane pominięte), sąsiedzi, widoczność za kursem, zmiana nazwy, archiwizacja, tylko autor.
- `test_lesson_fields.py`: zarys i wnioski (częściowa zmiana, `null` czyści szkic, zarys na stronie kursu), opublikowana lekcja nie traci zarysu / wniosków, ale można ją edytować, ostatnia opublikowana lekcja nie do archiwizacji, odrzucony nauczyciel traci dostęp do własnego kursu.
- `test_enrollments.py`: prośba, powtórka, ponowna po odrzuceniu, przyjęty nie prosi ponownie, kurs prywatny / zarchiwizowany / nieistniejący → 404, tylko uczeń, lista próśb (kolejność, filtr), przyjęcie, zmiana decyzji, tylko autor, prośby kursu zarchiwizowanego ukryte, dostęp przyjętego po wycofaniu publikacji.
- `test_lesson_access.py`: uczeń widzi tylko opublikowane lekcje z numeracją wśród nich, stany lekcji, `ENROLLMENT_REQUIRED`, `LESSON_LOCKED` z wymaganą lekcją, odblokowanie po zaliczeniu, ostatnia lekcja, zaliczona zostaje otwarta po zmianie kolejności, podgląd autora i admina.
- `test_progress.py`, `test_readiness.py`: czyste funkcje R10 i R11 (część lekcji).

## Jak sprawdzić ręcznie
- `uczen.nowy@imsu.pl` (po ankiecie): „Kursy” → „Zapisz się” przy Angielskim → „Prośba wysłana”; strona kursu bez stanów lekcji.
- `nauczyciel.demo@imsu.pl`: Matematyka → „Panel kursu” → prośba Zosi Mazur → „Przyjmij”; `uczen.zapis@imsu.pl` → Matematyka: lekcja 1 „Dostępna”, pozostałe z kłódką, podpowiedź z kursu.
- `uczen.demo@imsu.pl`: Matematyka — lekcje 1–2 zaliczone, 3 dostępna, 4 z kłódką; adres lekcji 4 wpisany ręcznie → komunikat z linkiem do lekcji 3.
- Nauczyciel: nowa lekcja (szkic, niewidoczna dla ucznia), zmiana kolejności, próba wycofania publikacji kursu bez opublikowanych lekcji.

## Ograniczenia
Brak moderacji kursów przez administratora (O6), powiadomień o prośbach i anulowania własnej prośby; jeden autor kursu (bez współautorów); `null` w `PATCH /courses/{id}` nie czyści wstępu ani podsumowania (pusty dokument TipTap — tak).
