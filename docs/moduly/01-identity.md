# Moduł `identity` (+ `core`)

Konta, role, sesja, zatwierdzanie nauczycieli, administracja kont. Decyzje: D3, D8, D9, D47.

## Odpowiedzialność
- `identity`: konta, role (stałe), rejestracja, logowanie, wylogowanie, „kim jestem”, **zatwierdzanie kont nauczycieli** przez administratora, zarządzanie kontami uczniów i nauczycieli, polecenie `create-admin`.
- Dla innych modułów (`service.py`): `get_users(db, ids)` (użytkownicy wg imienia — `curriculum` i `learning_style` biorą stąd imię i e-mail), `get_active_student`, `get_by_email`, `create_user` (seed), `set_teacher_approval` (seed), `require_approved(user)` (nauczyciel niezatwierdzony → `403 TEACHER_NOT_APPROVED`).
- Zależności FastAPI (`dependencies.py`): `CurrentUser` (zalogowany, aktywny), `TeacherUser` (nauczyciel **zatwierdzony**), `StudentUser`, `AdminUser`, `require_role(...)`.
- `core`: ustawienia (`config.py`), sesja bazy (`db.py`, `DbSession`, konwencja nazw ograniczeń), błędy (`errors.py`), `GET /health`, dokument TipTap (`rich_text.py`: typ `RichTextDocument` i `is_empty_document` — dokument pusty albo z samymi pustymi akapitami; ta sama reguła co `shared/rich-text/is-empty.ts` we frontendzie).

## Model danych

`users`: `id`, `email` (254, unikalny, po `trim` i małymi literami), `password_hash` (bcrypt), `display_name` (80), `role` (`student` / `teacher` / `admin`, `CHECK`), `approval_status` (`approved` / `pending` / `rejected`, `CHECK`, domyślnie `approved`), `is_active` (domyślnie `true`), `created_at`. Migracje `be52e423dcf8`, `01324f58656d` (`approval_status`). Styl ucznia jest w `learning_style`.

`approval_status`: samodzielna rejestracja nauczyciela → `pending`; uczeń, administrator i nauczyciel założony przez administratora → `approved`.

## Sesja i bezpieczeństwo
- JWT HS256 (`sub` = id, `iat`, `exp`, 480 min) w ciasteczku `imsu_access_token`: `HttpOnly`, `SameSite=Lax`, `Path=/`. **Bez roli w tokenie** — rola, aktywność i zatwierdzenie czytane z bazy przy każdym żądaniu, więc blokada i odrzucenie działają od razu.
- `JWT_SECRET` wymagany (≥ 32 znaki). Hasło 8–72 bajty UTF-8 (limit bcrypt); uszkodzony hash → logowanie nieudane. CSRF: `SameSite=Lax` + API tylko JSON + CORS tylko dla adresu frontendu.
- Nauczyciel `pending` / `rejected` **loguje się** normalnie; każdy endpoint nauczyciela (`TeacherUser`) i odczyt kursów / lekcji przez niego (`curriculum.get_visible_*`, `get_owned_*`, `list_courses` wołają `require_approved`) zwraca `403 TEACHER_NOT_APPROVED`.

## Format błędów (`core/errors.py`)
- `AppError(status, code, **params)` → `{"code": "...", ...params}` (parametry JSON, np. `issues`, `required_lesson`); walidacja 422 → `{"code": "VALIDATION_ERROR", "fields": [{"field", "type"}]}`; 500 → `{"code": "INTERNAL_ERROR"}` bez treści wyjątku; błędy frameworka → `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `HTTP_ERROR`.
- Kody modułu: `EMAIL_TAKEN`, `INVALID_CREDENTIALS`, `NOT_AUTHENTICATED`, `FORBIDDEN`, `USER_NOT_FOUND`, `TEACHER_NOT_APPROVED`.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `POST /auth/register` | każdy | `email`, `password`, `display_name`, `role` (`student` \| `teacher`) → 201, `UserResponse`, ciasteczko; nauczyciel `pending` | 409 `EMAIL_TAKEN`, 422 (także `role=admin`) |
| `POST /auth/login` | każdy | → `UserResponse`, ciasteczko (także nauczyciel `pending` / `rejected`) | 401 `INVALID_CREDENTIALS` (także konto zablokowane) |
| `POST /auth/logout` | każdy | 204, usuwa ciasteczko | |
| `GET /auth/me` | zalogowany | `UserResponse` | 401 `NOT_AUTHENTICATED` |
| `GET /users?role=&approval=` | admin | uczniowie albo nauczyciele (`role` wymagane), opcjonalnie wg `approval_status`; wg e-maila | 401, 403, 422 |
| `POST /users` | admin | konto ucznia / nauczyciela (od razu `approved`) → 201, bez ciasteczka | 409, 422 |
| `PATCH /users/{id}` | admin | `display_name?`, `email?`, `password?`, `is_active?` (`role` → 422) | 404 `USER_NOT_FOUND` (także konto administratora), 409 |
| `POST /users/{id}/approve` | admin | nauczyciel → `approved` (powtórka bez zmian) → `UserResponse` | 404 `USER_NOT_FOUND` (nie nauczyciel) |
| `POST /users/{id}/reject` | admin | nauczyciel → `rejected` (także wcześniej zatwierdzony) | 404 |
| `GET /health` | każdy | `{"status": "ok", "database": "ok" \| "error"}` | |

`UserResponse`: `id`, `email`, `display_name`, `role`, `approval_status`, `is_active`, `created_at`. Konto administratora jest dla API administracji „nieistniejące”. CLI: `python -m app.modules.identity.cli create-admin --email … --name …` (hasło przez `getpass`). Wyszukiwanie uczniów `GET /students` (v2, dla klas) nie istnieje.

## Frontend
- `features/auth`: `api.ts`, `hooks.ts` (`useCurrentUser` = `GET /auth/me`, klucz `["auth","me"]`; logowanie, rejestracja, wylogowanie), `roles.ts` (`roleLabels`, `approvalLabels`, `isUnapprovedTeacher`, `homePath`, `PENDING_PATH`), `validation.ts`, komponenty `LoginForm`, `RegisterForm` (kafelki ról na `RadioGroup`), `AuthGuard` (bez sesji → `/`), `GuestGuard`, `RoleGate` (strona tylko dla ról; niezatwierdzony nauczyciel → `/pending`), `RootRedirect` (gość — strona startowa, zalogowany → `homePath`), `AuthenticatedShell` (nawigacja według roli; nauczyciel niezatwierdzony — bez pozycji; menu użytkownika w `shared/layout/AppShell`), `PendingApprovalPage` (`/pending`: „Konto czeka na zatwierdzenie przez administratora” albo „Konto nauczyciela nie zostało zatwierdzone” + „Wyloguj”).
- Globalnie (`shared/api/query-provider.tsx`): błąd `TEACHER_NOT_APPROVED` z dowolnego zapytania lub mutacji unieważnia `["auth","me"]` — nauczyciel odrzucony w trakcie sesji trafia na `/pending`.
- `features/users` (`/admin/users`): zakładki Nauczyciele / Uczniowie, tabela (imię, e-mail, status, data); u nauczycieli kolumna „Konto” tekstem (Zatwierdzone / Czeka na zatwierdzenie / Odrzucone), filtr „Czekające (n)” (przyciski `aria-pressed`), „Zatwierdź” (konto niezatwierdzone) i „Odrzuć” (konto `pending`, z `AlertDialog`); `UserFormDialog` (dodawanie i edycja, nowe hasło opcjonalne), blokada z potwierdzeniem. Klucz `["users", role]`.
- `features/dashboard` (`/dashboard`): powitanie i karty w kolejności menu roli; niezatwierdzony nauczyciel → `/pending`.
- `features/landing`: `LandingPage` pod `/` dla gościa; `features/health`: `HealthStatus` (plac zabaw `/dev/ui`).
- Trasy: `(auth)/login`, `(auth)/register`, `/`, `/dashboard`, `/pending`, `/admin/users`, `/dev/ui`, `/dev/shell` (tylko tryb deweloperski).
- Nawigacja: uczeń — „Kursy”, „Moje postępy”, „Mój styl”; nauczyciel — „Moje kursy”; admin — „Użytkownicy”, „Kursy”. „Wyloguj” → `/`.

## Testy
`backend/tests/identity/`, `test_errors.py`, `test_health.py`: hasła i tokeny (`test_security.py`), rejestracja (role, duplikat bez względu na wielkość liter, walidacja, `role=admin` odrzucone), logowanie (normalizacja e-maila, zablokowane konto), `/auth/me` (brak, podrobiony, wygasły token), blokada i rola czytane z bazy, wylogowanie, administracja kont (lista według roli, tworzenie, edycja, `role` → 422, konto admina → 404); **zatwierdzanie** (`test_approval.py`: nauczyciel z rejestracji `pending`, uczeń i nauczyciel od administratora `approved`, logowanie `pending`, `TEACHER_NOT_APPROVED` na endpointach nauczyciela, zatwierdzony działa, approve / reject tylko dla nauczyciela i tylko przez admina, filtr `approval` i jego walidacja); CLI; format błędów i 500 bez treści wyjątku; `/health`.

## Jak sprawdzić ręcznie
- `nauczyciel.nowy@imsu.pl` (`Demo123!`): logowanie → `/pending`, menu puste; wejście na `/teach` → z powrotem na `/pending`.
- `admin.demo@imsu.pl`: `/admin/users` → Nauczyciele → „Czekające (1)” → „Zatwierdź” Piotra Zielińskiego; nauczyciel po odświeżeniu widzi „Moje kursy”. Odrzucenie z potwierdzeniem → ekran „nie zostało zatwierdzone”.
- Rejestracja nowego nauczyciela → ekran oczekiwania; ucznia → ankieta. Blokada ucznia przez admina → nie zaloguje się.
- Przywrócenie stanu pokazu: `python -m app.demo.seed --reset-students` (nauczyciel nowy znów `pending`).

## Ograniczenia
Bez refresh tokenu, zmiany i resetu hasła przez użytkownika, weryfikacji e-maila, limitu prób logowania i powiadomień (e-mail) o zatwierdzeniu; tabela użytkowników na telefonie przewija się w poziomie; walidator e-maili odrzuca domeny `.local` / `.test` (w testach `test.pl`).
