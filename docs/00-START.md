# Start tutaj — projekt IMSU, wersja 2

Ten katalog zawiera pełny kontekst projektu dla każdej nowej sesji pracy (człowieka albo agenta AI).
**Przeczytaj wszystkie dokumenty w podanej kolejności, zanim cokolwiek zmienisz.**

## Sytuacja w skrócie

- Projekt zaliczeniowy z przedmiotu *Inteligentne multimedialne systemy uczące* (Informatyka UwB, studia magisterskie, 1 semestr, 2026/27), praca zespołowa (dwie osoby, każda z własnym asystentem AI).
- Cel: **multimedialny inteligentny system uczący** dla uczniów do 16 lat, wzorowany na przykładowym systemie prowadzącego. **Nauczyciel** tworzy w edytorze kursy: lekcje z blokami tekstu i **załącznikami oznaczonymi V / A / K** oraz quiz lekcji. **Uczeń** po ankiecie VAK ma **styl** i **wagi V / A / K**; system podaje lekcję według stylu (materiały innych stylów zwinięte), po quizie zmienia wagi i **proponuje zmianę stylu** z uzasadnieniem, a decyduje uczeń.
- Wymagania pochodzą od prowadzącego (feedback ustny, przykładowy system z filmów i slajdy wykładu — `01-kontekst-i-materialy.md`).
- Kod: `backend/`, `frontend/`, `docker-compose.yml` na gałęzi `main` (wersja 2, budowana od nowa). Poprzednia wersja („StylNauki”) jest pod tagiem `v1-final`; przejęliśmy z niej logikę ankiety, personalizacji i adaptacji (`moduly/04-learning-style.md`).

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
| `moduly/` | aktualny stan każdego modułu, numerowany w kolejności powstawania: `01-identity`, `02-curriculum`, `03-content`, `04-learning-style`, `05-assessment`, `06-demo` (nowy moduł dostaje kolejny numer) |
| `SCENARIUSZ-POKAZU.md` | scenariusz pokazu na kontach demo i uruchomienie od zera |

## Podział pracy: AI przygotowuje, autor wprowadza i commituje

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

- **Termin: koniec listopada 2026.** Pokaz roboczy: 12.11.2026.
- Zrobione: etap 0 (szkielet), 1 (konta i role), 2 (administracja kont), 3 (kursy i edytor lekcji), 4 (styl uczenia się i quizy — kolega), 5 (poprawki stylu i quizów: zwijanie materiałów, styl efektywny lekcji, kontrolki shadcn), 6 (klasy i dostęp do kursów). Testy backendu: 349.
- **Następny:** etap 7 — wygląd (specyfikacja do przygotowania w `08-praca-biezaca.md`).
- **Dalej:** etap 8 — dokumentacja i pokaz.
