# Konwencje projektu

## Język

- **Kod po angielsku**: nazwy plików, modułów, klas, funkcji, zmiennych, tabel, kolumn, endpointów, typów TypeScript, komentarzy i docstringów.
- **API w całości po angielsku**, łącznie z komunikatami błędów i wszystkimi tekstami w odpowiedziach.
- **Po polsku**: wyłącznie teksty interfejsu w frontendzie, dokumentacja w `docs/`, treść kursów.
- Backend nie zwraca gotowych zdań dla użytkownika (wyjątek: uzasadnienia i propozycje w `learning_style`, D3). Zwraca **kody i parametry** (np. błąd `{"code": "SURVEY_REQUIRED"}`, uzasadnienie `{"reason": "retry_other_form", "score": 45, "threshold": 70}`), a frontend tłumaczy je na polski tekst. Teksty z treści kursu (komunikaty, wyjaśnienia) są danymi, nie komunikatami systemu.
- Pojęcia domenowe — stały słownik (nie tłumaczyć różnie w różnych miejscach):

| Polski | W kodzie |
|---|---|
| kurs / lekcja | course / lesson |
| opis / wstęp kursu | description / introduction |
| autor kursu | owner |
| kurs prywatny / opublikowany | private / published (`is_published`) |
| klasa / uczeń klasy *(etap 6)* | class / class member (nazwa w specyfikacji etapu 6) |
| blok lekcji: tekst / załącznik | block: text / attachment |
| typ załącznika | attachment kind |
| forma: wzrokowa / słuchowa / kinestetyczna | form: `V` / `A` / `K` (załącznik ma zbiór `forms`) |
| plik | file |
| quiz / pytanie / odpowiedź / podejście | quiz / question / answer / quiz attempt |
| ankieta / pytanie ankiety / wynik ankiety | survey / survey question / survey result |
| profil, styl, źródło stylu, wagi | learning profile, style, style source, weights |
| styl efektywny lekcji | effective style |
| rozwinięcie zwiniętego materiału | material opening |
| propozycja zmiany stylu | style proposal |
| uzasadnienie („dlaczego to widzisz”) | explanation / why |
| uczeń / nauczyciel / administrator | student / teacher / admin |

## Backend

- Python 3.12+, typowanie, Ruff (lint + format).
- Struktura modułu i zasady zależności: `03-architektura.md`.
- Logika w `service.py` i w czystych funkcjach; routery cienkie.
- Nazwy schematów Pydantic: sufiks **`Request`** dla danych wejściowych i **`Response`** dla wyjściowych (`RegisterRequest`, `UserResponse`). Nazwa bez sufiksu (`User`) jest zarezerwowana dla modelu bazy danych.
- Zależność sesji: `DbSession` z `core/db.py`; zależności użytkownika: `CurrentUser`, `TeacherUser`, `AdminUser`, `require_role(...)` z `identity/dependencies.py`.
- Konwencja nazw ograniczeń w bazie (`pk_`, `uq_`, `ck_`, `fk_`, `ix_`) z `core/db.py`; nowe migracje formatowane automatycznie (hooki w `alembic.ini` — wymagają `ruff` na PATH, więc migracje generujemy przy aktywnym venv). Migracja danych zmienia tylko wiersze o oczekiwanej treści i ma `downgrade`.
- Testy pytest dla każdej reguły logiki (scenariusze) i dla uprawnień endpointów; testowa baza budowana migracjami. E-maile testowe w domenie `test.pl` (walidator odrzuca `.local`, `.test`).
- Błędy 500 bez treści wyjątku; sekrety tylko w `.env`.

## Frontend

- TypeScript strict, ESLint, Prettier z sortowaniem klas Tailwinda (`npm run format` przed commitem, `npm run format:check` w kontroli), struktura `features/` (`03-architektura.md` §6).
- Next.js 16 ma zmiany łamiące zgodność — patrz `frontend/AGENTS.md`; nowe trasy z `PageProps` wymagają `npx next typegen` (albo restartu `npm run dev`).
- Komponenty shadcn/ui w stylu `base-nova` (Base UI: `render` zamiast `asChild`); teksty angielskie w komponentach shadcn tłumaczymy.
- Kody błędów API → polskie komunikaty w `shared/api/error-messages.ts`; kody jednego featura we własnym `errors.ts` z przejściem do `errorMessage`.
- Kontrolki formularzy tylko z shadcn/ui (`RadioGroup`, `Checkbox`, `Select`, `AlertDialog` zamiast `window.confirm`), nie natywne `<input type="radio">` / `<select>`.
- Dane zależne od stylu ucznia (bloki, quiz) mają styl w kluczu zapytania; widok nauczyciela korzysta z kluczy edytora, nie z kluczy ucznia.
- Link w stylu przycisku: `className={cn(buttonVariants({ variant: "outline" }))}` — zawsze przez `cn`, bo samo `buttonVariants` nie usuwa sprzecznych klas (zostaje `border-transparent`).
- Formularz w oknie (`Dialog`) otwieranym z wnętrza innego formularza: `event.stopPropagation()` w `onSubmit` — portal nie przerywa przekazywania zdarzeń w drzewie Reacta.
- Struktura: `app/` odwzorowuje adresy (np. `[courseId]`), `features/<feature>/` jest płaskie (`api.ts`, `hooks.ts`, `types.ts`, `components/`), nazwy folderów i plików pomocniczych z myślnikiem (`rich-text`, `use-unsaved-changes-warning.ts`).
- Komponent z hookami ma własne `"use client"` (nawet gdy importuje go inny komponent kliencki); importy typów przez `import type`.

## Git

- Kod na `main`; wersja 1 pod tagiem `v1-final` (D4).
- Poprawki i małe etapy **bezpośrednio na `main`** (D4, od 10.11). Większy etap — na decyzję autora — na gałęzi z aktualnego `main`, nazwa po angielsku: `feat/<nazwa>`; gałąź można wypychać na serwer jako kopię zapasową.
- Koniec etapu na gałęzi (testy, test ręczny, raport): `git checkout main` → `git merge --no-ff feat/<nazwa>` → `git push origin main` → usunięcie gałęzi lokalnie i na serwerze.
- Przed pracą: `git pull` (repozytorium współdzielone z drugim autorem); po pobraniu cudzych zmian: `alembic upgrade head` i ewentualnie `python -m app.demo.seed`.
- AI czyta repozytorium autora tylko poleceniami bez zapisu (`git --no-optional-locks status`, `diff`, `log`, `show`); nie uruchamia `fetch`, `pull`, `commit` ani innych poleceń zmieniających `.git`.
- Ścieżki względne. Docker Compose ma stałą nazwę projektu `imsu` (wolumen bazy nie zależy od nazwy katalogu).
- Porty: backend 8001, frontend 3001, baza 5433.
- Małe commity w formacie **Conventional Commits**: `<type>(<scope>): <description>`, **po angielsku**, w trybie rozkazującym (`add`, `fix`…), małą literą, bez kropki na końcu.
  - typy: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`, `style`;
  - zakres: nazwa modułu (`identity`, `content`, `learning-style`, `assessment`…), `demo`, `core`, `backend`, `frontend` albo `infra`.
- Bez sekretów w repozytorium (`*.bak` ignorowane); wyjątek: hasło kont demo w seedzie — seed nie trafia na serwer produkcyjny (D30).
- **Kod wprowadza i commituje autor** (D5). Po każdym kroku AI podaje gotową nazwę commita i ewentualnie podział na kilka commitów.

## Dokumentacja

- Dokumentacja w `docs/` w repozytorium — jedno źródło prawdy dla obu autorów (D32). AI zmienia ją na prośbę autora albo zgodnie z procesem etapu (D5); plików kodu nie zmienia — kod podaje w rozmowie.
- **Commity dokumentacji razem z tym, co opisuje** (repozytorium czyta też drugi autor i jego AI): zaakceptowana specyfikacja w `08-praca-biezaca.md` — osobny commit `docs: …` i push od razu; postęp kroku w `08` — w commicie tego kroku; decyzja z rozmowy (`04-decyzje.md`) — najpóźniej z najbliższym commitem; zamknięcie etapu (`moduly/`, status w `05` i `00`, wyczyszczenie `08`) — jeden commit `docs: …`. Opisy modułów zmieniamy dopiero przy zamknięciu etapu.
- Każda zmiana decyzji → `04-decyzje.md`; każdy ukończony etap → status w `05-plan-etapow.md` i `00-START.md`.
- Bieżąca specyfikacja w `docs/08-praca-biezaca.md`; po zakończeniu pracy wynik w `docs/moduly/<nr>-<moduł>.md` (opis stanu, bez historii), a plik bieżący czyszczony. Bez osobnych plików SPEC / RAPORT.
