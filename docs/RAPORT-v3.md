# Raport: IMSU v3 — przebudowa adaptacji (etap 9, 12.11.2026)

Zlecenie: `..\ZADANIE-CLAUDE-CODE-IMSU-v3.md`. Specyfikacja zaakceptowana przez Patryka 12.11 z dwiema poprawkami (progi okresu próbnego ±10, czyszczenie wyborów formy przy zmianie stylu); jest w historii gita (`git show b8832ef:docs/08-praca-biezaca.md`). Gałąź `feat/v3-adaptacja`, bez pushu i bez merge do `main`.

## Ściąga: jak działa system (do nauki przed pokazem)

**Idea.** Każda lekcja ma tę samą treść w trzech wersjach: **V** (tekst ze schematami), **A** (nagranie + krótki opis), **K** (instrukcja krok po kroku + karta PDF). Uczeń ma **jeden styl naraz** i dostaje lekcję w formie swojego stylu. System nie zgaduje: każdą reakcję wylicza reguła z liczb i zapisuje w dzienniku. Decyzję o zmianie stylu zawsze podejmuje uczeń.

**Dane ucznia.** Profil procentowy V / A / K (suma 100, każda forma 5–90) + aktywny styl + wyniki quizów z formą, w której przerabiał lekcję.

**Reguły (jeden plik czystych funkcji: `backend/app/modules/learning_style/rules.py`, 67 testów):**

| Reguła | Co robi | Przykład |
|---|---|---|
| R1 ankieta | punkty → procenty (min. 5%, suma 100, największe reszty); styl = najwyższa; remis → uczeń wybiera | A 11 / V 6 / K 3 → A 55 / V 30 / K 15 |
| R2 quiz | **tylko pierwsze podejście w danej formie w danej lekcji**: zaliczone (≥ 70%) +10, niezaliczone −10; pozostałe formy dzielą resztę proporcjonalnie | V 45 / A 40 / K 15, oblany V → V 35 / A 47 / K 18 |
| R3 potwierdzenie | forma „potwierdzona wynikami”, gdy uczeń zaliczył w niej choć jedną lekcję; inaczej „tylko z ankiety” | |
| R4 zaliczenie | odblokowanie następnej lekcji, pochwała z danymi przy serii ≥ 2 | „3 lekcje z rzędu w formie wzrokowej, średnio 87%” |
| R5 porażka | „Przerób tę lekcję w formie X”: X = potwierdzona z najwyższym procentem, a gdy brak potwierdzonych — druga forma z ankiety | „Słuchowe były drugie w Twojej ankiecie (40%), nie mamy jeszcze o nich wyników” |
| R6 propozycja | zmiana stylu na stałe tylko dla formy **potwierdzonej** z wyższym procentem niż styl; odrzucona wraca po 2 nowych wynikach | „Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%” |
| R7 okres próbny | po zmianie stylu 2 lekcje w nowej formie vs średnia 2 ostatnich w starej: ≥ +10 „pomogła”, ≤ −10 propozycja powrotu, pomiędzy „bez wyraźnej różnicy” | Marta: 40% → 90% = pomogła |
| R7a cofnięcie | zmiana stylu, zanim w okresie próbnym była jakakolwiek lekcja: powrót do starego stylu cofa zmianę (bez nowego okresu), trzeci styl dostaje nowy okres z punktem odniesienia ze stylu wyjściowego | A → V → A bez lekcji = „Zmiana cofnięta”; A → V → K porównuje z A |
| R8 podpowiedź | uczeń bez wyników w kursie widzi, która forma wypada w tym kursie najlepiej (min. 2 uczniów) — bez automatycznej zmiany | „forma słuchowa (średnio 86%, 3 uczniów)” |
| R9 losowanie | 5 pytań z puli ≥ 5; powtórka najpierw spoza ostatniego zestawu; zestaw zapisany na serwerze | pula 8 → 3 nowe + 2 stare |
| R10 kolejność | lekcja n+1 po zaliczeniu lekcji n (serwer: `403 LESSON_LOCKED`) | |
| R11 gotowość | lekcję publikuje się dopiero z zarysem, wnioskami, 3 kompletnymi wersjami i ≥ 5 pytaniami | |

Każda zmiana stylu (propozycja albo ręcznie) czyści jawne wybory formy w lekcjach jeszcze niezaliczonych — nowy styl obowiązuje wszędzie poza zaliczonymi.

**Po wysłaniu quizu (`learning_style/hooks.py`):** forma lekcji w chwili wysłania → czy to pierwsze podejście w tej formie (R2) → zapis wyniku, zmiana procentów i historia → zaliczenie: odblokowanie i pochwała / porażka: sugestia → okres próbny → propozycja → zdarzenia w dzienniku → jedna transakcja.

**Gdzie to widać:** uczeń — wynik quizu z wyjaśnieniami i „Co to zmieniło”, „Mój styl”, „Moje postępy” (wykres procentów w czasie, wyniki lekcji, dziennik); nauczyciel — „Panel kursu” (prośby o zapis, uczniowie, skuteczność form, rozkład stylów) i szczegóły ucznia z jego dziennikiem.

**Odpowiedzi na trudne pytania:** VAK i *meshing* są w badaniach krytykowane (Pashler i in., 2008) — dlatego ankieta to tylko hipoteza startowa, którą system sprawdza wynikami, a zmianę stylu proponuje dopiero przy potwierdzonej formie i zostawia decyzję uczniowi. Druga szansa w innej formie jest łatwiejsza (uczeń widział wyjaśnienia), co może zawyżać jej procent — łagodzą to: inne pytania przy powtórce (R9), liczenie tylko pierwszego podejścia w formie (R2) i wymóg potwierdzenia przed propozycją (R6).

## Co zrobione

| Obszar | Wynik |
|---|---|
| Model danych | migracja `01324f58656d_v3_adaptation`: zapisy, zaliczenia lekcji, wersje lekcji, zestawy pytań, profil procentowy z historią, wyniki, wybory formy, propozycje, okresy próbne, dziennik decyzji, zatwierdzanie nauczycieli; usunięte klasy, rozwinięcia materiałów, stare próby quizów |
| Backend | `identity` (zatwierdzanie), `curriculum` (zapisy, blokada R10, zarys / wnioski / podsumowanie, publikacja lekcji), `content` (wersje V / A / K, gotowość), nowy `authoring` (gotowość i publikacja R11), `assessment` (pula, losowanie R9, ocena wobec zestawu), `learning_style` (reguły R1–R8, okres próbny, dziennik, statystyki, postępy, panel kursu) |
| Frontend | uczeń: katalog i zapisy, strona kursu z blokadą i podpowiedzią, lekcja z wersjami i zmianą formy, quiz z wyjaśnieniami i „Co to zmieniło”, ankieta z remisem, „Mój styl”, „Moje postępy” (wykres SVG bez nowej biblioteki); nauczyciel: ekran oczekiwania na zatwierdzenie, edytor kursu, edytor lekcji z zakładkami V / A / K / pula / zarys i panelem gotowości, panel kursu, szczegóły ucznia; administrator: zatwierdzanie nauczycieli; klasy usunięte; strona startowa opisuje v3 |
| Dane demo | 3 kursy × 4 lekcje (Matematyka: funkcja liniowa, Angielski: Present Perfect, Programowanie: pętle w Pythonie), każda lekcja: zarys, wnioski, wersje V / A / K, pula 8 pytań z wyjaśnieniami; 43 zasoby (PNG, MP3 edge-tts — dialogi Zofia / Marek, karty PDF), ok. 11 MB; 13 kont w stanach do pokazu; historie zbudowane prawdziwymi serwisami |
| Dokumentacja | specyfikacja (w historii gita), `04-decyzje.md` (D41–D54, stare oznaczone), `moduly/` (01–07), `02-koncepcja.md`, `03-architektura.md`, `05-plan-etapow.md`, `06-konwencje.md` (słownik), `00-START.md`, `README.md`, `SCENARIUSZ-POKAZU.md` (nowy), `tex/` (LaTeX z UML), ten raport |

Praca: etap A (specyfikacja) → B0 (fundament integratora: modele, migracja, usunięcie klas, interfejsy) → B (pięciu agentów równolegle w osobnych worktree: backend dostęp/treść, backend silnik, frontend ucznia, frontend nauczyciela/admina, dane demo) → C (scalenie, audyt zgodności frontend ↔ backend, poprawki, weryfikacja, dokumentacja).

## Jak sprawdzone

| Sprawdzenie | Wynik |
|---|---|
| `pytest` (backend) | **473 passed** (w tym 67 testów `rules.py` — wszystkie przykłady liczbowe ze specyfikacji + właściwość „suma 100, każda 5–90” na siatce profili; ścieżki Kuby i Marty jako testy integracyjne) |
| `ruff check .`, `ruff format --check .` | czysto |
| `npm run lint`, `npm run format:check`, `npm run build` | czysto, build produkcyjny przechodzi |
| Migracja | na bazie z danymi v2: upgrade → downgrade → upgrade; od zera `downgrade base` + `upgrade head`; `alembic check` — modele zgodne z migracją |
| Seed | od zera 2 × — identyczne liczby wierszy w 13 tabelach, drugi przebieg „bez zmian”; `--reset-students` po symulowanym pokazie wraca do stanu startowego |
| Przegląd kodu przy dokumentacji | agent opisujący moduły znalazł 2 błędy logiki — statystyki kursu i podpowiedź R8 liczyły ucznia odrzuconego po fakcie; dziennik ucznia u nauczyciela gubił propozycje powstałe w innym kursie — poprawione, z testem regresji |
| Audyt zgodności | osobny agent porównał każde wywołanie API frontendu z routerami i schematami backendu: żadnego blokującego rozjazdu; 5 drobnych (teksty, nullowalność, obsługa `TEACHER_NOT_APPROVED` w trakcie sesji) — poprawione |
| Przeglądarka (Playwright) | `frontend/e2e/demo-tour.mjs` przeszedł cały scenariusz na wszystkich kontach demo (gość, Ola, Piotr, admin, Anna, Zosia, Kuba, Marta, Anna) + 4 ekrany na telefonie 390 px: **39 zrzutów, 0 błędów 500, 0 błędów JS, 0 poziomych przewinięć**; liczby na ekranach zgodne z regułami (np. Kuba: „Wzrokowe 45% → 35%”, sugestia słuchowej z ankiety 40%, „Słuchowe 47% → 57% · Lekcja 4 odblokowana”, propozycja „Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%”) |

## Co nie działa / wymaga Patryka

Stan po poprawkach z 12.11 (szczegóły w sekcji „Poprawki po teście”):

1. ~~Zrzuty do wygenerowania ponownie~~ — **zrobione**: 50 zrzutów w `docs/zrzuty-v3/` z pełnego przejścia.
2. **Nagrań nikt nie odsłuchał uchem.** Każde z 48 nagrań przeczytało cały tekst (sprawdzone znacznikami słów edge-tts), ale brzmienie słów kodu i liter („łajl”, „rejndż”, „iks”, „igrek”) trzeba ocenić uchem — przesłuchaj 2–3 nagrania.
3. ~~Kod jako zwykły akapit~~ — **zrobione**: `code` i `codeBlock` w edytorze i w lekcjach demo.
4. Merge `feat/v3-adaptacja` → `main`, push i powiadomienie Bartka (jego lokalna baza: `alembic downgrade base`, `alembic upgrade head`, seed; starsza baza z danymi v3 — `alembic upgrade head`, seed i `--refresh-demo-media`) — Twoja decyzja.
5. ~~Drobne ustalenia z przeglądu kodu~~ — **zrobione** (pochwała w dzienniku, zdania w `explain.ts`, semantyka `null`, zestaw pytań a forma lekcji).
6. ~~Worktree agentów~~ — **usunięte** (`wt/a1`–`a5`, `wt/b1`–`b3` i ich gałęzie).
7. Twoje prywatne konto ucznia (spoza kont demo) ma wyniki w Programowaniu — wlicza się do statystyk tego kursu (np. „A 87%, 1 uczeń”); reset kont demo go nie rusza.
8. Twoje prywatne konto ucznia ma też prośbę o zapis do Matematyki — widać ją w panelu kursu. Na zrzutach 22, 23 i 44 wiersz z imieniem i adresem jest zamazany (commit `f58da9f`), ale **niezamazane wersje są w lokalnym commicie `53b9c5e`** — przed pushem zdecyduj, czy przepisać historię, czy zostawić. Przed pokazem tę prośbę warto odrzucić (scenariusz, przygotowanie).

## Decyzje podjęte samodzielnie

- **Migracja nie przenosi danych uczenia v2** (profile, ankiety, próby, quizy bez wyjaśnień) — niezgodne z modelem v3; istniejące bloki lekcji stają się wersją V.
- **Moduł `authoring`** dla publikacji lekcji (sprawdza zarys z `curriculum`, wersje z `content` i pulę z `assessment` — w żadnym z nich nie dałoby się tego zrobić bez zależności „w górę”); zaliczenia lekcji w `curriculum`, żeby blokada nie zależała od `learning_style`.
- **Zestaw pytań zapisany na serwerze** (`quiz_draws`): odświeżenie strony nie losuje od nowa, ocena tylko wobec wylosowanych pytań.
- Przy integracji przyjęte odstępstwa agentów: `403 TEACHER_NOT_APPROVED` także przy odczycie kursów przez niezatwierdzonego nauczyciela; usunięcie ostatniej opublikowanej lekcji opublikowanego kursu → `409 LAST_PUBLISHED_LESSON`; zapis opublikowanej lekcji blokowany tylko, gdy wprowadza nowy brak; autor może zmienić decyzję o zapisie; pochwała liczy serię przez wszystkie kursy; gdy najlepsza forma jest zablokowana po odrzuceniu, propozycji nie ma (bez sięgania po drugą); otwarta propozycja powrotu wstrzymuje ocenę propozycji zmiany; zestaw z pytaniem usuniętym z puli jest losowany na nowo.
- Wykres procentów jako własny komponent SVG z tabelą danych (bez nowej biblioteki).
- `package-lock.json` zsynchronizowany (`npm ci` padało już przed etapem: brak `@emnapi/*` w locku).
- Seed przełącza wyjście na UTF-8 — w konsoli cp1250 strzałka „→” przerywała go w połowie historii ucznia (błąd znaleziony przy weryfikacji, naprawiony).
- Dokumentacja LaTeX: diagramy UML rysowane w samym LaTeX-u (TikZ, `pgf-umlcd`, `pgf-umlsd` z lokalnego MiKTeX-a) zamiast PNG.

## Poprawki po teście (12.11)

Zlecenie: `..\ZADANIE-CLAUDE-CODE-IMSU-v3-poprawki.md`. Decyzje D55–D62 (`04-decyzje.md`) zapisane przed kodem. Praca: trzech agentów równolegle (backend, frontend, dane demo i nagrania) w osobnych worktree, integracja i weryfikacja przez integratora.

| # | Poprawka | Wynik |
|---|---|---|
| 1 | Kursy od różnych nauczycieli | Matematyka — Anna Nowak, Angielski — Katarzyna Wróbel (`nauczyciel.angielski@imsu.pl`), Programowanie — Paweł Sikora (`nauczyciel.programowanie@imsu.pl`); seed przepina istniejące kursy przez `change_owner`, `--reset-students` też; stany uczniów i statystyki bez zmian |
| 2 | Zmiana właściciela przez administratora | `PUT /courses/{id}/owner` (tylko admin; `404 USER_NOT_FOUND`, `409 TEACHER_NOT_APPROVED`), log w tabeli `course_owner_changes` (migracja `7d2e9b4c1a35`); nowy właściciel zachowuje załączniki lekcji (pliki już użyte w lekcji są dozwolone); w `/courses` admina „Zmień właściciela” (wybór + `AlertDialog`) |
| 3 | Wejście do lekcji | `GET /courses/{id}/study-states`; przyciski „Rozpocznij”, „Kontynuuj”, „Powtórz” + najlepszy wynik, kłódka; w „Moje kursy” „Kontynuuj: Lekcja n – tytuł” |
| 4 | Przełącznik formy | spokojna linia „Forma: … (Twój styl) · Zmień formę tej lekcji”; ramka sugestii tylko po niezaliczonym quizie. **Przyczyna błędnego podpisu „Forma wybrana dla tej lekcji”:** o podpisie decydowało samo istnienie wiersza `lesson_forms`, a wiersz równy stylowi powstawał przy wyborze formy stylu z menu (utrwalone testem) i zostawał w zaliczonych lekcjach po zmianie stylu (np. Marta: lekcja 1 przerobiona w V, potem styl V). Teraz `choice` tylko, gdy wybór ≠ styl, a wybór formy stylu usuwa wiersz |
| 5 | Wersja A | 12 lekcji × (3 nagrania 30–50 s pod nagłówkami sekcji + powtórka 20–30 s), razem 48 MP3 (ok. 26 min, 6 MB); rozwijana transkrypcja pod każdym nagraniem (blok audio z plikiem i transkrypcją); tekst lektora osobno od transkrypcji (wymowa wzorów i słów kodu); **wszystkie 48 nagrań przeczytały cały tekst** (znaczniki słów edge-tts); `--refresh-demo-media` podmienia nagrania i treść w istniejącej bazie |
| 6 | Bloki kodu | `code` i `codeBlock` w edytorze (przyciski „Kod”, „Blok kodu”), czcionka o stałej szerokości u ucznia, nauczyciela i w podglądzie, przewijanie w poziomie na telefonie; lekcje Programowania z listingami, Matematyka ze wzorami w `code` |
| 7 | Podwójne nagłówki | usunięte z wstępów i podsumowań kursów demo (zarysy i wnioski ich nie miały) |
| 8 | Okres próbny przy cofnięciu (błąd Patryka) | reguła R7a `rules.trial_on_style_change`: A → V → A bez lekcji = cofnięcie (okres `cancelled`, nowy nie startuje, zdarzenie `style_change_reverted`), A → V → K = nowy okres z punktem odniesienia z A; nowy tekst `no_baseline`; testy jednostkowe i integracyjne obu ścieżek; etykieta „aktywny styl” w jednej linii |
| 9 | Drobne z raportu | zdarzenie `praise` w dzienniku; zdania szczegółów ucznia w `explain.ts`; `PATCH`: pole pominięte = bez zmian, `null` = wyczyść (wymagane → 422); zestaw pytań z formą (`quiz_draws.form`) — po zmianie formy lekcji nowy zestaw |
| 10 | Wykres i tabela „Moich postępów” | punkty tylko ankieta i policzone quizy, oś „Ankieta”, „L1 · A”…, data w podpowiedzi i tabeli; zmiany stylu jako pionowe znaczniki, **cofnięta zmiana — znacznik przekreślony z dopiskiem „cofnięta”** (wybrane zamiast pomijania: widać, że uczeń próbował, a w dzienniku jest wyjaśnienie); tabela z kolumną „Zdarzenie” i „bez zmian” w wierszach zmian stylu; test logiki wykresu (`npm test`, 8 przypadków, w tym ścieżka ankieta → 2 quizy → A → V → A) |

**Jak sprawdzone:**

| Sprawdzenie | Wynik |
|---|---|
| `pytest` | **540 passed** (było 473) |
| `ruff check .`, `ruff format --check .` | czysto |
| `npm run lint`, `npm run format:check`, `npx tsc --noEmit`, `npm test` | czysto, 8 / 8 |
| Build produkcyjny | przechodzi (w kopii roboczej z identycznym frontendem — bez ruszania `.next` działającego `next dev`) |
| Migracje | na pustej bazie: 10 kroków w górę, 10 w dół, znowu w górę; `alembic check` — zgodne z modelami |
| Seed | nowa baza 2 × — identyczne liczby wierszy; baza deweloperska: migracja, przepięcie 2 kursów, `--refresh-demo-media`, `--reset-students`, seed ponownie — identyczne liczby; stany Kuby, Marty, Zosi, uczniów 1–6 i skuteczność form w Matematyce (V 60 / A 86 / K 70) bez zmian |
| Playwright `frontend/e2e/demo-tour.mjs` | **50 zrzutów na dysku** w `docs/zrzuty-v3/`, 0 błędów 500 i JS, 0 poziomych przewinięć, wszystkie nowe kontrole spełnione: zmiana właściciela Programowania na Annę i z powrotem (sprawdzone przez API), przyciski lekcji (Zosia, Kuba), wersja A z kilkoma nagraniami i rozwiniętą transkrypcją, blok kodu (komputer i telefon), ścieżka A → V → A u Szymona (`uczen3`) z wpisem o cofnięciu, wierszem „Zmiana stylu na V (ręcznie)” i przekreślonym znacznikiem; po przejściu `--reset-students` |

**Co nie działa / uwagi:** brzmienie nagrań do odsłuchania (pkt 2 wyżej); `--refresh-demo-media` za każdym razem wgrywa 48 nagrań od nowa (stare zostają w `files`) i nadpisuje zmiany nauczyciela w treści kursów demo; kurs demo przepięty na konto spoza kont demo nie zostanie rozpoznany przez seed. W trakcie przejścia Patryk przypadkiem zatrzymał dev serwer — uruchomiłem go ponownie (`npm run dev` w `frontend/`, log w katalogu tymczasowym sesji).
