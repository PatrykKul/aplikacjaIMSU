# Koncepcja systemu

Źródła: system prowadzącego z filmów, feedback ustny i slajdy wykładu (`01-kontekst-i-materialy.md`; odwołania „§3.x” dotyczą tamtego dokumentu). Ustalenia autorów: listopad 2026; stan po etapie 9 (v3, 12.11). Szczegóły reguł z liczbami: `moduly/04-learning-style.md`.

## 1. W skrócie

Multimedialny inteligentny system uczący (MITS, §3.1) z **głównym modułem nauczyciela**. Nauczyciel tworzy kurs z lekcjami; każda lekcja ma tę samą treść w **trzech wersjach** — wzrokowej (V), słuchowej (A) i kinestetycznej (K; w interfejsie „praktyczna”, D66) — oraz jeden quiz z **puli** pytań. Uczeń po rejestracji wypełnia ankietę VAK raz i dostaje **jeden aktywny styl** oraz **profil procentowy** V / A / K. Każdą lekcję przerabia w jednej formie (domyślnie w swoim stylu), quiz losuje 5 pytań z puli i ocenia serwer. Wynik zmienia procent formy, w której lekcja była przerabiana. Gdy w danej formie uczniowi nie idzie, system **proponuje inną formę z argumentami z danych**, a decyduje uczeń. Każda decyzja trafia do **dziennika** z liczbami, z których wynika; nauczyciel widzi w swoim kursie, która forma działa.

Zasada nadrzędna: **zero decyzji „z niczego”** — każda reakcja systemu pochodzi z reguły w czystej funkcji (`learning_style/rules.py`) i niesie swoje liczby; backend zwraca kody i liczby, zdania składa frontend w jednym miejscu (`explain.ts`, D45).

## 2. Role i dostęp

| Rola | Co robi |
|---|---|
| Uczeń | rejestracja → **ankieta VAK** (raz, wymagana; przy remisie wybór jednego z remisujących stylów) → katalog kursów i **prośba o zapis** → po przyjęciu lekcje kolejno (następna po zaliczeniu quizu poprzedniej) → „Moje postępy” (wykres procentów, wyniki, dziennik) i „Mój styl” (styl, procenty, propozycje, okres próbny, ręczna zmiana) |
| Nauczyciel | **moduł główny:** po **zatwierdzeniu konta przez administratora** — kursy, lekcje z zarysem, trzema wersjami, wnioskami i pulą pytań; publikacja lekcji (gdy kompletna) i kursu; przyjmowanie próśb o zapis; panel kursu (uczniowie, skuteczność form, rozkład stylów) i szczegóły ucznia z dziennikiem |
| Administrator | **zatwierdza albo odrzuca konta nauczycieli**; zarządza kontami uczniów i nauczycieli (tworzenie, edycja, blokada zamiast usuwania); podgląd wszystkich kursów (odczyt) i **zmiana właściciela kursu** na zatwierdzonego nauczyciela (zapisy i wyniki zostają, każda zmiana w `course_owner_changes`, D56) |

- Rola wybierana przy rejestracji (uczeń albo nauczyciel) i stała; administrator tylko z CLI (D8). Nauczyciel z rejestracji czeka na zatwierdzenie (ekran „Konto czeka na zatwierdzenie”), założony przez administratora — od razu zatwierdzony (D47).
- Nauczyciel widzi i edytuje **tylko swoje kursy**, bez współautorów.
- **Dostęp do kursów przez zapisy** (D46): uczeń widzi w katalogu kursy opublikowane, prosi o zapis, autor przyjmuje albo odrzuca (odrzucony może poprosić ponownie). Treść lekcji i quiz — tylko po przyjęciu; przyjęty zachowuje dostęp po wycofaniu publikacji kursu. Klas nie ma.
- **Kolejność lekcji** (D48, R10): lekcja n+1 dostępna po zaliczeniu (≥ 70%) quizu lekcji n; egzekwuje serwer.

## 3. Struktura kursu (model dziedziny)

**Kurs → lekcje** (kolejność ustala nauczyciel). Meta-model z wykładu (§3.4): Course = kurs, Learning Unit = lekcja, Content = wersja lekcji (bloki tekstu), Multimedia Object / Content Link = załącznik, Exercise / Test = quiz lekcji.

| Element | Zawartość |
|---|---|
| Kurs | tytuł, **opis** (karta w katalogu), **wstęp**, **podsumowanie i wnioski**, autor, prywatny / opublikowany (≥ 1 opublikowana lekcja), archiwizacja |
| Lekcja | tytuł, **zarys** (2–3 zdania), **trzy wersje V / A / K**, **wnioski**, **pula pytań**, szkic / opublikowana |
| Wersja V | tekst (edytor wizualny: wklejanie z Worda, wzory) + obraz albo film (schematy, wykresy) |
| Wersja A | nagranie (plik albo tekst czytany przez lektora przeglądarki) + krótki opis |
| Wersja K | instrukcja krok po kroku + karta zadania PDF do wykonania |
| Załącznik | obraz, wideo (plik / YouTube), nagranie, PDF, link; **bez oznaczenia form** — formę wyznacza wersja (D42) |
| Pula pytań | ≥ 5 (do 50) pytań jednokrotnego wyboru (3–4 odpowiedzi) z **wyjaśnieniem**; podejście = 5 losowych pytań; próg 70% (D43) |

Lekcję publikuje się, gdy ma zarys, wnioski, trzy kompletne wersje i ≥ 5 pytań (R11, D49); opublikowana lekcja nie może stać się niekompletna.

## 4. Model ucznia

| Składnik (§3.5) | U nas |
|---|---|
| IP — preferencje | **aktywny styl** (jeden: V, A albo K; źródło: ankieta / wybór przy remisie / ręczny / propozycja) i **procenty V / A / K** (suma 100, każda 5–90; start z ankiety, korekta po quizach); historia procentów |
| S — wyniki | wyniki quizów: lekcja, **forma**, w której lekcja była przerabiana, procent, zaliczenie, czy wynik zmienił procenty („policzony”) |
| statystyki form | dla każdej formy: liczba policzonych lekcji, średnia, **„potwierdzona wynikami”** (co najmniej jedno zaliczenie) albo „tylko z ankiety” |
| decyzje | propozycje zmiany stylu i decyzje ucznia, okresy próbne, wybory formy lekcji, dziennik decyzji |
| Z — zaawansowanie | nie modelujemy (prototyp); postęp = zaliczone lekcje kursu |

Uczeń widzi u siebie całość tych danych; autor kursu widzi je dla przyjętych uczniów swojego kursu.

## 5. Reguły adaptacji (moduł nauczania)

Wszystkie w czystych funkcjach; stałe: próg 70%, krok 10 pkt, minimum 5%, 5 pytań, okres próbny 2 lekcje, progi ±10 pkt.

| Reguła | W skrócie |
|---|---|
| R1. Profil z ankiety | punkty → procenty (min. 5%, suma 100, największe reszty); styl = forma z największą liczbą punktów, remis → uczeń wybiera (do wyboru bez dostępu do kursów). V 9 / A 8 / K 3 → 45 / 40 / 15, styl V |
| R2. Zmiana po quizie | tylko **pierwsze podejście w danej formie w danej lekcji**: forma lekcji ±10, pozostałe dzielą różnicę proporcjonalnie. 45 / 40 / 15 + porażka w V → 35 / 47 / 18 |
| R3. Potwierdzenie formy | forma „potwierdzona wynikami” po co najmniej jednym zaliczeniu w niej (ze wszystkich kursów) |
| R4. Zaliczenie | odblokowanie następnej lekcji; pochwała za serię ≥ 2 zaliczonych lekcji w tej samej formie („3 lekcje z rzędu… średnio 87%”) |
| R5. Porażka | sugestia „Przerób tę lekcję w formie X”: X = potwierdzona forma z najwyższym procentem, a bez potwierdzonych — druga forma ankiety; uzasadnienie liczbami („Wzrokowe: ten quiz 40%, poprzednia lekcja 40%. Słuchowe były drugie w Twojej ankiecie (40%)…”) |
| R6. Propozycja zmiany stylu | tylko dla formy **potwierdzonej** z wyższym procentem niż aktywny styl; dowód „Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%”; odrzucona wraca po 2 nowych policzonych wynikach; każda zmiana stylu czyści wybory formy w niezaliczonych lekcjach |
| R7. Okres próbny | po przyjęciu propozycji albo zmianie ręcznej: 2 lekcje w nowym stylu vs średnia 2 ostatnich w poprzednim — ≥ +10 „pomogła”, ≤ −10 propozycja powrotu, pomiędzy „bez wyraźnej różnicy” |
| R7a. Cofnięcie zmiany | zmiana stylu, gdy okres próbny nie ma jeszcze żadnej policzonej lekcji: powrót do stylu sprzed zmiany cofa ją (okres anulowany, nowy nie startuje: A → V → A), przejście na trzeci styl zastępuje okres nowym z tym samym punktem odniesienia (A → V → K porównuje z wynikami w A) — D60 |
| R8. Podpowiedź z kursu | uczeń bez wyników w kursie: forma z najwyższą średnią innych uczniów (min. 2 uczniów) — tylko informacja |
| R9. Losowanie pytań | 5 z puli, przy powtórce najpierw pytania spoza poprzedniego zestawu; zestaw zapisany na serwerze |
| R10. Blokada lekcji | lekcja n+1 po zaliczeniu lekcji n; zaliczona zostaje dostępna po zmianie kolejności |
| R11. Gotowość lekcji | zarys, wnioski, kompletne wersje V / A / K, ≥ 5 pytań — warunek publikacji |

Lekcja podana uczniowi: zarys → wersja w jego formie (spokojna linia „Forma: Słuchowa (Twój styl) · Zmień formę tej lekcji”; wyraźna ramka „Przerób tę lekcję w formie X” tylko po niezaliczonym quizie) → wnioski → quiz. Wersja A to 2–3 krótkie nagrania pod nagłówkami sekcji i nagranie-powtórka, każde z rozwijaną transkrypcją (D58). Bez mieszania form i bez zwijania materiałów (D42). Na stronie kursu przy lekcji przycisk wg stanu: „Rozpocznij”, „Kontynuuj”, „Powtórz” z najlepszym wynikiem albo kłódka (D57).

**Mapowanie na model z wykładu (§3.5):** strategia = forma podania (V / A / K). Zamiast W(s, e) = argmax w(s, e) z pełnym silnikiem — profil procentowy jako wagi strategii, korygowany wynikami tylko tej formy, w której uczeń faktycznie przerabiał lekcję; zmianę strategii proponują reguły R5–R7 na podstawie wyników, a zatwierdza uczeń.

## 6. Widoki

- **Uczeń:** ankieta i wynik (procenty, wybór przy remisie); „Kursy” (moje kursy z postępem, katalog z prośbą o zapis); strona kursu (wstęp, streszczenie z zarysami i stanem lekcji, podpowiedź z kursu, podsumowanie); lekcja w trybie skupienia (zarys, pasek formy, wersja, wnioski, quiz, wynik z wyjaśnieniami i „Co to zmieniło”, sugestia, propozycja); „Moje postępy” (wykres procentów w czasie z tabelą danych, postęp kursów, wyniki lekcji z formą, dziennik); „Mój styl”.
- **Nauczyciel:** ekran oczekiwania na zatwierdzenie; „Moje kursy”; edytor kursu (ustawienia, publikacja, lekcje ze stanem gotowości); edytor lekcji z zakładkami „Zarys i wnioski”, „Wzrokowa (V)”, „Słuchowa (A)”, „Kinestetyczna (K)”, „Quiz (pula)” i panelem gotowości; podgląd lekcji (przełącznik wersji, pula z wyjaśnieniami); „Panel kursu” (prośby o zapis, uczniowie, skuteczność form, rozkład stylów); szczegóły ucznia.
- **Administrator:** użytkownicy (zatwierdzanie nauczycieli, tworzenie, edycja, blokada); wszystkie kursy z akcją „Zmień właściciela”.

Statystyki jako tabele i jeden wykres liniowy (własny SVG), bez kolorowych plakietek; kolor formy zawsze z literą i nazwą (`07-design.md`). Na wykresie punkty tylko dla ankiety i policzonych quizów, oś opisana zdarzeniami („Ankieta”, „L1 · A”), zmiany stylu jako pionowe znaczniki (cofnięta — przekreślona); tabela z kolumną „Zdarzenie” (D62).

## 7. Wirtualny mentor (opcjonalnie, O3)
Jedna stała postać, komunikaty z reguł (sugestia, propozycja, pochwała), bez LLM (§3.7). Poza zakresem v3.

## 8. Ocena skuteczności i zastrzeżenia
- **Pokaz na kontach demonstracyjnych** (`SCENARIUSZ-POKAZU.md`, D22): wymuszenie ankiety, zatwierdzenie nauczyciela, prośba o zapis i podpowiedź z kursu, ścieżka „porażka → sugestia → inna forma → zaliczenie → propozycja → okres próbny” (Kuba), zakończony okres próbny „Zmiana pomogła: średnia 40% → 90%” (Marta), panel kursu ze skutecznością form (Matematyka: V 60%, A 86%, K 70%).
- **Skuteczność form w kursie** liczona ze średniej policzonych wyników (pierwsze podejścia w formie), z liczbą wyników, podejść i uczniów — nauczyciel widzi, która wersja lekcji działa w jego kursie.
- **Zastrzeżenie o stylach uczenia się:** hipoteza *meshing* (lepsze wyniki, gdy forma materiału pasuje do stylu ucznia) nie ma mocnego potwierdzenia empirycznego, a model VAK jest krytykowany (Pashler i in., 2008). System traktuje ankietę wyłącznie jako **hipotezę startową**: procenty zmieniają tylko wyniki, propozycja zmiany wymaga formy potwierdzonej zaliczeniem, decyzję podejmuje uczeń, a okres próbny sprawdza, czy zmiana coś dała. Trzy wersje lekcji są też po prostu różnymi drogami do tej samej treści.
- **Druga szansa jest łatwiejsza:** po porażce uczeń przerabia lekcję w innej formie, ale zna już część pytań i wyjaśnienia, więc +10 dla formy „drugiej szansy” może zawyżać jej procent. Łagodzą to: inne pytania przy powtórce (R9), liczenie tylko pierwszego podejścia w formie (R2) i wymóg potwierdzenia formy przed propozycją (R6). Efektu nie usuwamy — opisujemy go i omawiamy na pokazie.
- Prototyp nie ma grupy kontrolnej ani danych z prawdziwych zajęć — ocena dotyczy działania i wyjaśnialności reguł, nie efektu dydaktycznego.

## 9. Kursy demonstracyjne
Trzy kursy z seeda (D53), każdy u innego nauczyciela (D55: Matematyka — Anna Nowak, Angielski — Katarzyna Wróbel, Programowanie — Paweł Sikora), każdy po 4 lekcje z kompletnymi wersjami V / A / K (schematy PNG, nagrania MP3 głosem neuronowym, karty PDF) i pulami po 8 pytań: Matematyka: funkcja liniowa, Angielski: Present Perfect, Programowanie: pętle w Pythonie (`moduly/06-demo.md`).

## 10. Pytania do prowadzącego (otwarte)
1. Czy ankieta VAK może być autorska (20 pytań z v1)?
2. Czy reguły zmiany formy (sugestia po porażce, propozycja tylko dla formy potwierdzonej wynikami, okres próbny) są w duchu jego systemu?
3. Czy test końcowy kursu jest oczekiwany?
4. Forma i dokładny termin oddania.
