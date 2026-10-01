# Kurs demonstracyjny „Matematyka: funkcja liniowa"   (01.10.2026)

## Plan (krótko)
1. Generator wykresów SVG w kodzie i dane kursu jako jedno źródło prawdy (treść + wykresy + dane do sprawdzeń).
2. Cztery tematy w układzie jak w kursie Pythona: teoria-ściąga, V (2 wykresy), A (omówienie słowne), K (ćwiczenie), 3 przykłady (poziomy 1/2/3), uwaga z typowym błędem, zadanie, quiz.
3. Testy przeliczające każdą liczbę i każdy klucz quizu na ułamkach.
4. Seed po nazwie, frontend (wykres w bloku `diagram`, KaTeX w odpowiedziach quizu), kontrola renderowania w przeglądarce, dokumentacja.

## Co zrobione (lista, z plikami)
**Backend**
- `app/wykresy.py` – `Prosta`, `Punkt`, `Schodek`, `Wykres` i `wykres_svg()`: układ współrzędnych z siatką, osiami ze strzałkami i podziałką z liczbami, proste przycięte do pola rysunku, legenda ze wzorem, zaznaczone punkty z opisem, „schodek" (o ile w prawo / w górę). Bez bibliotek i bez obrazków z zewnątrz.
- `app/seed_matematyka.py` – kurs „Matematyka: funkcja liniowa": działy „Podstawy" i „Zastosowania", 4 tematy, 44 bloki, 8 wykresów. Przy blokach pole `sprawdzenia` (dane do niezależnego przeliczenia), przy quizach `sprawdzenia_quizu`.
- `app/seed.py` – `seed_kurs_matematyka()` (kurs dodawany po nazwie, kursu Pythona nie rusza) i `zapisz_wykresy_matematyki()` – pliki SVG trafiają do `MEDIA_ROOT/demo/matematyka/` i są odtwarzane przy każdym uruchomieniu seeda.

| Temat | V – wykresy | K – ćwiczenie | Typowy błąd (uwaga) |
|---|---|---|---|
| 1. Wzór $y = ax + b$ | „schodek" dla $y = 2x + 3$; trzy proste równoległe (to samo $a$, różne $b$) | $y = 3x - 2$: trzy wartości, różnice równe $a$, naniesienie punktów | $y = 5 - 2x$: zamiana $a$ z $b$ |
| 2. Wykres i monotoniczność | $y = 2x - 1$ z dwóch punktów; porównanie $a > 0$, $a < 0$, $a = 0$ | tabelka i wykres $y = -2x + 4$ | $y = 3 - 4x$: ocena po pierwszej liczbie |
| 3. Miejsce zerowe i przecięcia z osiami | $y = 2x - 4$ (punkty $(2, 0)$ i $(0, -4)$); $y = -2x + 3$ z miejscem zerowym $\tfrac{3}{2}$ | równanie $3x + 6 = 0$ krok po kroku + sprawdzenie | $y = 2x + 6$: zgubiony minus w $x_0 = -\tfrac{b}{a}$ |
| 4. Wzór przez dwa punkty | $A = (1, 3)$, $B = (3, 7)$ ze schodkiem; prosta malejąca przez $(-1, 4)$ i $(2, -2)$ | $A = (2, 1)$, $B = (4, 5)$: po kratkach, potem rachunkiem | różna kolejność odejmowania w liczniku i mianowniku |

Przykłady na poziomie 3: zadanie z treścią (taksówka, $a = \tfrac{7}{2}$), parametr ($3 - 2m < 0$), ułamek i pole trójkąta, wzór z ułamkami ($y = \tfrac{3}{4}x + \tfrac{11}{4}$).

**Frontend**
- `components/temat/bloki/DiagramBlock.tsx` – gdy blok `diagram` ma `image_url`, pokazuje wykres z podpisem (KaTeX); bez obrazka działa jak dotąd (diagram kroków z tekstu).
- `components/temat/bloki/QuizBlock.tsx` – odpowiedzi quizu renderowane przez KaTeX (np. $\tfrac{3}{2}$, $y = 2x - 4$).
- `components/temat/bloki/CwiczenieBlock.tsx` – podpowiedzi w ćwiczeniach renderowane przez KaTeX.

**Testy** – `tests/test_seed_matematyka.py` (223 przypadki).

**Dokumentacja** – `README.md` (sekcja „Kursy demonstracyjne"), `docs/dokumentacja.md` (scenariusz prezentacji na temacie „Miejsce zerowe…", tabela testów, architektura).

## Decyzje i dlaczego
- **Liczby w treści są pisane wprost, a test liczy je od nowa.** Każdy blok z liczbami ma listę `sprawdzenia`: (rodzaj, dane, zapis w treści). Test wylicza wynik z danych na `fractions.Fraction`, formatuje i sprawdza dwie rzeczy: że wynik równa się zapisowi oraz że ten zapis faktycznie występuje w treści bloku. Dzięki temu test nie sprawdza „sam siebie".
- **Klucz quizu sprawdzany niezależnie:** dla każdego pytania test wyznacza, które odpowiedzi są poprawne, i wymaga, żeby była dokładnie jedna i żeby zgadzała się z kluczem. Przy pytaniach „który wzór / który punkt" test podstawia punkty do każdej z opcji.
- **Wykresy z tych samych danych co treść:** obiekty `Wykres` leżą w temacie obok bloków; test sprawdza, że punkty leżą na prostych, miejsce zerowe równa się $-\tfrac{b}{a}$, przecięcie z $OY$ to $(0, b)$, a te same punkty występują w podpisie bloku i w atrybutach `data-*` wygenerowanego SVG.
- **Wykres jako blok `diagram` z `image_url`** – typ bloku zgodny z poleceniem; drugi wykres w temacie to blok `obraz`.
- **Pliki SVG generowane przy seedzie, nie commitowane** – katalog `uploads/` jest poza repo; seed odtwarza pliki przy każdym uruchomieniu (także gdy kurs już istnieje).
- **Audio w pełni słownie** – test pilnuje, żeby w tekście dla lektora nie było cyfr, znaku `$`, `=`, `+`, ukośników itp. oraz żeby zdania były krótkie.
- **Wzory wyróżnione (`$$`) w osobnych liniach** – inaczej renderują się jak wzór w tekście (wyszło na zrzucie ekranu); jest na to test.
- **Poprawna odpowiedź nie stoi zawsze na tej samej pozycji** (test), a dystraktory to typowe błędy: zły znak, zamiana $a$ z $b$, punkt z osi $OX$ zamiast $OY$, odwrócony iloraz.

## Weryfikacja (komendy + wynik)
- `pytest` → 452 passed (w tym 223 w `test_seed_matematyka.py`)
- `npm run lint` → 0 błędów (4 ostrzeżenia `<img>`)
- `npm run build` → OK
- `python -m app.seed` dwa razy z rzędu → za drugim razem `kurs_matematyka: +0`, `kurs_demo: +0`; kurs Pythona bez zmian.
- **Przeglądarka (headless), konta `wzrokowiec@`, `sluchowiec@`, `kinestetyk@` i nauczyciel, wszystkie 4 tematy:**
  - każdy uczeń widzi bloki wspólne i tylko swojego stylu (V: 2 wykresy; A: „Posłuchaj"; K: „Zrób to sam");
  - KaTeX: we wszystkich blokach wzory wyrenderowane, **0 elementów `.katex-error`**, **0 fragmentów surowego TeX-a** w tekście (sprawdzane także po rozwinięciu odpowiedzi i rozwiązań zadań oraz wszystkich podpowiedzi ćwiczenia, w widoku nauczyciela z poziomami 1 i 3);
  - wszystkie wykresy wczytane (brak zepsutych obrazków);
  - quiz tematu 4 rozwiązany wg klucza → „5 / 5 (100%)";
  - brak błędów w konsoli.
- Obserwacje ze zrzutów ekranu i poprawki w trakcie: tytuły wykresów nie mieściły się w obrazku (skrócone + łamanie po dwukropku + test), wzory `$$…$$` w jednej linii wyglądały jak zwykłe wzory w tekście (przeniesione do osobnych linii + test), dwie etykiety punktów nachodziły na inne opisy (przesunięte). Po poprawkach zrzuty wyglądają poprawnie w trybie jasnym.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. `cd backend && python -m app.seed` (doda kurs i wykresy), uruchom backend i frontend.
2. Zaloguj się jako `wzrokowiec@stylnauki.pl` / `Uczen123!` → Kursy → „Matematyka: funkcja liniowa" → „Zastosowania" → „Miejsce zerowe i punkty przecięcia z osiami".
3. To samo jako `sluchowiec@…` (przycisk „Odsłuchaj") i `kinestetyk@…` (ćwiczenie krok po kroku).
4. Jako nauczyciel włącz „Tryb Edycji" – widać wszystkie warianty i plakietki poziomów (łatwiejszy / rozszerzenie).

## Znane problemy / TODO
- Lokalne bazy, w których kurs matematyki powstał z wcześniejszej wersji treści, nie są nadpisywane (seed nie rusza istniejącego kursu); w tej kopii kurs został odtworzony.
- Lektor czyta polski tekst głosem dostępnym w systemie; wymowa nazw „iks", „igrek" zależy od głosu.
- Wykresy mają jasne tło także w trybie ciemnym (celowo – czytelność osi i siatki).

## Propozycje (poza zakresem)
- Interaktywny wykres dla kinestetyka (suwaki $a$ i $b$).
- Generator wykresów dostępny dla nauczyciela w edytorze bloku (podaje $a$ i $b$, dostaje SVG).

## Commity (hash + opis)
- edb6df4 Seed: kurs „Matematyka: funkcja liniowa" z wykresami SVG generowanymi w kodzie
- dbaefb1 Testy: przeliczenie liczb, kluczy quizów i punktów na wykresach kursu matematyki
- bcb07ff Frontend: wykres w bloku diagram, wzory w odpowiedziach quizu i podpowiedziach ćwiczeń
- 981e72f README i dokumentacja: kursy demonstracyjne, scenariusz prezentacji na temacie „Miejsce zerowe"
