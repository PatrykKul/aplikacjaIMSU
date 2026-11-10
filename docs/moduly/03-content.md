# Moduł `content`

Bloki lekcji (tekst i załączniki z formami V / A / K) oraz pliki. Decyzje: D12, D13, D23–D25, D27, D28.

## Odpowiedzialność
- Treść lekcji jako uporządkowana lista **bloków** zapisywana w całości.
- Pliki: wgrywanie, przechowywanie na dysku, wydawanie.
- Dostęp sprawdza przez `curriculum.service.get_visible_lesson` / `get_owned_lesson`. Publiczny interfejs dla innych modułów: `service.get_blocks`, `service.save_blocks`, `service.save_upload`.

## Model danych

| Tabela | Kolumny |
|---|---|
| `lesson_contents` | `id`, `lesson_id` (unikalny), `blocks` (JSONB), `updated_at` |
| `files` | `id`, `owner_id` → `users`, `original_name`, `content_type`, `size`, `storage_name` (losowa, unikalna), `created_at` |

Migracja `908770dc9db3`. Pliki w `UPLOAD_DIR` (poza gitem).

## Bloki (`blocks.py`, dyskryminator `type`)

Wspólne: `id` (nadawany przez edytor, unikalny w lekcji — odwołują się do niego rozwinięcia materiałów), `type`.

| `type` | Pola |
|---|---|
| `text` | `doc` — dokument TipTap (`core/rich_text.py`) |
| `attachment` | `kind`, `forms` (niepusty podzbiór V / A / K, bez powtórzeń), `title`, `description?` + pola rodzaju |

| `kind` | Pola rodzaju |
|---|---|
| `image` | `file_id`, `alt` |
| `video` | `file_id` **albo** `youtube_url` (rozpoznawany przez `youtube_id()`) |
| `audio` | `file_id` **albo** `transcript` (tekst dla lektora przeglądarki) |
| `pdf` | `file_id` |
| `link` | `url` (`https`) |

Walidacja: unikalne `id`; `file_id` = plik autora kursu o rodzaju zgodnym z typem (`FILE_NOT_FOUND`, `FILE_KIND_MISMATCH`); dokładnie jedno źródło wideo / nagrania. W odpowiedzi pola tylko do wyświetlania: `file_url`, `file_name`, `youtube_id`.

## Pliki
- Biała lista rozszerzeń: obrazy (png, jpg, webp, gif), audio (mp3, ogg, wav, m4a), wideo (mp4, webm), PDF; **bez SVG / HTML**; typ z rozszerzenia, nie z nagłówka klienta.
- Limit 50 MB (`MAX_UPLOAD_BYTES`), zapis kawałkami, pusty plik odrzucany.
- `GET /files/{id}`: `inline`, `X-Content-Type-Options: nosniff`, obsługa Range (przewijanie wideo); dla każdego zalogowanego (prototyp, D24).

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /lessons/{id}/blocks` | widzący kurs | `{blocks}` | 404 |
| `PUT /lessons/{id}/blocks` | autor | zapis całości → `{blocks}` | 422 `VALIDATION_ERROR`, 400 `FILE_NOT_FOUND` / `FILE_KIND_MISMATCH` |
| `POST /files` | nauczyciel | multipart `file` → `{id, url, original_name, content_type, size}` | 400 `FILE_TYPE_NOT_ALLOWED` / `FILE_EMPTY`, 413 `FILE_TOO_LARGE` |
| `GET /files/{id}` | zalogowany | treść pliku | 404 `FILE_NOT_FOUND` |

## Frontend
- `shared/rich-text/`: `RichTextEditor` (TipTap: H2/H3, pogrubienie, kursywa, podkreślenie, listy, tabela, link, wzór `$…$` i „∑”, cofnij / ponów; wklejanie z Worda bez obrazów), `RichTextView` (tylko odczyt), okna wzoru i linku.
- `features/teach`: edytor lekcji `/teach/courses/[courseId]/lessons/[lessonId]` — bloki jako karty (w górę / w dół, edytuj, usuń), „+ Tekst” / „+ Załącznik” między blokami i pod listą, „Zapisz lekcję” i „Podgląd” w przyklejonym pasku, ostrzeżenie o niezapisanych zmianach; `AttachmentDialog` (krok 1: typ, krok 2: źródło, tytuł, opis, formy), `FileUpload` (react-dropzone, pasek postępu przez `XMLHttpRequest`), `AttachmentSummary` (miniatura, plakietki form).
- `features/content`: `BlockView`, `AttachmentView` (obraz, wideo z pliku / YouTube, nagranie z pliku / lektor `SpeechReader` `pl-PL`, PDF — przycisk i ramka od `sm`, link), `api.ts`, `hooks.ts` (`useLessonBlocks`, klucz `["lessons", id, "blocks"]`; `useSaveBlocks`).

## Testy
`backend/tests/content/`: blok tekstu, każdy rodzaj załącznika, błędne `forms`, dwa / brak źródeł, plik innego nauczyciela, rodzaj pliku niezgodny z typem, `youtube_id()`, pliki (dozwolone, `.svg`, `.exe`, za duży, pusty, pobranie z typem, Range dla wideo, nieistniejący), dostęp do bloków jak do lekcji.

## Jak sprawdzić ręcznie
Edytor lekcji: tekst + każdy typ załącznika (walidacje, `.svg` i plik > 50 MB odrzucone, przeciąganie pliku, YouTube, lektor), wstawienie między bloki, edycja, przesunięcie, zapis i F5 → podgląd; uczeń: odtwarzanie wideo / audio / YouTube, lektor, PDF, link.

## Ograniczenia
Wgrany, a niezapisany w lekcji plik zostaje na dysku; wklejony tekst z `$…$` nie zamienia się we wzory; wzory i obrazy z Worda się nie przenoszą; przejście przez nawigację `AppShell` z niezapisanymi zmianami nie pyta o potwierdzenie; YouTube wymaga internetu, głos lektora zależy od przeglądarki.
