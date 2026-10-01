# Etap 6 – dopracowanie UI, dokumentacja do zaliczenia   (01.10.2026)

## Plan (krótko)
1. Przegląd wizualny aplikacji (telefon 390 px, desktop, tryb jasny i ciemny) na zrzutach ekranu i poprawki.
2. Uczniowie demo w seedzie – żeby różnicę V / A / K dało się pokazać od razu po instalacji.
3. Dokumentacja do zaliczenia, README, aktualizacja `CLAUDE.md`.

## Co zrobione (lista, z plikami)
**UI**
- `src/components/Navbar.tsx` – nawigacja także na telefonie (drugi wiersz z linkami poniżej 1024 px), czytelna ikona logo w trybie jasnym, logo prowadzi do strony startowej roli.
- Gradient nagłówków czytelny na jasnym tle (`via-sky-400 dark:via-cyan-200`) – `app/page.tsx`, `app/kursy/*`, `app/dzialy/*`, `Navbar.tsx`.
- `src/app/not-found.tsx` – strona 404 po polsku.
- `src/components/LandingCta.tsx` + `app/page.tsx` – zalogowany użytkownik widzi „Przejdź do swojego panelu" zamiast rejestracji.
- `app/kursy/KursyListClient.tsx` – nagłówek „Kursy".
- `src/app/icon.svg` – własna ikona aplikacji; usunięte nieużywane pliki startowe z `public/` i stare `favicon.ico`.

**Dane demonstracyjne**
- `backend/app/seed.py` – trzech uczniów z wypełnioną ankietą: `wzrokowiec@…` (V 12 / A 5 / K 3), `sluchowiec@…` (V 4 / A 12 / K 4), `kinestetyk@…` (V 3 / A 5 / K 12); `uczen@…` zostaje bez ankiety (pokaz wymuszenia). Test w `tests/test_auth.py`.

**Dokumentacja**
- `docs/dokumentacja.md` – cel, aktorzy, architektura, model danych, reguły (ankieta, dobór materiałów, adaptacja), bezpieczeństwo, testy, uruchomienie, **scenariusz prezentacji**, ograniczenia.
- `README.md` – uruchomienie, zmienne, komplet kont testowych, mapa widoków wg roli.
- `CLAUDE.md` – aktualna sekcja „Stos i struktura", etapy 0–6 oznaczone jako zrobione.

## Decyzje i dlaczego
- **Przegląd UI na zrzutach ekranu** (przeglądarka headless) zamiast zgadywania – poprawiłem tylko to, co faktycznie było widać: brak nawigacji na telefonie, słabo czytelny gradient i ikona w trybie jasnym, angielska strona 404.
- **Osobne konta demo na każdy styl** – na prezentacji nie trzeba trzy razy wypełniać ankiety.
- Ostrzeżenia lint o `<img>` zostają: obrazy pochodzą z uploadu / plików SVG i `next/image` niczego tu nie daje.

## Weryfikacja (komendy + wynik)
- `pytest` → 224 passed
- `alembic check` → brak różnic między modelami a migracjami
- `npm run lint` → 0 błędów (3 ostrzeżenia `<img>`)
- `npm run build` → OK
- Smoke w przeglądarce headless – wszystkie scenariusze etapów 1–5 (logowanie i role, wymuszona ankieta, personalizacja V/A/K, adaptacja, panele): OK, bez błędów w konsoli.
- Zrzuty ekranu 11 widoków w dwóch wariantach (telefon jasny, desktop ciemny) obejrzane po poprawkach.
- Grep na nazwy starego projektu w kodzie, README i UI → brak (jedyne trafienie: `PROMPT-AUTONOMICZNY.md`, plik autora z poleceniem).

## Jak sprawdzić ręcznie (kroki dla człowieka)
Scenariusz krok po kroku: `docs/dokumentacja.md`, rozdział 9 „Scenariusz prezentacji".
Szybko: `python -m app.seed`, potem zaloguj się kolejno jako `wzrokowiec@stylnauki.pl`, `sluchowiec@stylnauki.pl`, `kinestetyk@stylnauki.pl` (hasło `Uczen123!`) i otwórz ten sam temat.

## Znane problemy / TODO
- `TODO(prowadzący)`: forma oddania i wymagany zakres dokumentacji (PYTANIA.md).
- Brak testów jednostkowych frontendu; scenariusze przeglądarkowe uruchamiałem skryptem spoza repo.
- Lektor (Web Speech API) zależy od głosów w systemie.
- Tabele paneli bez filtrowania i stronicowania.

## Propozycje (poza zakresem)
- Etap 7 (LLM): pytania otwarte w ankiecie, „Wyjaśnij inaczej" – z zachowaniem regułowego rdzenia.
- Testy E2E (Playwright) w repo i w CI.
- Klasy / zapisy na kurs; statystyki trudności tematów dla nauczyciela.
- Eksport dokumentacji do PDF, jeśli prowadzący tego wymaga.

## Commity (hash + opis)
- 6ed069f Seed: uczniowie demo (po jednym na styl V/A/K) + test
- 709e834 Frontend: dopracowanie UI – nawigacja mobilna, czytelny gradient, strona 404, CTA dla zalogowanych, ikona aplikacji
- 0368d7f Dokumentacja do zaliczenia, README i CLAUDE.md
