# Scenariusz pokazu IMSU v3 (12–15 minut)

Aplikacja: http://localhost:3001 (backend: http://localhost:8001). Hasło wszystkich kont demo: `Demo123!`.
Reguły R1–R11 i R7a opisuje `docs/moduly/04-learning-style.md` (decyzje w `docs/04-decyzje.md`), a ich kod jest w `backend/app/modules/learning_style/rules.py`. Liczby w tym scenariuszu pochodzą z seeda; sprawdza je test `backend/tests/demo/test_seed.py`. Zrzuty każdego kroku: `docs/zrzuty-v3/` (przejście `frontend/e2e/demo-tour.mjs`, numery zrzutów podane przy krokach).

| Konto | Kto | Stan startowy (po `--reset-students`) |
|---|---|---|
| `uczen.nowy@imsu.pl` | Ola Kowalska | bez ankiety |
| `nauczyciel.nowy@imsu.pl` | Piotr Zieliński | nauczyciel, konto czeka na zatwierdzenie |
| `admin.demo@imsu.pl` | Adam Admin | administrator |
| `nauczyciel.demo@imsu.pl` | Anna Nowak | autorka Matematyki (4 lekcje): 7 uczniów i 1 prośba o zapis |
| `nauczyciel.angielski@imsu.pl` | Katarzyna Wróbel | autorka Angielskiego (4 lekcje): Antoni, Szymon |
| `nauczyciel.programowanie@imsu.pl` | Paweł Sikora | autor Programowania (4 lekcje): Marta, Filip |
| `uczen.zapis@imsu.pl` | Zosia Mazur | ankieta A 50 / V 30 / K 20, styl słuchowy; prośba o zapis do Matematyki |
| `uczen.demo@imsu.pl` | Kuba Wiśniewski | styl wzrokowy, V 45 / A 40 / K 15; Matematyka 2/4, lekcja 3 dostępna („tuż przed sugestią”) |
| `uczen.zmiana@imsu.pl` | Marta Lewandowska | styl wzrokowy po zmianie z kinestetycznego; okres próbny: „Zmiana pomogła: średnia 40% → 90%” |
| `uczen1…6@imsu.pl` | klasa (Antoni, Julia, Szymon, Lena, Filip, Maja) | wyniki w Matematyce; Julia ma otwartą propozycję zmiany V → A; Szymon (`uczen3`): styl słuchowy, V 5 / A 90 / K 5 |

## Przygotowanie (10 minut przed pokazem)

1. Uruchom bazę i aplikację (sekcja „Uruchomienie od zera” na końcu, jeśli to nowa maszyna):
   ```powershell
   docker compose up -d                                   # w katalogu aplikacja\
   cd backend
   .\venv\Scripts\python.exe -m alembic upgrade head      # baza sprzed 12.11: tabela course_owner_changes, quiz_draws.form
   .\venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
   # drugi terminal: cd frontend; npm run dev             # http://localhost:3001
   ```
2. Przywróć wszystkie konta demo do stanu startowego (kursy zostają, właściciele kursów wracają do Anny, Katarzyny i Pawła):
   ```powershell
   cd backend
   .\venv\Scripts\python.exe -m app.demo.seed --reset-students
   ```
   Na końcu wypisuje się „Stan kont” i „Skuteczność form”. Sprawdź dwie linie:
   - `uczen.demo@imsu.pl: styl V, V 45 / A 40 / K 15, Matematyka 2/4`
   - `Matematyka: funkcja liniowa (Anna Nowak): V 60% (3 ucz.) · A 86% (3 ucz.) · K 70% (2 ucz.)`

   Baza sprzed poprawek 12.11 (jedno nagranie w wersji A, bez bloków kodu): raz `.\venv\Scripts\python.exe -m app.demo.seed --refresh-demo-media` — wgrywa od nowa wersje A (3 nagrania + powtórka z transkrypcjami), kod w lekcjach i podsumowania kursów.
3. Konta spoza demo (np. własne konto testowe) `--reset-students` nie czyści. Jeśli takie konto prosiło o zapis do Matematyki, Anna zobaczy w panelu 2 prośby zamiast 1 — odrzuć tę prośbę przed pokazem.
4. Otwórz dwie sesje przeglądarki: zwykłe okno (uczniowie) i okno incognito (nauczyciele i administrator). Dzięki temu nie trzeba się ciągle wylogowywać.
5. Sprawdź dźwięk: `nauczyciel.demo` → Matematyka → lekcja 1 → „Podgląd” → wersja słuchowa → odtwórz kilka sekund pierwszego nagrania. Nagrania to gotowe pliki MP3 (głosy neuronowe), więc działają bez internetu.
6. Miej pod ręką klucz odpowiedzi do lekcji 3 Matematyki (na końcu dokumentu). Kuba musi na żywo trafić dokładnie 2 z 5, a potem 4 z 5.

## Przebieg

### 0:00–1:00 Wstęp
Pokaż stronę startową (okno bez logowania).

Co powiedzieć:
- „IMSU to platforma kursów dla uczniów do 16 lat. Każda lekcja ma tę samą treść w trzech wersjach: do oglądania (V), do słuchania (A) i do zrobienia samodzielnie (K). Uczeń uczy się zawsze w **jednej** formie naraz.”
- „System sprawdza wynikami, czy forma działa. Gdy uczniowi nie idzie, proponuje inną **z argumentami z danych**. Każdą decyzję zapisuje w dzienniku, a o zmianie stylu na stałe decyduje uczeń.”
- „Każda reakcja systemu wynika z reguły w czystej funkcji (R1–R11) i niesie liczby, z których wynika. Nie ma decyzji »z niczego« ani modelu językowego w środku.”

### 1:00–2:45 Nowy uczeń: ankieta, procenty, katalog, prośba (`uczen.nowy`) — R1
1. „Zaloguj się” → `uczen.nowy@imsu.pl`. Kliknij „Kursy”: system kieruje na ankietę.
   - „Bez ankiety nie ma stylu, więc serwer nie wyda lekcji ani quizu (`403 SURVEY_REQUIRED`).”
2. Wypełnij ankietę (20 pytań; wybieraj głównie odpowiedzi „słuchowe”, np. 11–12 razy). Kliknij „Zobacz wynik”.
3. Ekran wyniku: procenty V / A / K na paskach i styl.
   - **R1:** „Punkty z ankiety zamieniamy na procenty, które sumują się do 100, a każda forma ma co najmniej 5%. Na przykład V 6 / A 10 / K 4 daje A 50 / V 30 / K 20.”
   - „Przy remisie uczeń sam wybiera jeden z remisujących stylów (»Wybieram ten styl«). Styl jest zawsze jeden.”
4. „Przejdź do kursów” → **Katalog** (zrzut 04): tytuł, opis, nauczyciel, liczba lekcji. Każdy kurs ma innego nauczyciela: Programowanie — Paweł Sikora, Angielski — Katarzyna Wróbel, Matematyka — Anna Nowak. Przy „Angielski: Present Perfect” kliknij „Zapisz się”. Pojawi się „Prośba wysłana – czeka na nauczyciela”.
   - „Kursy nie są otwarte dla wszystkich. Uczeń prosi o zapis, a nauczyciel kursu przyjmuje go albo odrzuca.”

### 2:45–3:15 Nauczyciel czeka na zatwierdzenie (`nauczyciel.nowy`)
1. Okno incognito → `nauczyciel.nowy@imsu.pl`. Ekran: **„Konto czeka na zatwierdzenie przez administratora”**.
   - „Każdy może się zarejestrować jako nauczyciel, ale tworzyć kursy może dopiero po zatwierdzeniu konta. Serwer odrzuca każde żądanie nauczyciela z kodem `403 TEACHER_NOT_APPROVED`.”
2. „Wyloguj”.

### 3:15–4:45 Administrator: zatwierdzenie i zmiana właściciela kursu (`admin.demo`)
1. `admin.demo@imsu.pl` → „Użytkownicy” → zakładka „Nauczyciele” → filtr **„Czekające (1)”** → przy Piotrze „Zatwierdź” (zrzuty 07–08).
   - „Kolumna »Konto« pokazuje stan tekstem: Zatwierdzone / Czeka na zatwierdzenie / Odrzucone.”
2. „Kursy” (zrzut 09): wszystkie kursy z autorem, stanem „Opublikowany” i przyciskiem „Zmień właściciela”. Przy „Angielski: Present Perfect” kliknij **„Zmień właściciela”**.
   - Okno „Zmień właściciela kursu”: „obecny autor: Katarzyna Wróbel. Zapisy uczniów, wyniki i statystyki zostają bez zmian.” Pole „Nowy autor” — lista zatwierdzonych nauczycieli; świeżo zatwierdzony Piotr już na niej jest. Wybierz „Piotr Zieliński (nauczyciel.nowy@imsu.pl)” → „Dalej”.
   - Potwierdzenie „Przekazać kurs?”: „Nowy autor zobaczy go w swoim panelu i będzie mógł go edytować; poprzedni straci do niego dostęp.” → **„Zmień właściciela”** (zrzuty 10–12 pokazują to samo dla Programowania i Anny).
   - Na liście przy Angielskim: „Piotr Zieliński · 4 lekcje”; komunikat „Kurs „Angielski: Present Perfect” ma nowego autora: Piotr Zieliński.”
   - „Zmienić właściciela może tylko administrator (`PUT /courses/{id}/owner`), a nowym autorem może być tylko zatwierdzony nauczyciel — inaczej `404 USER_NOT_FOUND` albo `409 TEACHER_NOT_APPROVED`. Każda zmiana zapisuje się w tabeli `course_owner_changes`: kurs, z kogo, na kogo, kto i kiedy.”
3. Opcjonalnie: zaloguj się jako Piotr → „Moje kursy”: Angielski z „1 prośba o zapis” — to prośba Oli sprzed chwili.
   - „Zapisy, wyniki i statystyki należą do kursu, nie do autora, więc prośba Oli przeszła razem z kursem. Załączniki poprzedniej autorki zostają w lekcjach.”
4. Przywróć właściciela: „Zmień właściciela” przy Angielskim → „Katarzyna Wróbel (nauczyciel.angielski@imsu.pl)” → „Dalej” → „Zmień właściciela”. To drugi wpis w `course_owner_changes`. (Jeśli zabraknie czasu, `--reset-students` po pokazie i tak przywraca właścicieli kursów demo.)

### 4:45–6:45 Nauczycielka: lekcja w 3 wersjach, gotowość, prośby, panel kursu (`nauczyciel.demo`) — R11
1. `nauczyciel.demo@imsu.pl` → „Moje kursy” (zrzut 14): kurs Anny — Matematyka, „Opublikowany · 4 z 4 lekcji opublikowanych”, „1 prośba o zapis” (Zosia). Angielski i Programowanie mają swoich nauczycieli.
2. Matematyka → lekcja „Miejsce zerowe” → **edytor lekcji** z zakładkami „Zarys i wnioski”, „Wzrokowa (V)”, „Słuchowa (A)”, „Kinestetyczna (K)”, „Quiz (pula)” (zrzuty 16–20).
   - V: tekst z rachunkiem miejsca zerowego jako **blok kodu** (czcionka o stałej szerokości), wykres i schemat przypadków (PNG).
   - A: krótki opis i **3 krótkie nagrania (30–50 s)** zatytułowane jak sekcje wersji V („Jak obliczyć miejsce zerowe?”, „Szczególne przypadki”, „Gdzie wartości są dodatnie?”) oraz **„Powtórka” (ok. 25 s)**; każde nagranie ma transkrypcję.
   - K: instrukcja „1. Zapisz… 2. Oblicz…” i karta zadania PDF (ostatnia strona zawiera odpowiedzi).
   - „Quiz (pula)”: 8 pytań, przy każdym poprawna odpowiedź i **wyjaśnienie**; licznik „w puli (min. 5)”.
   - „Wszystkie trzy wersje uczą tego samego, a pytania z puli dotyczą wspólnej treści. Uczeń z każdej wersji musi umieć na nie odpowiedzieć. Słuchowiec dostaje krótkie części i powtórkę zamiast jednego długiego nagrania.”
3. Panel **gotowości** (**R11**): lekcja jest kompletna, więc widać „Wycofaj publikację”.
   - „Lekcji nie da się opublikować, dopóki czegoś brakuje: zarysu, wniosków, obrazu w wersji V, nagrania i opisu w A, instrukcji i karty PDF w K albo 5 pytań w puli.”
   - „Opublikowana lekcja nie może stać się niekompletna: zapis, który usunąłby np. kartę PDF, serwer odrzuci (`409 PUBLISHED_LESSON_INCOMPLETE`). Wszystkie 12 lekcji demo opublikował seed przez ten sam moduł (`authoring`), więc każda przeszła tę kontrolę.”
4. Wróć do kursu → **„Panel kursu”** (zrzuty 22–23):
   - **„Prośby o zapis (1)”**: Zosia Mazur → „Przyjmij”.
   - **Uczniowie (7)**: tabela ze stylem, procentami, postępem, średnią i ostatnią aktywnością. Julia Kamińska ma otwartą propozycję „zmiana na A (słuchowy)”.
   - **„Skuteczność form”** (policzone wyniki w tym kursie):

     | Forma | Średnia | Wyniki | Podejścia | Uczniowie |
     |---|---|---|---|---|
     | V | 60% | 5 | 6 | 3 |
     | A | 86% | 7 | 7 | 3 |
     | K | 70% | 4 | 4 | 2 |

     „W tym kursie najlepiej wypada forma słuchowa. To dane tylko z tego kursu i tylko z pierwszych podejść w danej formie.”
   - **„Rozkład stylów”**: V 3 · A 2 · K 2.

### 6:45–7:45 Podpowiedź z kursu, przyciski lekcji, nagrania (`uczen.zapis`) — R8, R10
1. Zwykłe okno → wyloguj Olę → `uczen.zapis@imsu.pl` → „Kursy”: w „Moich kursach” Matematyka z przyciskiem **„Kontynuuj: Lekcja 1 – Wzór i wykres”** (zrzut 24) → otwórz kurs.
2. Ramka „Podpowiedź z kursu” (zrzut 25): **„W tym kursie najlepiej wypada forma słuchowa (średnio 86%, 3 uczniów). To tylko informacja: lekcje dostajesz w swoim stylu, a formę każdej lekcji możesz zmienić w trakcie.”**
   - **R8:** „Zosia nie ma jeszcze żadnego wyniku w tym kursie, więc system pokazuje, jak radzą sobie inni. Liczą się tylko formy, w których uczyło się co najmniej 2 uczniów. System niczego nie zmienia sam.”
3. „Streszczenie kursu”: ponumerowane lekcje z zarysami. Przy lekcji 1 przycisk **„Rozpocznij”**, przy lekcjach 2–4 kłódka i „Najpierw zalicz lekcję 1 / 2 / 3” (**R10**).
   - „Przycisk zależy od stanu ucznia w lekcji: »Rozpocznij« bez wyniku, »Kontynuuj« po niezaliczonym podejściu albo wyborze formy, »Powtórz« z najlepszym wynikiem po zaliczeniu.”
4. „Rozpocznij” → lekcja 1 w wersji A (zrzuty 26–27). Linia nad treścią: **„Forma: Słuchowa (Twój styl) · Zmień formę tej lekcji”** — spokojny link z menu, nie duży przycisk. Pod opisem 3 nagrania (0:37, 0:43, 0:40) i „Powtórka” (0:24). Rozwiń **„Transkrypcja”** pod pierwszym nagraniem: zapis rozmowy nauczycielki z Markiem, wzory zapisane jak w zeszycie („y = 2x + 1”).
   - „Transkrypcja jest domyślnie zwinięta. Pomaga, gdy ktoś nie może słuchać albo chce wrócić do wzoru.”

### 7:45–10:45 Sugestia, zmiana formy i propozycja (`uczen.demo`) — R2, R5, R9, R3, R6, R7
1. `uczen.demo@imsu.pl` → „Mój styl” (zrzut 28): styl wzrokowy, V 45 / A 40 / K 15. Przy formach: V „potwierdzona wynikami”, A i K „tylko z ankiety”.
   - „Kuba ma za sobą 2 lekcje Matematyki: lekcję 1 w V na 80%, lekcję 2 w V na 40% (dostał wtedy sugestię A, ale ją zignorował) i powtórkę lekcji 2 w V na 80%. Powtórka zaliczyła lekcję, ale nie zmieniła procentów.”
2. „Kursy” → Matematyka (zrzut 29): lekcje 1–2 „Zaliczona · najlepszy wynik 80%” z przyciskiem „Powtórz”, lekcja 3 „Rozpocznij”, lekcja 4 z kłódką „Najpierw zalicz lekcję 3”. Kliknij „Rozpocznij” przy lekcji 3 „Miejsce zerowe”.
   - Linia nad treścią (zrzut 30): **„Forma: Wzrokowa (Twój styl) · Zmień formę tej lekcji”**. Widać „Zarys”, wersję wzrokową (tekst, rachunek w bloku kodu, wykresy) i „Wnioski”.
3. „Sprawdź się”: 5 pytań wylosowanych z puli 8. Odpowiedz **poprawnie na 2** (klucz na końcu) → „Sprawdź” (zrzut 31).
   - Wynik: „Jeszcze nie: 2 z 5 (40%) – zaliczenie od 70%”. Przy każdym pytaniu poprawna odpowiedź z wyjaśnieniem.
   - „Co to zmieniło”: **„Wzrokowe 45% → 35%”**.
     **R2:** „Pierwsze podejście w danej formie w tej lekcji zmienia procent formy o 10 punktów. Pozostałe formy dzielą resztę proporcjonalnie, więc teraz jest V 35 / A 47 / K 18.”
   - Ramka sugestii (**R5**): **„Spróbuj tej lekcji w formie słuchowej. Wzrokowe: ten quiz 40%, poprzednia lekcja 40%. Słuchowe były drugie w Twojej ankiecie (40%), nie mamy jeszcze o nich wyników – warto sprawdzić.”**
     „Wyraźna ramka pojawia się tylko po niezaliczonym quizie. Kuba nie ma jeszcze zaliczonej formy innej niż V, więc system sięga po drugą formę z ankiety. Uzasadnienie niesie liczby.”
4. Kliknij **„Przerób tę lekcję w formie słuchowej”**. Linia pokazuje teraz **„Forma: Słuchowa (wybrana dla tej lekcji) · Zmień formę”**, ramka znika (zrzut 32). Odtwórz kilka sekund pierwszego nagrania.
   - „Wybór formy dotyczy tylko tej lekcji i trafia do dziennika. Styl Kuby się nie zmienił. Otwarty zestaw pytań był z formy V, więc serwer losuje nowy dla formy A.”
5. „Sprawdź się” (nowe losowanie: najpierw pytania spoza poprzedniego zestawu, **R9**). Odpowiedz **poprawnie na 4** → „Sprawdź” (zrzut 33).
   - „Zaliczone: 4 z 5 (80%)”. „Co to zmieniło”: **„Słuchowe 47% → 57% · Lekcja 4 odblokowana”** (**R2**, **R10**).
   - Baner propozycji (**R6**): **„Lepiej idzie Ci w formie słuchowej – przełączyć styl na stałe?”**, „Dlaczego: Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%”.
     „Słuchowa jest teraz **potwierdzona wynikami** (**R3**: zaliczenie w tej formie) i ma wyższy procent niż styl Kuby (57 wobec 28). Forma tylko z ankiety nigdy nie dostaje propozycji.”
6. Kliknij **„Przełącz na stałe”** (zrzuty 34–35).
   - **R7:** „Zaczyna się okres próbny: 2 lekcje w nowej formie. Średnia przed zmianą to 40%, czyli 2 ostatnie policzone wyniki w V. Po 2 lekcjach system porówna średnie. Wzrost o co najmniej 10 punktów oznacza, że zmiana pomogła. Spadek o 10 lub więcej oznacza propozycję powrotu.”
   - „Przy zmianie stylu system czyści wybory formy w niezaliczonych lekcjach. Kuba miał wybór tylko w lekcji 3, a tę już zaliczył, więc nic nie zostało wyczyszczone.”
   - „Mój styl” pokazuje styl słuchowy i „0 z 2 lekcji w nowej formie”.

### 10:45–12:00 Okres próbny, wykres, dziennik, kod (`uczen.zmiana`) — R7, R4
1. `uczen.zmiana@imsu.pl` → „Moje postępy” (zrzut 37):
   - **„Procenty form w czasie”**: punkty tylko dla ankiety i policzonych quizów, oś opisana zdarzeniami („Ankieta”, „L1 · K”, „L1 · V”, „L2 · V”, „L3 · V”), od K 50 / V 35 / A 15 do V 72 / A 9 / K 19. Przyjęta zmiana stylu to pionowa linia „styl V” — bez własnego punktu, bo nie zmienia procentów.
   - Tabela pod wykresem z kolumną **„Zdarzenie”**: „Ankieta”, „Quiz: Pętla for – forma K, 40%”, …, „Zmiana stylu na V (propozycja systemu)” z „bez zmian” zamiast powtórzonych procentów.
   - **„Wyniki lekcji”**: Programowanie. Lekcja 1: K 40% (niezaliczone), potem V 80%. Lekcja 2: V 100%. Lekcja 3: V 80%.
   - **„Dziennik decyzji”** (od najnowszego): koniec okresu próbnego **„Zmiana pomogła: średnia 40% → 90%”**, pochwała „3 lekcje z rzędu zaliczone w formie wzrokowej, średnio 87%”, wyniki quizów, pochwała „2 lekcje z rzędu… średnio 90%”, rozpoczęcie okresu próbnego („Średnia przed zmianą: 40% w formie kinestetycznej.”), przyjęta propozycja K → V, propozycja („Kinestetyczne: 1 lekcja, średnio 40% · Wzrokowe: 1 lekcja, średnio 80%”), zmiana formy lekcji według sugestii i sugestia.
   - „Każda decyzja ma swoje dane. To jest odpowiedź na pytanie »dlaczego system tak zrobił«.”
2. „Kursy” → Programowanie → lekcja 1 „Pętla for” (zrzut 39): **„Forma: Wzrokowa (Twój styl)”** — Marta wybrała kiedyś V dla tej lekcji, ale V jest teraz jej stylem, więc to nie jest już osobny wybór. Kod w treści jako **blok kodu** (`for owoc in owoce:` z wcięciem) i fragmenty `kodu` w zdaniach.
3. Opcjonalnie, na żywo (**R4**): lekcja 4 „break i continue” (w V) → odpowiedz poprawnie na 4 z 5. Pojawi się pochwała **„4 lekcje z rzędu zaliczone w formie wzrokowej, średnio 85%”** (także jako wpis w dzienniku) i „Kurs ukończony”.
   - „Seria liczy tylko policzone zaliczenia w tej samej formie.”

### 12:00–12:45 Opcjonalnie: cofnięcie zmiany stylu przed pierwszą lekcją (`uczen3`) — R7a
1. `uczen3@imsu.pl` (Szymon) → „Mój styl” (zrzut 40): styl słuchowy, A 90%, „potwierdzona wynikami (4 lekcje, średnio 85%)”.
2. „Zmień styl” → zaznacz „Wzrokowa (V)” → „Zmień styl” → w oknie potwierdzenia „Zmień styl” (zrzut 41): „Twój styl: wzrokowy (V) – zmieniony ręcznie”, ramka **„Okres próbny: nauka w formie wzrokowej — 0 z 2 lekcji w nowej formie. Średnia przed zmianą: 80% w formie słuchowej.”** (dwa ostatnie policzone wyniki w A: 80% i 80%).
3. Bez żadnej lekcji: zaznacz „Słuchowa (A)” → „Zmień styl” → „Zmień styl” (zrzut 42): „Twój styl: słuchowy (A) – zmieniony ręcznie”, **bez nowego okresu próbnego**.
   - **R7a:** „Zmiana na V nie została sprawdzona ani jedną lekcją, więc powrót do A to cofnięcie: okres próbny dostaje stan `cancelled`, a nowy »V → A« bez danych do porównania się nie zaczyna. Gdyby Szymon zamiast A wybrał K, okres zostałby zastąpiony okresem A → K z tym samym punktem odniesienia — średnią 80% w A.”
4. „Moje postępy” (zrzut 43): na wykresie przekreślony znacznik „styl V” z dopiskiem **„cofnięta”**; w tabeli wiersze „Zmiana stylu na V (ręcznie)” i „Zmiana cofnięta – znów styl A”, oba z „bez zmian”; w dzienniku **„Zmiana na styl wzrokowy (V) cofnięta przed pierwszą lekcją – wracamy do stylu słuchowego (A). Okres próbny anulowany, nowy się nie zaczyna.”**
   - Statystyki Matematyki się nie zmieniają: procenty i wyniki Szymona są te same, a styl znów A.

### 12:45–13:30 Nauczycielka: szczegóły ucznia (`nauczyciel.demo`)
1. Okno incognito → „Panel kursu” Matematyki → w tabeli „Uczniowie” kliknij Kubę (zrzuty 44–45).
2. Widać to samo co w „Moich postępach” Kuby: procenty form, procenty w czasie, wyniki lekcji w tym kursie, a w dzienniku decyzji świeżą sugestię, zmianę formy, propozycję i jej przyjęcie z liczbami.
   - „Nauczyciel widzi uzasadnienia, a nie tylko wyniki. Wie, dlaczego Kuba uczy się teraz w formie słuchowej i co system sprawdzi w okresie próbnym.”
3. Wróć do „Skuteczność form”: po pokazie forma A ma 8 policzonych wyników ze średnią 85%, a V 6 wyników ze średnią 57%.

### 13:30–15:00 Podsumowanie i pytania
- **Architektura:** FastAPI + PostgreSQL + Next.js. Moduły backendu: `identity` (konta, zatwierdzanie), `curriculum` (kursy, lekcje, zapisy, blokada, zmiana właściciela), `content` (3 wersje lekcji, pliki, nagrania z transkrypcją), `learning_style` (ankieta, reguły R1–R8 i R7a, dziennik, statystyki, stany lekcji ucznia), `assessment` (pula, losowanie, ocena), `authoring` (gotowość i publikacja).
- **Ocena tylko na serwerze:** klucz nie trafia do przeglądarki, a wynik idzie jednym wywołaniem `record_quiz_result` przez reguły R2–R7.
- **Dane demo:** historie uczniów powstały przez prawdziwe serwisy, więc dziennik i procenty są prawdziwe. Seed tylko przesunął daty o dni wstecz.

## Pytania, które mogą paść

- **Skąd system wie, że forma działa?** Z wyników quizów: liczymy średnią policzonych wyników w każdej formie i to, czy forma ma choć jedno zaliczenie (**R3**). Propozycję zmiany na stałe dostaje tylko forma potwierdzona wynikami, nigdy forma tylko z ankiety (**R6**). Po zmianie okres próbny porównuje średnie przed i po (**R7**).
- **Dlaczego tylko jeden styl naraz?** Żeby dało się zmierzyć, co działa. Gdyby uczeń dostawał wszystko naraz, wynik quizu nie mówiłby nic o formie. Jedna forma na lekcję daje czysty pomiar: wynik w formie X. Uczeń zawsze może przerobić konkretną lekcję w innej formie („Zmień formę tej lekcji”), a ten wybór też jest zapisany.
- **Dlaczego +10 tylko za pierwsze podejście w formie?** Inaczej procenty dałoby się nabić powtarzaniem tego samego quizu. Kolejne podejścia w tej samej formie są zapisywane i mogą zaliczyć lekcję, ale procentów nie zmieniają (**R2**: „To kolejne podejście w tej formie – procenty bez zmian”).
- **Czy druga szansa w innej formie nie jest łatwiejsza?** Jest. Uczeń zna już część pytań i wyjaśnienia, więc +10 dla formy drugiej szansy może zawyżać jej procent. Łagodzą to trzy rzeczy: przy powtórce losujemy w pierwszej kolejności inne pytania (pula 8, zestaw 5: 3 nowe i 2 z poprzedniego, **R9**), liczy się tylko pierwsze podejście w każdej formie, a propozycja na stałe wymaga potwierdzenia formy. Mówimy o tym otwarcie jako o znanym ograniczeniu.
- **Co, jeśli uczeń zmieni styl i od razu się rozmyśli?** Zmiana bez ani jednej lekcji w nowej formie nie jest sprawdzona: powrót do poprzedniego stylu ją cofa (okres próbny `cancelled`, zdarzenie `style_change_reverted`), a przejście na trzeci styl zachowuje pierwotny punkt odniesienia (**R7a**). Po policzonych lekcjach zmiana działa jak dotąd.
- **Co się dzieje z kursem po zmianie właściciela?** Zapisy, zaliczenia, wyniki i statystyki zostają, bo należą do kursu i uczniów. Poprzedni autor traci kurs ze swojego panelu, nowy widzi go od razu, katalog pokazuje nowego autora. Załączniki poprzedniego autora użyte w lekcjach zostają. Historia zmian jest w tabeli `course_owner_changes` (bez widoku w aplikacji).
- **Przecież teoria stylów VAK jest krytykowana?** Tak. Pashler i in. (2008) pokazali, że brakuje dowodów na *meshing*, czyli na to, że dopasowanie formy do zadeklarowanego stylu poprawia wyniki. Dlatego ankieta jest tu tylko **hipotezą startową**. System nie zakłada, że jest prawdziwa: sprawdza ją wynikami ucznia, pokazuje dane, a decyzję o zmianie stylu zostawia uczniowi. Okres próbny sprawdza, czy zmiana rzeczywiście pomogła.
- **Czy uczeń może oszukać wynik?** Nie. Pytania losuje serwer i zapisuje zestaw razem z formą lekcji, odpowiedzi ocenia serwer, klucz nie trafia do przeglądarki, a powtórki nie zmieniają procentów.
- **Co z uczniem, który nie chce zmiany?** „Zostaję przy swoim”. Propozycja tej samej formy wraca najwcześniej po 2 nowych policzonych wynikach (**R6**).

## Klucz odpowiedzi (do pokazu)

Matematyka, lekcja 3 „Miejsce zerowe”. Kuba odpowiada poprawnie na 2 z 5 (40%), a potem na 4 z 5 (80%).

| Pytanie | Poprawna odpowiedź |
|---|---|
| Czym jest miejsce zerowe funkcji? | argumentem x, dla którego y = 0 |
| Jakie jest miejsce zerowe funkcji y = 2x − 4? | 2 |
| Jakie jest miejsce zerowe funkcji y = −3x + 6? | 2 |
| W którym punkcie wykres funkcji y = 2x − 4 przecina oś x? | (2, 0) |
| Ile miejsc zerowych ma funkcja y = 5? | żadnego |
| Jakie jest miejsce zerowe funkcji y = x + 3? | −3 |
| Dla jakich x funkcja y = 2x − 4 ma wartości dodatnie? | dla x > 2 |
| Którym wzorem obliczysz miejsce zerowe funkcji y = ax + b, gdy a ≠ 0? | x₀ = −b : a |

Programowanie, lekcja 4 „break i continue” (opcjonalnie dla Marty, 4 z 5):

| Pytanie | Poprawna odpowiedź |
|---|---|
| Co robi instrukcja break w pętli? | natychmiast kończy całą pętlę |
| Co robi instrukcja continue w pętli? | pomija resztę bieżącego obrotu i przechodzi do następnego |
| Lista [3, 8, -1, 5], break przy n < 0 – co zobaczysz? | 3 i 8 |
| for n in range(1, 7), continue dla parzystych – co wypisze? | 1, 3, 5 |
| Jak kończy się pętla while True:? | instrukcją break, gdy spełniony jest warunek wyjścia |
| Ile wynosi 7 % 2 w Pythonie? | 1 |
| for n in range(20, 40), print i break przy n % 7 == 0 – co wypisze? | 21 |
| Czy print("koniec") po pętli wykona się po break? | Tak – break kończy tylko pętlę, program działa dalej. |

## Po pokazie
`.\venv\Scripts\python.exe -m app.demo.seed --reset-students` (w `backend`): wszystkie konta wracają do stanu startowego (Piotr znów czeka na zatwierdzenie, Zosia znów prosi o zapis, Kuba znów jest „tuż przed sugestią”, Szymon ma czystą historię), a kursy demo wracają do swoich nauczycieli — kurs przepięty na pokazie na konto demo (Annę, Katarzynę, Pawła, Piotra) seed przepina z powrotem przez `curriculum.change_owner` (wypisuje „zmieniono autora kursu …” i dopisuje wiersz w `course_owner_changes`). Kursy i ich treść zostają. Kursu przepiętego na konto spoza demo seed nie znajdzie — przepnij go z powrotem w aplikacji przed resetem.

## Uruchomienie od zera

Wymagania: Docker Desktop, Python 3.12, Node.js. Komendy w PowerShell, z katalogu `aplikacja\`.

```powershell
# 1. Baza danych (PostgreSQL w Dockerze)
Copy-Item .env.example .env
docker compose up -d

# 2. Backend
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env        # JWT_SECRET: własny klucz, min. 32 znaki
.\venv\Scripts\python.exe -m alembic upgrade head      # tabele + 20 pytań ankiety
.\venv\Scripts\python.exe -m app.demo.seed             # konta, 3 kursy u 3 nauczycieli (79 plików), historie uczniów
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --port 8001

# 3. Frontend (drugi terminal)
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev                                            # http://localhost:3001
```

Uwagi:
- Seed jest idempotentny: drugie uruchomienie niczego nie zmienia i wypisuje „bez zmian”. `--reset-students` przywraca stan startowy wszystkich kont demo i właścicieli kursów demo. `--refresh-demo-media` zapisuje od nowa treść kursów demo z `courses.py` (wersje A z 3 nagraniami, powtórką i transkrypcjami, kod w lekcjach, podsumowania) — potrzebne raz w bazie sprzed poprawek 12.11; nadpisuje zmiany nauczyciela w treści kursów demo.
- Baza sprzed poprawek 12.11: `alembic upgrade head` (migracja `7d2e9b4c1a35`) → `python -m app.demo.seed` (przepina Angielski i Programowanie na ich nauczycieli: dwa wiersze „zmieniono autora kursu …”) → `python -m app.demo.seed --refresh-demo-media`.
- Zasoby demo (19 PNG, 48 MP3, 12 PDF) leżą w `backend/app/demo/assets/`. Tworzą je generatory `app.demo.generate_assets` i `app.demo.generate_audio`, uruchamiane w osobnym venvie narzędziowym (Pillow, edge-tts, imageio-ffmpeg; nagrania wymagają internetu).
- Komendy uruchamiaj przez `python -m ...`. Pliki `.exe` w `venv\Scripts` przestają działać po przeniesieniu folderu z projektem.
- Sprawdzenie kodu: w `backend`: `python -m pytest` (540 testów), `python -m ruff check .`; we `frontend`: `npm run lint`, `npm run build` (nie przy działającym `npm run dev` na tym samym `.next`).
- Przejście automatyczne po wszystkich kontach: `node e2e/demo-tour.mjs` we `frontend` (Playwright spoza zależności projektu, dane po `--reset-students`); zapisuje 50 zrzutów do `docs/zrzuty-v3/`. Po przejściu znów `--reset-students`.
