# Dane demo (`backend/app/demo`)

Konta w stanach do pokazu, trzy kursy po 4 lekcje z kompletnymi wersjami V / A / K i pulami pytań, historie uczniów zbudowane prawdziwymi serwisami. Decyzje: D14 (wyjątek), D22, D30, D53, D55 (nauczyciele kursów), D58 (nagrania wersji A), D59 (kod w treści). Scenariusz pokazu: `SCENARIUSZ-POKAZU.md`.

## Uruchomienie
Z katalogu `backend/` (po `alembic upgrade head` — pytania ankiety wstawia migracja; bez nich seed kończy się komunikatem):

```
python -m app.demo.seed                        # dokłada brakujące; drugie uruchomienie: „bez zmian”
python -m app.demo.seed --reset-students       # stan startowy wszystkich kont demo (po pokazie)
python -m app.demo.seed --refresh-demo-media   # wersja A od nowa: aktualne nagrania i transkrypcje
```

- **Idempotentny**: konto rozpoznawane po e-mailu, kurs po tytule wśród niezarchiwizowanych kursów kont nauczycieli demo (Anna Nowak, Katarzyna Wróbel, Paweł Sikora, Piotr Zieliński — admin mógł przepiąć kurs na pokazie), historia ucznia budowana tylko, gdy uczeń nie ma profilu. Treści kursów nie nadpisuje — zmiany nauczyciela w kursach demo zostają. Drugie uruchomienie nie zmienia liczby wierszy w żadnej tabeli (test).
- **Właściciele kursów (D55)**: nowa baza — każdy kurs tworzy i pliki wgrywa jego nauczyciel (`OWNERS` w `seed.py`), zapisy uczniów przyjmuje nauczyciel kursu. Istniejąca baza — kurs demo z innym właścicielem seed przepina przez `curriculum.change_owner` jako `admin.demo` (wpis w `course_owner_changes`, wypisuje „zmieniono autora kursu …: X → Y”); przy każdym uruchomieniu, więc też przy `--reset-students`.
- Wszystko przez serwisy modułów (te same walidacje co w aplikacji): `curriculum` (kursy, lekcje, zarys, wnioski, zapisy), `content` (pliki, wersje), `assessment` (pula, losowanie, wysłanie odpowiedzi), `authoring` (publikacja po sprawdzeniu gotowości R11), `learning_style` (ankieta, wybór formy, przyjęcie propozycji). Jedyny bezpośredni SQL przesuwa czasy ucznia o dzień wstecz po każdym kroku historii (wykres i dziennik mają oś czasu, kolejność zostaje).
- Losowanie pytań z ziarnem (`SEED = 2026`, `assessment.rng`) — te same historie przy każdym uruchomieniu; `take_quiz` odpowiada poprawnie na k z 5 pytań, żeby uzyskać zadany wynik. W Matematyce (`DIFFICULTY` w `seed.py`: kolejność pytań puli od najtrudniejszego i „pułapka” — pytanie trudne z indeksem typowej złej odpowiedzi) złe odpowiedzi dostają najtrudniejsze z wylosowanych pytań, a pytanie trudne zawsze tę samą złą odpowiedź; w innych kursach źle jest ostatnie 5 − k pytań zestawu. Zła odpowiedź poza pułapką: pierwsza zła w pytaniu. Nowi uczniowie są na końcu `STUDENTS`, więc zestawy pytań wcześniejszych kont się nie zmieniają (to samo ziarno).
- `--reset-students`: właściciele kursów demo przywróceni (jak wyżej); `nauczyciel.nowy` znów `pending`; u każdego ucznia demo usuwa wyniki, zestawy pytań, historię procentów, dziennik, propozycje, okresy próbne, wybory formy, zaliczenia, zapisy, profil i ankietę; potem odtwarza historie z tabeli niżej. Kursy, pliki i konta zostają.
- `--refresh-demo-media`: w istniejących kursach (jako nauczyciel kursu) zapisuje od nowa treść z `courses.py` — wstęp i podsumowanie kursu, zarys i wnioski lekcji, wersje V / A / K. Wersja A dostaje ponownie wgrane nagrania MP3 (opis, 3 nagrania z transkrypcjami, powtórka), V i K zostają przy swoich zapisanych obrazach i PDF (D56: pliki już użyte w lekcji). Stare pliki zostają w `uploads/` i `files`. Tak baza sprzed poprawek 12.11 dostaje nowe nagrania, kod w `codeBlock` / `code` i podsumowania bez własnego nagłówka.
- `main()` przełącza `stdout` na UTF-8 (`errors="replace"`), więc polskie litery i strzałki nie przerywają seeda w konsoli cp1250 ani w potoku. Na końcu wypisuje stan kont i skuteczność form w każdym kursie.
- Hasło wszystkich kont `Demo123!` jest w kodzie — seed nigdy na serwerze produkcyjnym (D30).

## Konta i stany startowe

| Konto | Rola | Stan startowy (z `seed.py`) | Na pokazie |
|---|---|---|---|
| `admin.demo@imsu.pl` (Adam Admin) | admin | — | zatwierdza nauczyciela `pending`, zmienia właściciela kursu |
| `nauczyciel.demo@imsu.pl` (Anna Nowak) | nauczyciel, zatwierdzony | autorka Matematyki, prośba Zosi w Matematyce | edytor lekcji (3 wersje, pula, gotowość), przyjęcie prośby, panel kursu, szczegóły ucznia |
| `nauczyciel.angielski@imsu.pl` (Katarzyna Wróbel) | nauczyciel, zatwierdzony | autorka Angielskiego (Antoni, Szymon) | panel kursu z innym autorem |
| `nauczyciel.programowanie@imsu.pl` (Paweł Sikora) | nauczyciel, zatwierdzony | autor Programowania (Marta, Filip) | szczegóły Marty (okres próbny, pochwała) |
| `nauczyciel.nowy@imsu.pl` (Piotr Zieliński) | nauczyciel `pending` | — | ekran „Konto czeka na zatwierdzenie” |
| `uczen.nowy@imsu.pl` (Ola Kowalska) | uczeń | bez ankiety | wymuszenie ankiety, procenty, katalog, prośba o zapis |
| `uczen.zapis@imsu.pl` (Zosia Mazur) | uczeń | ankieta V 6 / A 10 / K 4 → **V 30 / A 50 / K 20**, styl A; prośba o zapis do Matematyki (`pending`) | nauczycielka przyjmuje → podpowiedź „forma słuchowa (średnio 86%, 3 uczniów)” (R8) |
| `uczen.demo@imsu.pl` (Kuba Wiśniewski) | uczeń | ankieta V 9 / A 8 / K 3 → 45 / 40 / 15, styl V; Matematyka: L1 w V 80% → V 55 / A 33 / K 12; L2 w V 40% → 45 / 40 / 15 (sugestia A z ankiety — zignorowana); L2 w V 80% (niepoliczone, zaliczone, odblokowuje L3) — **„tuż przed sugestią”**: L1–L2 zaliczone, L3 dostępna, L4 zablokowana | L3 w V 40% → V 35 / A 47 / K 18 + „Przerób w formie słuchowej” (A druga w ankiecie, 40%) → L3 w A 80% → V 28 / A 57 / K 15 → propozycja V → A („Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%”) → przyjęcie → okres próbny (przed: 40%) |
| `uczen.zmiana@imsu.pl` (Marta Lewandowska) | uczeń | ankieta V 7 / A 3 / K 10 → V 35 / A 15 / K 50, styl K; Programowanie: L1 w K 40% (sugestia V) → wybór formy V → L1 w V 80% → propozycja K → V przyjęta (okres próbny, przed 40%) → L2 w V 100%, L3 w V 80% → **„Zmiana pomogła: średnia 40% → 90%”**, pochwała „3 lekcje z rzędu zaliczone w formie wzrokowej, średnio 87%”; procenty V 72 / A 9 / K 19 | dziennik i wykres w „Moich postępach”, szczegóły ucznia u nauczycielki |
| `uczen1@imsu.pl` (Antoni Wójcik) | uczeń | V 10 / A 5 / K 5 → styl V; Matematyka L1 V 80%, L2 V 40%; Angielski L1 V 100% → V 60 / A 20 / K 20 | statystyki kursu |
| `uczen2@imsu.pl` (Julia Kamińska) | uczeń | V 9 / A 8 / K 3 → styl V; Matematyka L1 V 60%, wybór A, L1 A 80% → V 28 / A 57 / K 15, **otwarta propozycja V → A** | otwarta propozycja w tabeli panelu kursu |
| `uczen3@imsu.pl` (Szymon Wojciechowski) | uczeń | V 5 / A 11 / K 4 → styl A; Matematyka L1–L3 w A: 80, 100, 80%; Angielski L1 A 80% → V 5 / A 90 / K 5 | |
| `uczen4@imsu.pl` (Lena Dąbrowska) | uczeń | V 4 / A 12 / K 4 → styl A; Matematyka L1–L3 w A: 80, 80, 100% → V 5 / A 90 / K 5 | |
| `uczen5@imsu.pl` (Filip Kozłowski) | uczeń | V 5 / A 4 / K 11 → styl K; Matematyka L1 K 80%, L2 K 60%; Programowanie L1 K 60% → V 29 / A 26 / K 45 | |
| `uczen6@imsu.pl` (Maja Jankowska) | uczeń | V 6 / A 3 / K 11 → styl K; Matematyka L1 K 80%, L2 K 60% → V 30 / A 15 / K 55 | |
| `uczen7@imsu.pl` (Natalia Zając) | uczeń | V 6 / A 11 / K 3 → styl A; Matematyka w A: L1 100, L2 60 → 80 (powtórka), L3 100, L4 80 → V 16 / A 75 / K 9; 4/4 | statystyki kursu (druga grupa, tylko Matematyka) |
| `uczen8@imsu.pl` (Mikołaj Król) | uczeń | V 11 / A 5 / K 4 → styl V; L1 V 80, L2 V 80, L3 V 40 → wybór A (sugestia) → L3 A 80, L4 V 80 → V 67 / A 23 / K 10; 4/4 | |
| `uczen9@imsu.pl` (Hanna Pawlak) | uczeń | V 10 / A 7 / K 3 → styl V; L1 V 80, L2 V 60 → A 80, L3 V 40 → A 100, przyjęta propozycja V → A (okres próbny, przed 50%), L4 A 60 → 100 (powtórka) → V 32 / A 53 / K 15; 4/4, **okres próbny trwa** (1 z 2 lekcji) | |
| `uczen10@imsu.pl` (Wiktor Michalski) | uczeń | V 4 / A 5 / K 11 → styl K; L1 K 80, L2 K 80, L3 K 60 → A 80, L4 K 60 → A 80 → V 13 / A 47 / K 40; 4/4, **otwarta propozycja K → A** | |
| `uczen11@imsu.pl` (Amelia Grabowska) | uczeń | V 12 / A 4 / K 4 → styl V; L1 V 100, L2 V 100, L3 V 60 → 80 (powtórka w V), L4 V 60 → V 60 / A 20 / K 20; 3/4 | |
| `uczen12@imsu.pl` (Igor Nowicki) | uczeń | V 9 / A 6 / K 5 → styl V; L1 V 80, L2 V 40 → A 60 (sugestia) → K 40 (wybór własny) → V 59 / A 24 / K 17; 1/4, **3 policzone porażki z rzędu** (R12: 40, 60, 40) | „wymaga uwagi” w tabeli uczniów |

Skuteczność form w Matematyce (policzone wyniki): **V 67%** (18 wyników, 20 podejść, 7 uczniów), **A 82%** (18, 20, 8), **K 67%** (9, 9, 4); przyjętych uczniów 13 (Kuba i uczniowie 1–12), prośba 1 (Zosia), rozkład stylów V 6 · A 4 · K 3. Podpowiedź z kursu dla Zosi (R8): A, średnio 82%, 8 uczniów. Pierwsza grupa (Kuba, uczniowie 1–6) sama dawała V 60 / A 86 / K 70 — jej konta i liczby się nie zmieniły. Angielski: Antoni (V) i Szymon (A); Programowanie: Marta i Filip.

Statystyki etapu 10 w Matematyce (stan startowy; definicje i progi: `08-praca-biezaca.md`):

| Lekcja | Zaczęło | Zaliczyło | Zaliczalność | Średnia policzonych (n) | Podejść do zaliczenia | V | A | K |
|---|---|---|---|---|---|---|---|---|
| 1. Wzór i wykres | 13 | 13 | 100% | 81% (14) | 1,1 | 80% · 7 | 85% · 4 | 80% · 3 |
| 2. Współczynnik kierunkowy a | 12 | 8 | **67% — najtrudniejsza** | 65% (15) | 1,4 | 60% · 6 | 76% · 5 | 60% · 4 |
| 3. Miejsce zerowe | 7 | 7 | 100% | 74% (10) | 1,6 | **47% · 3** | **90% · 6** | — · 1 |
| 4. Funkcja liniowa w zadaniach | 5 | 4 | 80% | 70% (6) | 1,5 | 70% · 2 | 73% · 3 | — · 1 |

- Wniosek macierzy (różnica ≥ 20 pkt) tylko w lekcji 3: słuchowa 90% (6) wobec wzrokowej 47% (3). Po pokazie Kuby (L3: V 40, A 80): V 45% · 4, A 89% · 7.
- Pytanie trudne (pułapka) i łatwe w każdej lekcji (wylosowane / poprawnie / najczęstsza zła odpowiedź): L1 q8 „y = 4x − 1 ma wartość 7” 8 / 12% / „x = 27” 88%, łatwe np. q2 „wykres = prosta” 9 / 100%; L2 q4 „najbardziej stroma” 10 / 20% / „y = 3x” 80% (także q6 38%), łatwe q3 12 / 100%; L3 q4 „przecięcie z osią x” 6 / 17% / „(0, −4)” 83%, łatwe q1 8 / 100%; L4 q1 „wzór taksówki” 6 / 0% / „y = 8x + 3” 100%, łatwe q4 5 / 100% (reszta pytań L4 ma < 5 losowań — „za mało danych”).
- Seria porażek (R12): Igor Nowicki (40, 60, 40).

## Kursy (wszystkie opublikowane)

| Kod | Kurs | Nauczyciel | Lekcje |
|---|---|---|---|
| `m` | Matematyka: funkcja liniowa | Anna Nowak | 1. Wzór i wykres · 2. Współczynnik kierunkowy a · 3. Miejsce zerowe · 4. Funkcja liniowa w zadaniach |
| `e` | Angielski: Present Perfect | Katarzyna Wróbel | 1. Budowa zdania · 2. ever, never, already, yet · 3. for i since · 4. Present Perfect czy Past Simple? |
| `p` | Programowanie: pętle w Pythonie | Paweł Sikora | 1. Pętla for · 2. range() · 3. Pętla while · 4. break i continue |

Każdy kurs: opis, wstęp, „Podsumowanie i wnioski” (bez własnego nagłówka w treści — tytuły sekcji daje strona kursu). Każda lekcja (spełnia R11 — sprawdza test seeda): zarys, wnioski; **V** — tekst + 1–2 schematy / wykresy PNG; **A** — krótki opis i **4 nagrania MP3 (D58)**: 3 części po 30–50 s, zatytułowane jak sekcje wersji V (np. „Jak zapisać pętlę for”, „Wcięcie decyduje”, „Przykład: suma liczb z listy”), i „Powtórka” 20–30 s; dialog nauczycielki (Zofia) i Marka albo objaśnienie, przykłady angielskie głosami en-GB; każde nagranie ma transkrypcję w polu `transcript` bloku audio (zapis pisany: wzory, kod, cyfry; nazwy mówców w dialogu); **K** — instrukcja krok po kroku + karta zadania PDF (A4, odpowiedzi na ostatniej stronie); **pula 8 pytań** z wyjaśnieniami. Kod w Programowaniu jako `codeBlock` (listingi) i znacznik `code` (w zdaniach, listach, tabeli `range`); w Matematyce wzory główne jako `code`, a rachunek miejsca zerowego jako blok (D59).

## Pliki
- `courses.py` — treść kursów (dokumenty TipTap budowane funkcjami `heading`, `paragraph`, `bullets`, `ordered`, `table`, `code_block`; w zwykłych napisach fragment w `` `odwrotnych apostrofach` `` dostaje znacznik `code`, `mono(...)` to samo jawnie), bloki wersji (`Text`, `Image`, `Audio`, `Pdf`), pytania. Nagranie: `Audio.script` to tury `say(głos, ...)`, a tura to linie (`Line`) czytane po kolei; angielskie przykłady `en(...)` / `en2(...)`. W linii fragment `{zapis|wymowa}` trafia do transkrypcji jako zapis, a lektor czyta wymowę, np. `{y = 2x + 1|igrek równa się dwa iks plus jeden}`, `{while|łajl}`, `{range(1, 11)|rejndż od jednego do jedenastu}`; `Audio.transcript()` składa transkrypcję. `seed.py` — konta, właściciele kursów (`OWNERS`), kursy, historie (`STUDENTS`: kroki `Survey`, `Enrol`, `Quiz`, `ChooseForm`, `AcceptProposal`), reset, odświeżenie treści.
- `assets/` — 79 plików w repozytorium (19 PNG, 48 MP3, 12 PDF; ok. 10,5 MB, z tego nagrania ok. 6 MB, razem ok. 26 min).
- Generatory (jednorazowe, wynik jest w repozytorium, seed ich nie potrzebuje) — w **osobnym venv narzędziowym**, bo pakiety są spoza `requirements.txt`:
  - `generate_assets.py` — obrazy PNG wersji V i karty PDF wersji K; Pillow + fonty Windows (Segoe UI, Consolas — polskie litery);
  - `generate_audio.py` — nagrania MP3 wersji A; `edge-tts` (wymaga internetu) + `imageio-ffmpeg` (przycinanie ciszy, łączenie, MP3 mono 24 kHz, 32 kb/s); głosy `pl-PL-ZofiaNeural`, `pl-PL-MarekNeural`, `en-GB-SoniaNeural`, `en-GB-RyanNeural`. **Kontrola kompletności**: dla każdej linii edge-tts zwraca znaczniki przeczytanych słów (`WordBoundary`), a generator porównuje je ze słowami tekstu dla lektora — różnica to błąd; sprawdza też długości z D58 (części 30–50 s, powtórka 20–30 s). Wypisuje wiersz na plik (`ok m1_a1_wzor.mp3 37.8 s 147 KB fragmenty 5 słowa 87/87`) i kod wyjścia 1 przy problemie. Linie i ich znaczniki zapisywane w `%TEMP%/imsu-tts-cache` (zmiana jednej kwestii nagrywa tylko ją); argumenty zawężają do plików (`… generate_audio m1 e2`); pełne uruchomienie usuwa z `assets/` pliki MP3, których nie używa żadne nagranie.
  - Uruchomienie z `backend/`: `<tools-venv>\Scripts\python -m app.demo.generate_assets` / `generate_audio`, potem `--refresh-demo-media` w istniejącej bazie.

## Testy
`backend/tests/demo/test_seed.py` (seed raz na moduł, pliki do katalogu tymczasowego, na końcu wycofanie transakcji): konta (admin, trzech nauczycieli zatwierdzonych, nauczyciel `pending`, uczeń bez ankiety, uczniowie 1–12); właściciele kursów (nowa baza: bez wpisów w `course_owner_changes`, pliki wgrane przez nauczyciela kursu; panele Angielskiego i Programowania u ich nauczycieli); wersje A (3–4 nagrania z plikiem i transkrypcją, ostatnie „Powtórka”, transkrypcja pisana — `y = ax + b`, `while licznik <= 5:` — a lektor czyta „łajl”); `codeBlock` i `code` w wersjach V Programowania, `code` w Matematyce; brak nagłówków we wstępie, podsumowaniu, zarysach i wnioskach; procenty uczniów 1–6; kursy opublikowane, lekcje w kolejności z `courses.py`, każda bez braków R11 i z pulą 8 pytań; Zosia (A, 30 / 50 / 20, prośba `pending` w Matematyce); Kuba „tuż przed sugestią” (45 / 40 / 15, stany lekcji, ostatnia sugestia A z ankiety, bez propozycji); Marta (okres próbny K → V `helped` 40 → 90, pochwała V × 3 średnio 87, jeden wybór formy); historia rozłożona na dni w kolejności; otwarta propozycja Julii; druga grupa (procenty uczniów 7–12, okres próbny Hanny V → A przed 50%, propozycja Wiktora K → A, trzy policzone porażki Igora); skuteczność form w Matematyce (V 67, A 82, K 67; uczniowie 7 / 8 / 4; 13 przyjętych) i podpowiedź A 82% z 8 uczniami dla Zosi; statystyki lekcji liczone z `quiz_results` (≥ 10 uczniów z historią, w każdej lekcji ≥ 3, zaliczalność 100 / 67 / 100 / 80, różnica form ≥ 20 pkt tylko w lekcji 3: A 90 wobec V 47); pytania z `quiz_draws` (w każdej lekcji pułapka z `DIFFICULTY` wylosowana ≥ 5 razy, < 40% poprawnych, jedna zła odpowiedź u większości, i pytanie > 90% z ≥ 5 losowaniami); drugie uruchomienie bez zmian w liczbach wierszy; pokaz Kuby (35 / 47 / 18 + sugestia A → 28 / 57 / 15 + propozycja z dowodem 3 lekcje / 53 i 1 lekcja / 80); `--reset-students` po pokazie (w tym przepięciu Angielskiego na Piotra Zielińskiego) przywraca właścicieli, liczby wierszy (poza dwoma wpisami w `course_owner_changes`), `pending` nauczyciela, procenty Kuby i prośbę Zosi; `--refresh-demo-media` zapisuje od nowa podsumowanie (podmienione na wersję z nagłówkiem), daje wersji A nowe pliki z transkrypcjami, zostawia pliki V i stare pliki w `files`.

## Jak sprawdzić ręcznie
Nowa baza: `alembic upgrade head` → `python -m app.demo.seed` (wypisuje „utworzono …” i stan kont) → drugie uruchomienie (same „bez zmian”). Baza sprzed poprawek 12.11: `alembic upgrade head` → `python -m app.demo.seed` (dwa wiersze „zmieniono autora kursu …”, stany uczniów bez zmian) → `python -m app.demo.seed --refresh-demo-media` (nowe nagrania, kod, podsumowania bez nagłówka). Po pokazie: `python -m app.demo.seed --reset-students`. Przebieg pokazu i zrzuty: `SCENARIUSZ-POKAZU.md`; przejście automatyczne po wszystkich kontach — `frontend/e2e/demo-tour.mjs` (Playwright spoza zależności projektu, backend :8001 i frontend :3001 z danymi po resecie; zrzuty do `docs/zrzuty-v3/`; po przejściu znów `--reset-students`).

## Ograniczenia
- Seed przerwany w trakcie tworzenia kursu zostawia kurs uznawany za istniejący — trzeba go zarchiwizować i uruchomić seed ponownie; uczeń z profilem, którego historia urwała się w połowie, nie zostanie uzupełniony (pomaga `--reset-students`).
- `--reset-students` nie cofa zmian w kursach (np. lekcji dodanej na pokazie) ani nie usuwa kont zarejestrowanych na pokazie.
- Kurs demo przepięty na pokazie na konto spoza kont demo (np. nauczyciela zarejestrowanego na pokazie) nie zostanie znaleziony — seed utworzy drugi kurs o tym samym tytule; trzeba go wcześniej przepiąć z powrotem albo zarchiwizować.
- `--refresh-demo-media` przy każdym uruchomieniu wgrywa 48 nagrań od nowa (stare zostają w `files` i `uploads/`), a zmiany nauczyciela w treści kursów demo nadpisuje.
- Wymowę lektora sprawdzają tylko znaczniki słów (czy przeczytano wszystkie słowa), nie brzmienie; zapis fonetyczny (`łajl`, `rejndż`, `brejk`, `kontinju`, `iks`, `igrek`) dobrany jak w poprzednich nagraniach.
- Generatory zależą od Windows (fonty) i internetu (edge-tts).
- Losowania nie da się wymusić: liczba losowań pytań trudnych i łatwych wynika z ziarna i kolejności historii. Zmiana historii, kolejności `STUDENTS` albo puli Matematyki może przesunąć te liczby — test `test_math_questions_hard_and_easy` to wychwyci, wtedy trzeba poprawić `DIFFICULTY` albo historie.
