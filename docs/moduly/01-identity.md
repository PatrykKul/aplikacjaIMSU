# Moduł `identity` (+ `core`)

Konta, role, sesja, administracja kont. Decyzje: D3, D8, D9.

## Odpowiedzialność
- `identity`: konta użytkowników, role, rejestracja, logowanie, wylogowanie, „kim jestem”, zarządzanie kontami uczniów i nauczycieli przez administratora, wyszukiwanie uczniów dla nauczyciela, polecenie `create-admin`.
- Dla innych modułów (`service.py`): `get_users` (użytkownicy o podanych id, wg imienia), `get_active_student` (aktywny uczeń albo `None`) — z nich `curriculum` bierze dane uczniów i nauczycieli klas.
- `core`: ustawienia (`config.py`), sesja bazy (`db.py`, `DbSession`, konwencja nazw ograniczeń), format błędów (`errors.py`, `AppError`), `GET /health`, dokument TipTap (`rich_text.py`).
- Zależności dla innych modułów (`identity/dependencies.py`): `CurrentUser`, `TeacherUser`, `AdminUser`, `require_role(...)`.

## Model danych

`users`: `id`, `email` (254, unikalny, po `trim` i małymi literami), `password_hash` (bcrypt), `display_name` (80), `role` (`student` / `teacher` / `admin`, `Enum` bez typu natywnego), `is_active` (domyślnie `true`), `created_at`. Bez pól profilu — styl ucznia jest w `learning_style`.

## Sesja i bezpieczeństwo
- JWT HS256 (`sub` = id, `iat`, `exp`, 480 min) w ciasteczku `imsu_access_token`: `HttpOnly`, `SameSite=Lax`, `Path=/`. **Bez roli w tokenie** — rola i aktywność z bazy przy każdym żądaniu, więc blokada działa od razu.
- `JWT_SECRET` wymagany (≥ 32 znaki), aplikacja bez niego nie startuje.
- Hasło 8–72 bajty UTF-8 (limit bcrypt); odporność na uszkodzony hash. CSRF: `SameSite=Lax` + API tylko JSON + CORS tylko dla adresu frontendu.

## Format błędów (`core/errors.py`)
- `AppError(status, code)` → `{"code": "..."}`; walidacja 422 → `{"code": "VALIDATION_ERROR", "fields": [{"field", "type"}]}`; 500 → `{"code": "INTERNAL_ERROR"}` bez treści wyjątku; błędy frameworka → `NOT_FOUND`, `METHOD_NOT_ALLOWED`, `HTTP_ERROR`.
- Kody modułu: `EMAIL_TAKEN`, `INVALID_CREDENTIALS`, `NOT_AUTHENTICATED`, `FORBIDDEN`, `USER_NOT_FOUND`.

## API

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `POST /auth/register` | każdy | `email`, `password`, `display_name`, `role` (`student` \| `teacher`) → 201, `UserResponse`, ciasteczko | 409 `EMAIL_TAKEN`, 422 (także `role=admin`) |
| `POST /auth/login` | każdy | → `UserResponse`, ciasteczko | 401 `INVALID_CREDENTIALS` (także konto zablokowane) |
| `POST /auth/logout` | każdy | 204, usuwa ciasteczko | |
| `GET /auth/me` | zalogowany | `UserResponse` | 401 `NOT_AUTHENTICATED` |
| `GET /users?role=` | admin | uczniowie albo nauczyciele (wymagane `role`), wg e-maila | 401, 403, 422 |
| `POST /users` | admin | konto ucznia / nauczyciela z hasłem → 201 (bez ciasteczka) | 409, 422 |
| `GET /students?email=` | nauczyciel | aktywni uczniowie, których e-mail zawiera tekst (bez wielkości liter; `%` i `_` dosłownie), najwyżej 20, wg e-maila; `StudentResponse` (`id`, `display_name`, `email`) | 401, 403, 422 (tekst krótszy niż 3 znaki po przycięciu) |
| `PATCH /users/{id}` | admin | `display_name?`, `email?`, `password?`, `is_active?` (`role` → 422) | 404 `USER_NOT_FOUND` (także konto administratora), 409 |
| `GET /health` | każdy | `{"status": "ok", "database": "ok"}` | |

`UserResponse`: `id`, `email`, `display_name`, `role`, `is_active`, `created_at`. Konto administratora jest dla API administracji „nieistniejące”. CLI: `python -m app.modules.identity.cli create-admin --email … --name …` (hasło przez `getpass`).

## Frontend
- `features/auth`: `api.ts`, `hooks.ts` (`useCurrentUser` = `GET /auth/me`, klucz `["auth","me"]`; logowanie, rejestracja, wylogowanie), `roles.ts`, komponenty `LoginForm`, `RegisterForm` (kafelki ról), `AuthGuard`, `GuestGuard`, `RoleGate`, `RootRedirect`, `AuthenticatedShell` (nawigacja według roli), `UserMenu`.
- `features/users`: `/admin/users` — zakładki Nauczyciele / Uczniowie, tabela (imię, e-mail, status, data), `UserFormDialog` (dodawanie i edycja, nowe hasło opcjonalne), blokada z potwierdzeniem.
- `features/dashboard`: `/dashboard` — powitanie i karty zależne od roli.
- Trasy: `(public)/login`, `(public)/register`, `/` przekierowuje, `/dev/ui` i `/dev/shell` (plac zabaw, tylko w trybie deweloperskim).
- Nawigacja: uczeń — „Kursy”, „Moje klasy”, „Mój styl”; nauczyciel — „Moje kursy”, „Klasy”; admin — „Kursy”, „Użytkownicy”. Karty na `/dashboard` odpowiadają pozycjom menu.
- Wyszukiwanie uczniów na żywo używa `features/classes` (`useStudentSearch`) — opis w `02-curriculum.md`.

## Testy
`backend/tests/identity/`, `test_health.py`: hasła, rejestracja (role, duplikat bez względu na wielkość liter, walidacja), logowanie (zablokowane konto), `/auth/me` (brak, podrobiony, wygasły token), blokada i rola czytane z bazy, wylogowanie, administracja kont (lista według roli, tworzenie, edycja e-maila i hasła, `role` → 422, konto admina → 404), wyszukiwanie uczniów (`test_student_search.py`: fragment bez wielkości liter, kolejność, tylko aktywni uczniowie, znaki wieloznaczne dosłownie, limit 20, min. 3 znaki, tylko nauczyciel), CLI, `/health`, 500 bez treści wyjątku.

## Jak sprawdzić ręcznie
Rejestracja ucznia i nauczyciela, logowanie, wylogowanie; jako admin `/admin/users`: dodanie nauczyciela (puste pola, zajęty e-mail), edycja z nowym hasłem i logowanie nim, blokada ucznia (nie zaloguje się), odblokowanie; `/dashboard` dla każdej roli.

## Ograniczenia
Bez refresh tokenu, zmiany i resetu hasła przez użytkownika, weryfikacji e-maila, limitu prób logowania; tabela użytkowników na telefonie przewija się w poziomie; walidator e-maili odrzuca domeny `.local` / `.test` (w testach `test.pl`).
