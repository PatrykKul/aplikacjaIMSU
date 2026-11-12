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

1. **Zrzuty w `docs/zrzuty-v3/` trzeba wygenerować ponownie po restarcie serwera frontendu.** Pełne przejście przeszło, ale potem uruchomiłem `npm run build` w tym samym katalogu `.next`, z którego korzystał działający `next dev` — jego procesy kompilacji padły (strony lekcji zwracają 500 do restartu). Środowisko nie pozwoliło mi zakończyć tych procesów (`node.exe` z `next dev`, także osierocony `next dev -p 3014` agenta 4 z `..\wt\a4`). Po ich zakończeniu: `npm run dev` w `frontend/`, `python -m app.demo.seed --reset-students` w `backend/`, przejście z opisu w `frontend/e2e/demo-tour.mjs`, znowu `--reset-students`.
2. **Nagrań nikt nie odsłuchał uchem.** Polskie głosy czytają słowa kodu fonetycznie („łajl”, „rejndż”) i litery matematyczne („iks”, „igrek”) — przesłuchaj 1–2 nagrania przed pokazem.
3. W blokach tekstu kod jest zwykłym akapitem (edytor ma wyłączone `code` / `codeBlock`); kod o stałej szerokości jest na PNG i w kartach PDF.
4. Merge `feat/v3-adaptacja` → `main`, push i powiadomienie Bartka (jego lokalna baza: `alembic downgrade base`, `alembic upgrade head`, seed) — Twoja decyzja.
5. Drobne ustalenia z przeglądu kodu, niepoprawione (do decyzji): pochwała R4 jest tylko w wyniku quizu, bez zdarzenia w dzienniku (specyfikacja jej tam nie wymienia); ekran szczegółów ucznia u nauczyciela składa kilka krótkich fragmentów zdań poza `explain.ts`; `null` w `PATCH /courses/{id}` nie czyści wstępu ani podsumowania, a w `PATCH /lessons/{id}` czyści zarys i wnioski; zmiana formy lekcji przy otwartym (niewysłanym) zestawie pytań nie losuje nowych pytań — wynik i tak liczy się do formy z chwili wysłania.
6. Worktree agentów (`..\wt\a1`–`a5`) i gałęzie `feat/v3-a1`–`a5` są już scalone; można je usunąć: `git worktree remove ..\wt\a1` (… `a5`) i `git branch -d feat/v3-a1` (… `a5`). Bazy `imsu_test_a1`, `imsu_test_a2`, `imsu_test_a5`, `imsu_test_int`, `imsu_a5` w kontenerze są robocze.

## Decyzje podjęte samodzielnie

- **Migracja nie przenosi danych uczenia v2** (profile, ankiety, próby, quizy bez wyjaśnień) — niezgodne z modelem v3; istniejące bloki lekcji stają się wersją V.
- **Moduł `authoring`** dla publikacji lekcji (sprawdza zarys z `curriculum`, wersje z `content` i pulę z `assessment` — w żadnym z nich nie dałoby się tego zrobić bez zależności „w górę”); zaliczenia lekcji w `curriculum`, żeby blokada nie zależała od `learning_style`.
- **Zestaw pytań zapisany na serwerze** (`quiz_draws`): odświeżenie strony nie losuje od nowa, ocena tylko wobec wylosowanych pytań.
- Przy integracji przyjęte odstępstwa agentów: `403 TEACHER_NOT_APPROVED` także przy odczycie kursów przez niezatwierdzonego nauczyciela; usunięcie ostatniej opublikowanej lekcji opublikowanego kursu → `409 LAST_PUBLISHED_LESSON`; zapis opublikowanej lekcji blokowany tylko, gdy wprowadza nowy brak; autor może zmienić decyzję o zapisie; pochwała liczy serię przez wszystkie kursy; gdy najlepsza forma jest zablokowana po odrzuceniu, propozycji nie ma (bez sięgania po drugą); otwarta propozycja powrotu wstrzymuje ocenę propozycji zmiany; zestaw z pytaniem usuniętym z puli jest losowany na nowo.
- Wykres procentów jako własny komponent SVG z tabelą danych (bez nowej biblioteki).
- `package-lock.json` zsynchronizowany (`npm ci` padało już przed etapem: brak `@emnapi/*` w locku).
- Seed przełącza wyjście na UTF-8 — w konsoli cp1250 strzałka „→” przerywała go w połowie historii ucznia (błąd znaleziony przy weryfikacji, naprawiony).
- Dokumentacja LaTeX: diagramy UML rysowane w samym LaTeX-u (TikZ, `pgf-umlcd`, `pgf-umlsd` z lokalnego MiKTeX-a) zamiast PNG.
