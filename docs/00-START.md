# Start tutaj — projekt IMSU, wersja 3

Ten katalog zawiera pełny kontekst projektu dla każdej nowej sesji pracy (człowieka albo agenta AI).
**Przeczytaj wszystkie dokumenty w podanej kolejności, zanim cokolwiek zmienisz.**

## Sytuacja w skrócie

- Projekt zaliczeniowy z przedmiotu *Inteligentne multimedialne systemy uczące* (Informatyka UwB, studia magisterskie, 1 semestr, 2026/27), praca zespołowa (dwie osoby, każda z własnym asystentem AI).
- Cel: **multimedialny inteligentny system uczący** dla uczniów do 16 lat, wzorowany na przykładowym systemie prowadzącego. **Nauczyciel** (konto zatwierdza administrator) tworzy kursy: każda lekcja ma zarys, **tę samą treść w trzech wersjach** — V (tekst ze schematami), A (nagranie), K (zadanie z kartą PDF) — wnioski i **pulę pytań** z wyjaśnieniami; przyjmuje uczniów, którzy proszą o zapis. **Uczeń** po ankiecie VAK ma **jeden styl** i **profil procentowy V / A / K**; dostaje lekcje w formie stylu, kolejne po zaliczeniu poprzednich. Po quizie system zmienia procent formy, w której uczeń się uczył, przy porażce podpowiada „przerób w formie X”, a gdy inna forma jest lepsza i potwierdzona wynikami — **proponuje zmianę stylu** z liczbami; decyduje uczeń. Każda decyzja trafia do **dziennika**; nauczyciel widzi skuteczność form w swoim kursie.
- Wymagania pochodzą od prowadzącego (feedback ustny, przykładowy system z filmów i slajdy wykładu — `01-kontekst-i-materialy.md`).
- Kod: `backend/`, `frontend/`, `docker-compose.yml`. Wersja 3 powstała w etapie 9 (12.11) na gałęzi `feat/v3-adaptacja` (przebudowa uzgodniona przez obu autorów). Wersja 1 („StylNauki”) jest pod tagiem `v1-final`.

## Dokumenty

| Plik | Zawartość |
|---|---|
| `01-kontekst-i-materialy.md` | wymagania, feedback prowadzącego, jego przykładowy system, streszczenie slajdów wykładu i artykułów |
| `02-koncepcja.md` | jak działa system: role i dostęp, struktura kursu, model ucznia, reguły adaptacji, widoki |
| `03-architektura.md` | moduły, zależności, model domeny, frontend, infrastruktura |
| `04-decyzje.md` | dziennik decyzji: przyjęte, odroczone |
| `05-plan-etapow.md` | etapy, proces pracy nad etapem, szablon specyfikacji, **aktualny status** |
| `06-konwencje.md` | język, nazewnictwo, testy, commity, dokumentacja |
| `07-design.md` | design system (warstwy, tokeny, shadcn/ui) i ustalenia wyglądu |
| `08-praca-biezaca.md` | specyfikacja bieżącej pracy (do akceptacji, potem realizacja) |
| `moduly/` | aktualny stan każdego modułu, numerowany w kolejności powstawania: `01-identity`, `02-curriculum`, `03-content`, `04-learning-style` (reguły adaptacji R1–R8), `05-assessment`, `06-demo`, `07-authoring` (nowy moduł dostaje kolejny numer) |
| `SCENARIUSZ-POKAZU.md` | scenariusz pokazu na kontach demo (która reguła, co powiedzieć) i uruchomienie od zera |
| `RAPORT-v3.md` | raport etapu 9 (v3): co zrobione, jak sprawdzone, ograniczenia, ściąga „jak działa system” |
| `zrzuty-v3/` | zrzuty ekranów z przejścia pokazu (`frontend/e2e/demo-tour.mjs`) |
| `tex/` | dokumentacja do oddania (LaTeX, UML) |

## Podział pracy: AI przygotowuje, autor wprowadza i commituje

**Wyjątek — etap 9 (v3, D54):** kod napisał i zacommitował AI na gałęzi `feat/v3-adaptacja` (pięciu agentów równolegle, integracja i weryfikacja przez AI). Poniższe zasady obowiązują znowu od następnego etapu, chyba że autorzy ustalą inaczej.

- Asystent AI **nie zmienia plików kodu w repozytorium**. Kod przekazuje w rozmowie — w całych plikach albo jako dokładne wskazanie zmiany (plik, miejsce, przed / po). Autor sam wprowadza zmiany, żeby świadomie śledzić każdy krok.
- AI zmienia **dokumentację `docs/`** (status, praca bieżąca, opisy modułów, decyzje), gdy autor o to poprosi albo gdy wynika to z ustalonego procesu (`05-plan-etapow.md`).
- AI może **czytać** repozytorium autora poleceniami bez zapisu (`git --no-optional-locks status`, `diff`, `log`, `show`, testy), żeby sprawdzić zmiany przed commitem.
- **Testy, lint i build uruchamia autor.** Przy sprawdzaniu kroku AI tylko **porównuje pliki autora z kodem, który podało** (diff), i wskazuje różnice — nie uruchamia testów (zajmuje to dużo czasu).
- Autor uruchamia testy i **commituje**; po każdym kroku AI podaje nazwę commita po angielsku (Conventional Commits).
- Kod w rozmowie (nie w archiwach) i **w kolejności zależności**: każdy plik importuje tylko to, co już istnieje; przy większym kroku — części do sprawdzenia po kolei.
- Polecenia dla autora: Windows, `cmd`, pojedynczo (bez łączenia przez `;`).

## Zasady dla każdej sesji

1. Specyfikację etapu **akceptuje autor przed implementacją**.
2. Decyzji odroczonych w `04-decyzje.md` nie traktuj jako przesądzonych — zapytaj.
3. Po zakończonym etapie zaktualizuj status w `05-plan-etapow.md` i tutaj, a nowe ustalenia dopisz do `04-decyzje.md`.
4. Kod drugiego autora zmieniamy świadomie: zmiana cudzego pliku jest wymieniona w specyfikacji etapu.
5. Materiały źródłowe (PDF-y) leżą w projekcie claude.ai; slajdy wykładu i filmy prowadzącego nie są nigdzie zapisane — ich treść streszcza `01-kontekst-i-materialy.md`.

## Aktualny status

- **Termin: koniec listopada 2026.**
- Zrobione: etapy 0–7 (v2) i **etap 9 — v3** (12.11): jeden styl i profil procentowy, lekcje w trzech wersjach z pulą pytań, reguły adaptacji R1–R11 z dziennikiem decyzji, statystyki ucznia i panel kursu, zapisy na kurs (klasy usunięte), zatwierdzanie nauczycieli, nowe dane demo i scenariusz. Poprawki po teście Patryka (12.11, D55–D62). Testy backendu: 540. Raport: `RAPORT-v3.md`.
- Gałąź `feat/v3-adaptacja` czeka na merge do `main` (decyzja autora).
- **Następny:** etap 8 — dokumentacja do oddania i pokaz (scenariusz i LaTeX zaktualizowane w etapie 9).
