# Praca bieżąca

Specyfikacja tego, co teraz robimy. Po zakończeniu: wynik trafia do `moduly/<nr>-<moduł>.md`, decyzje do `04-decyzje.md`, status do `05-plan-etapow.md` i `00-START.md`, a ten plik czyścimy (historia w gicie).

---

# Etap 6 — klasy i dostęp do kursów   (10.11.2026)
Status: **zaakceptowana** (10.11.2026)

Gałąź: `feat/classes` (większy etap, D4). Decyzje: D10 (dostęp przez klasy), O6 (administrator).

## Odpowiedzialność
- Nauczyciel tworzy **klasy**, dodaje do nich istniejących uczniów (wyszukiwanie po e-mailu), usuwa ich, zmienia nazwę klasy, usuwa klasę i **przypisuje klasie swoje kursy** (opublikowane i prywatne).
- Uczeń widzi **katalog** (kursy opublikowane — jak dziś) oraz **swoje klasy**: nazwę, nauczyciela (imię i e-mail do kontaktu) i kursy klasy (bez listy uczniów).
- Administrator — bez klas w tym etapie (O6).
- Kurs prywatny przypisany klasie jest dostępny dla jej uczniów (lekcje, quizy, personalizacja — przez istniejące reguły widoczności).

## Analiza (obecny kod)
- Widoczność kursu jest w jednym miejscu: `curriculum.service.can_view_course` (uczeń: opublikowany; nauczyciel: swój; admin: wszystko) i `list_courses`. Z `get_visible_course` / `get_visible_lesson` korzystają `content`, `learning_style` i `assessment` — zmiana reguły w `can_view_course` wystarczy, żeby lekcje, bloki, quizy i rozwinięcia działały dla kursów klasy.
- Klasy łączą użytkowników i kursy, a widoczność kursu zależy od klas, więc **klasy są częścią modułu `curriculum`** (osobny moduł tworzyłby cykl: `curriculum` ↔ klasy). Pliki `classrooms.py` (logika) obok `service.py`, wspólne `models.py`, osobny router.
- `identity` nie ma wyszukiwania uczniów dla nauczyciela (tylko lista dla administratora) — dochodzi `search_students`.
- Frontend: `features/courses` (katalog, strona kursu, lekcja), `features/teach` (panel nauczyciela), nawigacja w `AuthenticatedShell`, karty panelu w `DashboardHome`.

## Model danych

Migracja `create classrooms tables` (moduł `curriculum`). W kodzie „klasa” = `classroom` (słowo `class` jest zarezerwowane w Pythonie).

| Tabela | Kolumny | Uwagi |
|---|---|---|
| `classrooms` | `id`, `teacher_id` → `users`, `name` (80), `created_at`, `updated_at` | właściciel = nauczyciel, który ją utworzył (jeden nauczyciel na klasę); usunięcie klasy usuwa jej powiązania (CASCADE) |
| `classroom_students` | `classroom_id` → `classrooms` (CASCADE), `student_id` → `users` (CASCADE), `added_at` | PK (`classroom_id`, `student_id`); wiele do wielu — uczeń może być w kilku klasach |
| `classroom_courses` | `classroom_id` → `classrooms` (CASCADE), `course_id` → `courses` (CASCADE), `assigned_at` | PK (`classroom_id`, `course_id`); wiele do wielu; tylko kursy nauczyciela klasy |

## Widoczność kursu (nowa reguła)
- Administrator: wszystkie kursy (bez zmian).
- Nauczyciel: tylko swoje (bez zmian).
- Uczeń: kurs niezarchiwizowany i (**opublikowany** albo **przypisany do klasy, do której uczeń należy**).
- `GET /courses` dla ucznia zostaje **katalogiem**: tylko opublikowane. Kursy klas uczeń widzi na stronie klasy.

## API

Klasy (`curriculum`, router `/classrooms`):

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /classrooms` | nauczyciel, uczeń | nauczyciel: swoje klasy; uczeń: klasy, do których należy; pola: `id`, `name`, `teacher` (`id`, `display_name`, `email`), `course_count`, dla nauczyciela też `student_count` | 403 `FORBIDDEN` (administrator) |
| `POST /classrooms` | nauczyciel | `{name}` → 201, klasa | 422 |
| `GET /classrooms/{id}` | właściciel, uczeń klasy | klasa, `courses` (podsumowania kursów; dla ucznia tylko niezarchiwizowane); **tylko dla nauczyciela** `students` (`id`, `display_name`, `email`) | 404 `CLASSROOM_NOT_FOUND` (niewidoczna też 404), 403 (administrator) |
| `PATCH /classrooms/{id}` | właściciel | `{name}` | 404 |
| `DELETE /classrooms/{id}` | właściciel | **usunięcie** klasy z powiązaniami, 204 (uczniowie tracą dostęp do kursów prywatnych tej klasy; kursy i konta zostają) | 404 |
| `PUT /classrooms/{id}/students/{student_id}` | właściciel | dodanie ucznia, 204 (ponowne — bez zmian) | 404 `CLASSROOM_NOT_FOUND`, 404 `STUDENT_NOT_FOUND` (nie istnieje albo nie jest uczniem) |
| `DELETE /classrooms/{id}/students/{student_id}` | właściciel | usunięcie z klasy, 204 | 404 |
| `PUT /classrooms/{id}/courses/{course_id}` | właściciel | przypisanie swojego kursu, 204 | 404 `COURSE_NOT_FOUND` (cudzy / zarchiwizowany) |
| `DELETE /classrooms/{id}/courses/{course_id}` | właściciel | odpięcie kursu, 204 | 404 |

Wyszukiwanie uczniów (`identity`): `GET /students?email=` — nauczyciel; aktywni uczniowie, których **e-mail** zawiera podany tekst (bez względu na wielkość liter, min. 3 znaki), najwyżej 20, wg e-maila; pola `id`, `display_name`, `email`. Krótszy tekst → 422.

## Frontend

**Nauczyciel** (`features/teach`):
- Nawigacja: „Moje kursy”, **„Klasy”** (`/teach/classes`); karta „Klasy” na `/dashboard`.
- `/teach/classes`: karty klas (nazwa, liczba uczniów i kursów), „+ Nowa klasa” (okno z nazwą).
- `/teach/classes/[classroomId]`: nazwa (zmiana w oknie), dwie sekcje:
  - **Uczniowie**: lista (imię, e-mail, „Usuń z klasy”), „+ Dodaj ucznia” — okno z polem „E-mail ucznia” (od 3 znaków, wyniki na bieżąco: e-mail i imię), przy wyniku „Dodaj”; uczeń już w klasie oznaczony.
  - **Kursy**: lista przypisanych (tytuł, plakietka Prywatny / Opublikowany, „Odepnij”), „+ Przypisz kurs” — okno z listą swoich nieprzypisanych kursów.
  - „Usuń klasę” (usunięcie z potwierdzeniem: „Uczniowie stracą dostęp do prywatnych kursów tej klasy. Kursy i konta uczniów zostaną.”).
- Edytor kursu: bez zmian (przypisania tylko z poziomu klasy).

**Uczeń** (`features/classes`):
- Nawigacja: „Kursy” (katalog — bez zmian), **„Moje klasy”** (`/classes`), „Mój styl”; karta „Moje klasy” na `/dashboard`.
- `/classes`: karty klas (nazwa, nauczyciel, liczba kursów); pusty stan „Nie należysz jeszcze do żadnej klasy. Nauczyciel doda Cię do klasy.”
- `/classes/[classroomId]`: nazwa, nauczyciel (imię i e-mail do kontaktu), **Kursy** (karty jak w katalogu, prowadzą do `/courses/[id]`).
- Strona kursu i lekcja — bez zmian (dostęp wynika z nowej reguły widoczności).

## Dane demo
Seed tworzy klasę „Klasa 7a” nauczyciela demo z oboma uczniami demo i przypisuje jej kurs „Programowanie: pętle w Pythonie”, który staje się **prywatny** — w pokazie: kurs znika z katalogu, a uczniowie widzą go w klasie.

## Testy
- Widoczność: uczeń widzi prywatny kurs swojej klasy (kurs, lekcja, bloki, quiz); nie widzi go po usunięciu z klasy, po odpięciu kursu i po usunięciu klasy; uczeń spoza klasy — 404; katalog bez kursów prywatnych; kurs opublikowany przypisany klasie — w katalogu i w klasie.
- Klasy: tworzy tylko nauczyciel; administrator — 403; cudza klasa — 404 (odczyt i zmiany); uczeń widzi tylko swoje klasy, bez listy uczniów; dodanie: nie-uczeń / nieistniejący → `STUDENT_NOT_FOUND`, powtórka bez błędu; przypisanie cudzego / zarchiwizowanego kursu → 404; zmiana nazwy; usunięcie klasy usuwa powiązania, a kursy i konta zostają.
- Wyszukiwanie uczniów: tylko nauczyciel; po fragmencie e-maila, bez wielkości liter; bez zablokowanych, nauczycieli i administratorów; limit; za krótki tekst → 422.
- Seed: klasa z dwoma uczniami i kursem prywatnym; idempotencja.

## Kroki implementacji (commity na `feat/classes`)

| Krok | Zakres | Commit (propozycja) |
|---|---|---|
| S1 | modele i migracja klas | `feat(curriculum): add classrooms with students and courses` |
| S2 | API klas nauczyciela + wyszukiwanie uczniów + testy | `feat(curriculum): let teachers manage classrooms` (+ `feat(identity): let teachers search students`) |
| S3 | widoczność kursów klasy + widok klasy ucznia + testy | `feat(curriculum): give classroom students access to assigned courses` |
| S4 | frontend nauczyciela: lista i strona klasy | `feat(teach): add classroom management` |
| S5 | frontend ucznia: „Moje klasy”, nawigacja, panel | `feat(frontend): add student classrooms` |
| S6 | seed demo, dokumentacja (`moduly/02-curriculum.md`, decyzje, status, scenariusz) | `feat(demo): add a demo classroom` + `docs: …` |

## Poza zakresem
Współprowadzący klasy, zaproszenia / kody dołączenia do klasy, import listy uczniów, terminy i zadania dla klasy, panel wyników klasy (styl, quizy — O3), moderacja kursów przez administratora.

## Rozstrzygnięcia (10.11)
1. Uczniowie i klasy oraz klasy i kursy — wiele do wielu.
2. Jeden nauczyciel na klasę (właściciel), bez współprowadzących.
3. Dodawanie uczniów: wyszukiwanie istniejących **po e-mailu**.
4. Uczeń **nie widzi** uczestników klasy.
5. Katalog — tylko kursy opublikowane; kursy klasy na stronie klasy.
6. Administrator — bez klas w tym etapie (O6).
7. Przypisać klasie można też kurs opublikowany.
8. Dane demo: „Klasa 7a” z oboma uczniami demo, „Programowanie” jako prywatny kurs klasy.
9. Klasę się **usuwa** (z powiązaniami), bez archiwizacji.

---
## Stan realizacji

**Kroki zrobione (commity):**
- S1 — modele `Classroom`, `ClassroomStudent`, `ClassroomCourse` w `curriculum/models.py`, migracja `249e835bc4e5` (`create classrooms tables`); tabele łączące z kluczem złożonym, kaskadą do klasy, ucznia i kursu oraz indeksem na `student_id` / `course_id` (wyszukiwanie klas ucznia i sprawdzanie dostępu do kursu w S3); bez relacji ORM (usuwanie powiązań przez `ON DELETE CASCADE` w bazie).
- S2 — `GET /students?email=` (`identity`: `search_students`, `StudentResponse`; dla innych modułów `get_users`, `get_active_student`); API klas nauczyciela w `curriculum/classrooms.py` + `classrooms_router`; na razie wszystkie endpointy `/classrooms` tylko dla nauczyciela (uczeń dostaje odczyt w S3). Testy: `tests/identity/test_student_search.py`, `tests/curriculum/test_classrooms.py` (43).

**Decyzje w trakcie:**
- Dodać do klasy można tylko **aktywnego** ucznia (zablokowany → `STUDENT_NOT_FOUND`, jak w wyszukiwaniu); zablokowany uczeń już w klasie zostaje na liście.
- `DELETE` ucznia / kursu, którego nie ma w klasie → 204 bez zmian (jak ponowne `PUT`); 404 tylko dla niewidocznej klasy.
- Nauczyciel widzi w klasie także kursy **zarchiwizowane** (`is_archived`), żeby mógł je odpiąć; `course_count` na liście klas nauczyciela liczy wszystkie przypisane.
- **E-mail nauczyciela** w danych klasy (`teacher.email`) — uczeń widzi go do kontaktu; dostają go tylko uczniowie tej klasy (zmiana autora 11.11).
- Kolejność: klasy wg nazwy, kursy klasy wg tytułu, uczniowie klasy wg imienia.
- Wyszukiwanie: znaki `%` i `_` traktowane dosłownie; tekst przycinany, min. 3 znaki po przycięciu.
- `curriculum` pobiera dane uczniów przez `identity.service` (bez złączeń z `users`); `classrooms.py` korzysta z `service.py`, nie odwrotnie (w S3 sprawdzenie członkostwa w `service.can_view_course` zapytaniem na tabelach klas, bez importu `classrooms.py`).

**Do zrobienia:** S3–S6.
