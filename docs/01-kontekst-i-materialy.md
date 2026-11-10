# Kontekst projektu i materiały od prowadzącego

## 1. Wymagania

| Kwestia | Ustalenie |
|---|---|
| Przedmiot | Inteligentne multimedialne systemy uczące (IMSU), UwB, magisterka, sem. 1, 2026/27 |
| Charakter | projekt zaliczeniowy, zespołowy |
| Dziedzina | matematyka (wybór zespołu) |
| Grupa docelowa | uczniowie do 16 lat |
| Role | uczeń, nauczyciel, administrator |
| Profil ucznia | **VAK** jako proporcje, zmieniające się w trakcie nauki |
| Treść | **nauczyciel tworzy kurs w edytorze**: lekcje z treścią i załącznikami oznaczonymi V/A/K oraz quiz; **system decyduje, jak podać lekcję** uczniowi i na podstawie quizu ocenia opanowanie i proponuje zmianę stylu |
| Technologia | dowolna; zespół wybrał Next.js + FastAPI + PostgreSQL |
| Dane | brak prawdziwych uczniów do testów — działanie adaptacji pokazujemy sami (scenariusz demonstracyjny, ewentualnie symulacja) |
| Termin | **koniec listopada 2026** |
| Dokumentacja do oddania | podstawowa, minimalna |

## 2. Feedback prowadzącego (05.11.2026, relacja autora)

- Role uczeń / nauczyciel / administrator.
- Nauczyciel ma **narzędzie do składania kursu** z różnego rodzaju materiałów: tekstu, nagrań głosowych, filmików.
- Profil **VAK**. Wynik ankiety nie jest jednoznaczny — **proporcje**, np. V 70%, A 20%, K 10%.
- Proporcje **zmieniają się zależnie od tego, z czego uczeń częściej korzysta**; ustalone z autorem: także **z wyników** (preferencje niejawne — `02-koncepcja.md`).
- System **przy pewnych warunkach proponuje zmianę stylu**.
- Nauczyciel dodaje różne materiały, a **system decyduje, w jaki sposób złożyć kurs** (instancja kursu z meta-modelu — §3.4).

## 2a. Przykładowy system prowadzącego (filmy, obejrzane przez autora 06.11.2026)

- **Administrator** zarządza nauczycielami (dodaje, usuwa) — rola mocno okrojona.
- **Uczeń** po rejestracji wypełnia **ankietę VAK**, potem ma dostępne kursy, na które może się **zapisać** (zasada udostępniania nieznana).
- **Moduł nauczyciela jest główny:** CRUD kursów, CRUD lekcji w kursie, CRUD quizów. Struktura kursu jest stała: **opis kursu + lekcje**. W lekcji nauczyciel edytuje **treść** (w filmie wklejoną z pliku DOCX z formatowaniem), **załączniki oznaczone VAK** i **quiz** przypisany do lekcji.
- **„Inteligencja”:** quiz ocenia opanowanie materiału, na tej podstawie system **proponuje zmianę stylu**.

Nasza wersja rozwija ten system — szczegóły w `02-koncepcja.md`.

## 3. Streszczenie slajdów wykładu

### 3.1 Cel przedmiotu i MITS
- Cel: indywidualizacja kształcenia w systemach internetowych; projektowanie i budowa inteligentnych systemów uczących **adaptujących się do potrzeb użytkownika**.
- **MITS** (multimedialne inteligentne systemy edukacyjne) — kontynuacja ITS. Paradygmat: **wierne odtworzenie działań nauczyciela-eksperta**; działania nauczyciela oraz treść i forma przekazu mają charakter adaptacyjny.
- Architektura: **moduł dziedziny** (reprezentacja wiedzy) → **moduł ucznia** ↔ **moduł nauczyciela** (zarządzanie nauczaniem) ↔ **interfejs komunikacyjny**.
- Wariant **IEEE LTSC** (Chęć): silnik uczący, model ucznia, baza wiedzy, baza metod, ocena, prezentacja, komunikacja. Model ucznia **nakładkowy** (wiedza ucznia ⊂ wiedza eksperta) lub **dewiacyjny** (plus błędna wiedza). Parametry modelu ucznia: profesjonalne, psychologiczne, fizjologiczne, demograficzne.

### 3.2 Style uczenia się
- **VAK** (Fernald, Keller, Orton, Gillingham, Stillman, Montessori, ok. 1920): **V — patrzenie i czytanie**, **A — słuchanie i mówienie**, **K — dotykanie i działanie**. Uwagi ze slajdu: własny styl łatwo określić; do każdego stylu łatwo dobrać strategię nauczania.
- Charakterystyki: wzrokowcy pamiętają kolory, rysunki, położenie; słuchowcy uczą się słuchając i rozmawiając; kinestetycy w ruchu, przez eksperymenty i działanie (nudzą się na wykładzie). Rozwinięcie: VARK.
- **Metody aktywizujące:** wzrokowiec — demonstracje, pokazy, wizualne przedstawienie problemu; słuchowiec — dialog, wykład / pogadanka, **liczne powtórzenia**, odtwarzanie wiedzy wypowiedzią; kinestetyk — wykonywanie czynności, bezpośrednie zaangażowanie.
- Znajomość stylu pozwala zaplanować zajęcia atrakcyjne dla ucznia; nauczyciel powinien znać też własny styl.
- Tło: cykl **Kolba** (konkretne doświadczenie → obserwacja i refleksja → abstrakcyjne hipotezy → testowanie; matematyka = wiedza asymilacyjna → środowisko symboliczne i percepcyjne); **inteligencje wielorakie Gardnera** (równoprawne, zmieniają się w trakcie działania; nauczyciel powinien rozpoznać dominującą).

### 3.3 Strategie uczenia się (tło)
- Definicje (Oxford 1993, O'Malley i Chamot 1990, Griffiths 2008); typologie Oxford (bezpośrednie: pamięciowe, kognitywne, kompensacyjne; pośrednie: metakognitywne, afektywne, społeczne), Rubin, O'Malley i Chamot; trening strategiczny (wiedza deklaratywna „wiem, że” i proceduralna „wiem, jak”; autonomia ucznia).
- Etapy strategii uczenia się: przygotowanie, lektura właściwa, **kolejne powtórki: po 24 h, tygodniu, miesiącu, 3 miesiącach, pół roku**, ostatnia przed sprawdzianem.

### 3.4 Meta-model kursów adaptacyjnych
(Najpewniej Graf i Kinshuk, oparty na modelu stylów Feldera–Silvermana.)
- **Course → Chapter → Learning Unit → Learning Object**; obiekty: **Content, Example, Exercise, Test, Multimedia Object, Content Link, Collection**, Question, Chat, Forum.
- Kurs zaczyna się **streszczeniem** (wszystkie rozdziały), kończy **podsumowaniem i wnioskami**; każdy rozdział ma **zarys i wnioski**. Trzeba określić, co jest pokazywane po rozdziale / jednostce — **dla części uczniów część materiału może być dostępna lub ukryta**.
- Obiekty treści = małe „klocki wiedzy”; mogą zawierać linki — u uczniów sekwencyjnych ukryte w treści i zebrane na końcu rozdziału.
- Obiekty multimedialne (audio z wypowiedzią eksperta, interaktywne animacje) wspierają wzrokowców, uczenie przez działanie i przeżywanie; **mogą być ukryte**, żeby uniknąć przeciążenia lub dać liniowy przebieg; repozytorium obiektów; slajdy jako obiekty wielokrotnego użytku.
- **Przykłady** ważne dla uczących się przez działanie — więcej przykładów dla aktywnych. **Ćwiczenia** (kilka pytań: interpretacja gotowych rozwiązań lub nowe rozwiązania) — więcej dla aktywnych. **Testy** — sekwencyjni: częściej (po jednostce), globalni: na koniec rozdziału.
- Nawigacja: lista wszystkich obiektów albo „następny / poprzedni”.
- Przyszłe prace autorów: **wykrywanie stylu z zachowania w kursie i przypisanie odpowiedniej instancji kursu**.

### 3.5 Modelowanie wyboru strategii nauczania
- Czynniki: cel nauczania, styl ucznia, specyfika przedmiotu, poziom wiedzy ucznia i nauczyciela, dostępne media.
- **Moduł wyboru strategii = zbiór reguł** identyfikujących stan systemu i wybierających strategię.
- **Cztery typy strategii:** **nauczanie, ocena (test kompetencji), powtórka (korekta błędów, uzupełnienie luk), poprawa (ponowna ocena)**; metoda dla fragmentu wiedzy wyznacza sekwencję taktyk: nauka → ocena → w razie potrzeby powtórka i poprawa.
- **Cel nauczania** = stan, do którego dąży uczeń (punkt odniesienia oceny). **Typ wiedzy** (deklaratywna / proceduralna) wpływa na dobór mediów.
- **Stan E = WD × MU.** WD = fragment wiedzy C × typ T {deklaratywny, proceduralny} × prezentacja P {multimedialna, tekstowa}. MU = predyspozycje I × zaawansowanie Z {początkujący, zaawansowany} × wyniki testów S × preferencje IP. (W modelu z wykładu I i IP są stałe — u nas preferencje się zmieniają.)
- Preferencje **jawne** (bezpośrednie pytanie ucznia) i **niejawne** (metody, które wcześniej dały dobre efekty).
- **Wiedza nauczyciela** obejmuje statystykę powodzenia strategii w populacji — używaną, gdy o uczniu wiadomo za mało. **Środowisko nauczania** = media (multimedialne / tekstowe).
- **Funkcja przejścia W: S × E → S**; wartością jest strategia o **maksymalnej wadze**: W(sᵢ, e) = sⱼ ⇔ w(sⱼ, e) > w(sₗ, e) dla każdego l.
- **Kiedy zmieniać strategię:** wyniki bardzo słabe lub niespodziewanie dobre; zmiana charakteru treści; mało wiedzy o uczniu; potrzeba wzmocnienia motywacji; potrzeba pomocy tutora-człowieka.

### 3.6 Multimedia i Cognitive Apprenticeship
- Pham (1997): wiele systemów kusi efektami (obrazy, animacje, wideo, dźwięk) kosztem celów dydaktycznych.
- Animacje — do bezpośredniego nauczania, symulacje — do nauki poznawczej, diagramy — do podejmowania decyzji.
- **Cognitive Apprenticeship:** modelowanie (uczeń obserwuje rozwiązanie eksperta) → nauczanie (rozwiązuje z konsultacją) → **zanikanie** (wsparcie maleje wraz z osiągnięciami); przy błędach system pomaga szukać ich źródła.
- Obiekty według potrzeby: obserwacja bierna — tekst, obrazy, animacje, wideo, audio; obserwacja aktywna — interaktywne obrazy i animacje, linki; odkrywanie / naśladowanie — symulacje, diagramy; informacja zwrotna natychmiastowa (rozwiązywanie problemów) i opóźniona (ocena); praktykowanie — symulacje i diagramy w różnych scenariuszach.

### 3.7 Agenci edukacyjni (wirtualni mentorzy)
- Postać (awatar albo tylko komunikaty / głos) z ludzkimi cechami w kontekście społecznym; cechy: autonomia, reaktywność i proaktywność, komunikacja, wnioskowanie, ciągłość działania, osobowość, adaptowalność.
- Ograniczają rezygnację z nauki (znużenie, osamotnienie); cierpliwi, dostępni o każdej porze.
- Role: **przewodnik**; **asystent ucznia** (spersonalizowana zawartość, co do zrobienia / nieukończone, nowości, przypomnienia o terminach); **asystent nauczyciela** (powiadomienia, zadania organizacyjne); współuczeń / kompan (konkurencja, dysonans poznawczy — Duffy); trener / tutor z repozytorium wiedzy (Adele, Steve).
- Reaktywność: rejestrowanie interakcji, wykrywanie schematów i anomalii; wykrywanie nadużywania podpowiedzi i zachęcanie do samodzielności; reakcja na przerwanie nauki i długi przestój.
- Postać dopasowana do wieku („sympatyczny pingwin nie przekona nastolatka”); ważna ciągłość i przewidywalność.

## 4. Artykuły (projekt claude.ai)

**Chęć (Instytut Łączności, 2005) — Inteligentny System Nauczający dla ODL** (`przyklad_systemu.pdf`).
- Porównanie dziedzin SI (systemy ekspertowe, rozmyte, sieci neuronowe, algorytmy genetyczne) → systemy hybrydowe.
- Architektura IEEE LTSC; model ucznia nakładkowy i dewiacyjny; cykl: zadanie → porównanie rozwiązań → informacja zwrotna → aktualizacja modelu → dobór kolejnej partii materiału i sposobu prezentacji.
- **Symulowana populacja uczniów** (rozkład normalny zdolności) do testowania systemu bez prawdziwych uczniów; stan wiedzy jako liczba czwórkowa (poziom 0–3 na jednostkę).
- Kolb: matematyka = wiedza asymilacyjna; strategie: drill & practice, tutorial, symulacja, modelowanie; LASSI.

**Tadeusiewicz — SI w nauczaniu wspomaganym komputerowo** (`Wykorzystanie _AI_2.pdf`).
- Programy traktują każdego ucznia jednakowo; uczniowie nie korzystają z ręcznej parametryzacji.
- Adaptacja zakresu, formy (tekst / obraz / wideo / dźwięk) i sposobu (dedukcyjnie / indukcyjnie).
- **Identyfikacja bierna** z normalnej pracy: czas w typach fragmentów lekcji, korzystanie z linków, wideo, dźwięku (także ponowne odtworzenia); **jakość × czas odpowiedzi → 4 grupy**: zdolni (szybko, dobrze), pilni (wolno, dobrze), „leniwi” (szybko, źle), słabi (wolno, źle).

**Barcz, Piela, Tretiakowa (2013) — model jakości ISN** (`model_jakości_w_inteligentnych_systemach_nauczania.pdf`).
- Jakość ISN zależy od jakości bazy wiedzy; wskaźniki ilościowe (ISO/IEC 25010); dla baz reguł: kompletność `C = N / P` (P = iloczyn liczby termów wejść), minimalna liczba reguł `R = max(p_j)`, niesprzeczność, redundancja. Możliwe do zastosowania w dokumentacji do oceny naszego zbioru reguł.

**Kwaśnicka, Zatwarnicki — BPiT, system dla dzieci z dysleksją** (`zatwarnickikwasnicka.pdf`).
- „Komputerowi przyjaciele” (postaci), polecenia głosowe; 7 zasad interfejsu dla dzieci (prostota, spójność, grafika, obsługa błędów — dziecko poprawia błąd samo, ze wskazaniem drogi); ocena przez szybkie prototypowanie z ekspertami.

**Gardner — test inteligencji wielorakich** (`Free_multiple_intelligences_test_manual_*.pdf`) — tło; poza zakresem systemu.
