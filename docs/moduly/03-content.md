# Moduł `content`

Trzy wersje lekcji (V / A / K) jako listy bloków (tekst, załączniki) oraz pliki. Decyzje: D12, D14, D23–D25, D28, D42, D49 (część wersji), D56 (pliki po zmianie właściciela), D58 (nagranie z transkrypcją), D59 (kod).

## Odpowiedzialność
- Treść lekcji w **trzech wersjach**: jedna lista bloków na formę (`V` — tekst ze schematami / filmem, `A` — nagranie + opis, `K` — instrukcja + karta PDF), zapisywana w całości. Zarys i wnioski (wspólne dla wersji) są w `curriculum`.
- Gotowość wersji do publikacji (R11, `readiness.py`) i ochrona opublikowanej lekcji przed utratą kompletności.
- Pliki: wgrywanie, przechowywanie na dysku, wydawanie.
- Dostęp przez `curriculum.service` (`get_visible_lesson`, `get_owned_lesson`). Interfejs dla innych modułów: `get_version(db, lesson_id, form)` (bloki gotowe do pokazania; dostęp sprawdza wołający — `learning_style` dla `/study`), `version_issues(db, lesson_id)` (dla `authoring`), `stored_versions`, `save_upload` (seed).

## Model danych

| Tabela | Kolumny |
|---|---|
| `lesson_contents` | `id`, `lesson_id` → `lessons`, `form` (`V` / `A` / `K`, `CHECK`), `blocks` (JSONB), `updated_at`; unikalne (`lesson_id`, `form`) — jeden wiersz na wersję |
| `files` | `id`, `owner_id` → `users` (indeks), `original_name`, `content_type`, `size`, `storage_name` (losowa, unikalna), `created_at` |

Migracje `908770dc9db3`, `01324f58656d` (kolumna `form`; istniejące bloki v2 stały się wersją V, z załączników usunięto `forms`). Brak wiersza = wersja pusta. Pliki w `UPLOAD_DIR` (domyślnie `backend/uploads`, poza gitem).

## Bloki (`blocks.py`, dyskryminator `type` / `kind`)

Wspólne: `id` (`[A-Za-z0-9_-]{1,40}`, unikalny w wersji), `type`. Do 200 bloków w wersji.

| `type` / `kind` | Pola |
|---|---|
| `text` | `doc` — dokument TipTap (`core/rich_text.py`: sprawdzany tylko korzeń `doc`, więc przechodzą wszystkie węzły edytora, także `codeBlock` i znacznik `code`, D59; `codeBlock` z kodem to treść niepusta) |
| `attachment` (wspólne) | `title` (1–120), `description` (≤ 500) |
| `image` | `file_id`, `alt` |
| `video` | `file_id` **albo** `youtube_url` (rozpoznawany przez `youtube_id()`: `watch?v=`, `youtu.be/`, `/embed/`, `/shorts/`) |
| `audio` | `file_id` i / albo `transcript` (1–5000 znaków) — co najmniej jedno (D58); plik + transkrypcja: nagranie z rozwijaną transkrypcją pod odtwarzaczem; sama transkrypcja: czyta ją lektor przeglądarki |
| `pdf` | `file_id` |
| `link` | `url` (tylko `https`) |

Załącznik **nie ma pola `forms`** — formę wyznacza wersja (D42). Walidacja: unikalne `id`; dokładnie jedno źródło wideo; nagranie z plikiem, transkrypcją albo jednym i drugim; `file_id` = plik o rodzaju zgodnym z typem (`400 FILE_KIND_MISMATCH`) należący do **autora kursu albo już użyty w którejś wersji tej lekcji** (D56: po zmianie właściciela nowy autor zachowuje załączniki poprzedniego; inaczej `400 FILE_NOT_FOUND`). Nieznane pola (np. odesłane `file_url`) są ignorowane. W odpowiedzi pola tylko do wyświetlania: `file_url`, `file_name`, `youtube_id`.

## R11 — gotowość wersji (`readiness.py`, czysta funkcja `version_issues(form, blocks)`)

| Wersja | Wymaga | Kod braku |
|---|---|---|
| każda | co najmniej jeden blok | `VERSION_EMPTY` (wtedy bez kodów szczegółowych) |
| V | niepusty blok tekstu **i** obraz albo wideo | `V_VISUAL_MISSING` |
| A | nagranie (plik, tekst lektora albo oba) | `A_AUDIO_MISSING` |
| A | niepusty blok tekstu (krótki opis) | `A_DESCRIPTION_MISSING` |
| K | niepusty blok tekstu (instrukcja) | `K_INSTRUCTION_MISSING` |
| K | PDF (karta zadania) | `K_WORKSHEET_MISSING` |

Braki mają `area` = forma. `PUT /lessons/{id}/versions/{form}` opublikowanej lekcji, który wprowadziłby **nowy** brak w tej wersji (porównanie braków przed i po), → `409 PUBLISHED_LESSON_INCOMPLETE` z `issues`; zapis bez nowego braku przechodzi.

## Pliki (`files.py`)
- Biała lista rozszerzeń: obrazy (png, jpg, jpeg, webp, gif), audio (mp3, ogg, wav, m4a), wideo (mp4, webm), PDF; **bez SVG / HTML**; typ z rozszerzenia, nie z nagłówka klienta.
- Limit 50 MB (`MAX_UPLOAD_BYTES`), zapis kawałkami (1 MB), przerwany / za duży / pusty plik usuwany z dysku.
- `GET /files/{id}`: `inline`, `X-Content-Type-Options: nosniff`, `Cache-Control: private`, obsługa Range (przewijanie wideo); dla każdego zalogowanego (prototyp, D24).

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/versions` | autor, admin | `{"V": {"blocks": […]}, "A": {…}, "K": {…}}` (pusta lista dla wersji bez treści) | 404 `LESSON_NOT_FOUND`, 403 `TEACHER_NOT_APPROVED` |
| `PUT /lessons/{id}/versions/{form}` | autor | `{blocks}` → `{blocks}` (zastępuje wersję) | 422 `VALIDATION_ERROR` (także nieznana forma), 400 `FILE_NOT_FOUND` / `FILE_KIND_MISMATCH`, 409 `PUBLISHED_LESSON_INCOMPLETE` + `issues`, 404 |
| `POST /files` | nauczyciel (zatwierdzony) | multipart `file` → `{id, url, original_name, content_type, size, kind}` | 400 `FILE_TYPE_NOT_ALLOWED` / `FILE_EMPTY`, 413 `FILE_TOO_LARGE`, 403 |
| `GET /files/{id}` | zalogowany | treść pliku | 404 `FILE_NOT_FOUND`, 401 |

Uczeń nie ma dostępu do `versions` (404) — swoją wersję dostaje przez `GET /lessons/{id}/study` (`learning_style`). Endpointy v2 `GET` / `PUT /lessons/{id}/blocks` nie istnieją.

## Frontend
- `shared/rich-text/`: `RichTextEditor` (TipTap: H2/H3, pogrubienie, kursywa, podkreślenie, listy, tabela, link, wzór `$…$` i „∑”, cofnij / ponów; wklejanie z Worda bez obrazów), `RichTextView` (tylko odczyt), okna wzoru i linku, `is-empty.ts` (pusty dokument — ta sama reguła co backend).
- Edytor lekcji `features/teach` (`/teach/courses/[courseId]/lessons/[lessonId]?tab=`, opis zakładek i publikacji w `moduly/07-authoring.md`): zakładki wersji „Wzrokowa (V)”, „Słuchowa (A)”, „Praktyczna (K)” z `VersionEditor` — bloki jako karty `BlockCard` (w górę / w dół, edytuj, usuń), `InsertBlockBar` („+ Tekst”, „+ Załącznik” między blokami i pod listą), podpowiedź, co wersja musi zawierać (R11 sprawdzane na żywo na niezapisanych blokach, `teach/readiness.ts`), `SaveBar` (przyklejony pasek zapisu), `SaveErrorAlert` (409 z listą braków); `AttachmentDialog` (krok 1: typ, krok 2: źródło, tytuł, opis — bez form), `FileUpload` (react-dropzone, sprawdzenie typu i rozmiaru przed wysłaniem, pasek postępu przez `XMLHttpRequest`), `AttachmentSummary`; ostrzeżenie o niezapisanych zmianach (`use-unsaved-changes-warning.ts`).
- `features/content`: `BlockView`, `AttachmentView` (obraz, wideo z pliku / YouTube, nagranie z pliku / lektor `SpeechReader` `pl-PL`, PDF — przycisk i ramka od `sm`, link), `attachment-kinds.ts`, `api.ts`, `hooks.ts` (`useLessonVersions`, klucz `["lessons", id, "versions"]`; zapis wersji ustawia dane w kluczu i unieważnia `["lessons", id, "readiness"]`). `FormBadge.tsx` zostało w katalogu, ale nic go już nie importuje.
- Podgląd lekcji (`features/courses/LessonPreview`, autor i admin): zarys, przełącznik wersji V / A / K (bloki z klucza edytora — aktualne zaraz po zapisie), wnioski, pula pytań (`QuizPoolPreview`).

## Testy
`backend/tests/content/`:
- `test_blocks.py`: `youtube_id()` dla znanych i obcych adresów.
- `test_versions.py`: nowa lekcja ma trzy puste wersje, zapis każdej wersji osobno, zapis zastępuje wersję, załącznik bez `forms`, serwis (`get_version`, `version_issues`), nagranie z plikiem i transkrypcją naraz, nagranie bez pliku i transkrypcji → 422, błędne bloki i nieznana forma → 422, plik innego nauczyciela i niezgodny rodzaj → 400, po zmianie właściciela zapis z plikami poprzedniego autora użytymi w lekcji (także przeniesionymi do innej wersji) przechodzi, a nieużyty plik poprzedniego autora → 400, opublikowana lekcja: zapis z nowym brakiem → 409, kompletny zapis przechodzi; wersje tylko dla autora, odrzucony nauczyciel → 403, bez logowania → 401.
- `test_readiness.py`: każdy kod R11 dla V / A / K (komplet i braki; nagranie z plikiem, transkrypcją albo oboma).
- `tests/test_rich_text.py`: dokument z `codeBlock` i znacznikiem `code` przechodzi walidację, kod liczy się jako treść (`is_empty_document`).
- `test_files.py`: dozwolone pliki, inne typy, za duży (bez śladu na dysku), pusty, brak pola, tylko nauczyciel, pobieranie `inline`, Range dla wideo, logowanie, nieistniejący.

## Jak sprawdzić ręcznie
`nauczyciel.demo@imsu.pl`: dowolna lekcja demo → zakładki V / A / K (obraz, MP3, karta PDF) → nowa lekcja: dodanie tekstu i obrazu w V (podpowiedź znika), nagrania jako tekst lektora w A, PDF w K, wstawienie bloku między innymi, przesunięcie, zapis i F5 → „Podgląd” z przełącznikiem wersji. W opublikowanej lekcji usunięcie jedynego PDF z wersji K i zapis → komunikat z brakiem. Uczeń: odtwarzanie MP3, lektor, PDF w ramce.

## Ograniczenia
Wgrany, a niezapisany w lekcji plik zostaje na dysku; wklejony tekst z `$…$` nie zamienia się we wzory; wzory i obrazy z Worda się nie przenoszą; przejście przez nawigację `AppShell` z niezapisanymi zmianami nie pyta o potwierdzenie; YouTube wymaga internetu, głos lektora zależy od przeglądarki; R11 sprawdza obecność elementów, nie to, że trzy wersje uczą tego samego.
