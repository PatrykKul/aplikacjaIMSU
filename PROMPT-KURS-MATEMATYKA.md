# Zadanie: drugi kurs demonstracyjny – matematyka (funkcja liniowa)

Tryb autonomiczny jak dotąd (CLAUDE.md). Raport: `docs/postep/kurs-matematyka.md` + aktualizacja `STATUS.md` + commity.

## Cel
Drugi opublikowany kurs w seedzie, pokazujący personalizację V/A/K na materiale matematycznym (poziom: liceum, klasa 1).
Autor jest korepetytorem matematyki – treść ma być **merytorycznie bezbłędna** i napisana tak, jak tłumaczy dobry korepetytor.

## Struktura
Kurs: **„Matematyka: funkcja liniowa”**
- Dział „Podstawy”:
  1. Wzór funkcji liniowej \(y = ax + b\) – znaczenie \(a\) i \(b\)
  2. Wykres funkcji liniowej i monotoniczność (rosnąca / malejąca / stała w zależności od \(a\))
- Dział „Zastosowania”:
  3. Miejsce zerowe i punkty przecięcia z osiami
  4. Wyznaczanie wzoru funkcji przechodzącej przez dwa punkty

## Każdy temat – ten sam układ co w kursie Pythona
- **teoria** (wspólna): najpierw ściąga – wzór na literach + jeden przykład liczbowy, wzory w KaTeX (`$...$`, `$$...$$`).
- **V**: `diagram` – wykres(y) jako **SVG wygenerowany w kodzie** (osie z podziałką i opisami, siatka, prosta/proste, zaznaczone punkty
  np. miejsce zerowe i \(b\)); zapisz pliki do media i podepnij w bloku. Żadnych obrazków z internetu. Plus `obraz` lub drugi diagram
  (np. porównanie \(a>0\), \(a<0\), \(a=0\) w temacie 2).
- **A**: `audio` – tekst dla lektora przeglądarki: **bez LaTeX-a i symboli**, matematyka słownie („y równa się dwa x plus trzy”,
  „minus trzy drugie”), krótkie zdania, jak omówienie na głos podczas lekcji.
- **K**: `cwiczenie` – zadanie „zrób sam krok po kroku” (np. oblicz trzy punkty, nanieś na układ, połącz; podstaw i sprawdź).
- **3 przykłady** na poziomach 1 / 2 / 3 (łatwy z małymi liczbami całkowitymi, standardowy, rozszerzony – ułamki, parametr, zadanie z treścią).
- **uwaga** – typowy błąd **na konkretnym przykładzie** (np. zamiana \(a\) z \(b\), błąd znaku przy miejscu zerowym \(x_0 = -\tfrac{b}{a}\),
  odejmowanie w złej kolejności przy liczeniu \(a = \tfrac{y_2-y_1}{x_2-x_1}\)).
- **zadanie** (wspólne) z odpowiedzią i rozwiązaniem.
- **quiz** 4–5 pytań jednokrotnego wyboru, dystraktory = typowe błędy uczniów.

## Poprawność (obowiązkowe)
- Każdą liczbę w przykładach, zadaniach i kluczach quizów **policz programem**, nie z głowy: dodaj test pytest, który dla każdego
  pytania quizu i każdego zadania z odpowiedzią przelicza wynik (np. z `fractions.Fraction`) i porównuje z kluczem.
- Wykresy SVG generuj z tych samych danych, z których powstaje treść (jedno źródło prawdy), i dodaj test, że punkty na wykresie
  (miejsce zerowe, przecięcie z OY) zgadzają się z treścią.
- Sprawdź w przeglądarce, że KaTeX renderuje się poprawnie we wszystkich blokach (zrzuty/obserwacje do raportu).

## Seed
- Kurs dodawany po nazwie – idempotentnie (drugie `python -m app.seed` nic nie dubluje), nie rusza kursu Pythona.
- Zaktualizuj README (sekcja kursów demo) i scenariusz prezentacji w `docs/dokumentacja.md`
  (np. ten sam temat „Miejsce zerowe” oczami wzrokowca i słuchowca).
- Weryfikacja: `pytest`, `npm run lint`, `npm run build`; lokalnie odśwież bazę dev (`python -m app.seed`) i sprawdź kurs jako
  `wzrokowiec@`, `sluchowiec@`, `kinestetyk@`.
