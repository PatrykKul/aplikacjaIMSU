# Scenariusz filmu prezentującego IMSU (ok. 11–12 minut)

Film nagrywany **scena po scenie**, z narracją na żywo (mówisz w trakcie klikania). Nieudaną scenę nagrywasz od nowa, a na koniec sklejasz sceny w Clipchampie. Kolejność opowieści: **gość → nauczyciel tworzy kurs → uczeń się uczy → system się dopasowuje → administrator → podsumowanie**.

Pokaz na żywo opisuje `SCENARIUSZ-POKAZU.md`. Ten plik dotyczy tylko filmu i korzysta z tych samych kont i danych demo (`moduly/06-demo.md`). Hasło wszystkich kont: `Demo123!`.

| Konto | W scenach |
|---|---|
| `nauczyciel.demo@imsu.pl` (Anna Nowak) | 3–6 |
| `uczen.nowy@imsu.pl` (Ola Kowalska) | 7–9 |
| `uczen.demo@imsu.pl` (Kuba Wiśniewski) | 10 |
| `admin.demo@imsu.pl` | 11 |

---

## A. Przygotowanie (raz, ok. 45 minut)

### A1. Aplikacja w trybie produkcyjnym

Do nagrania uruchom frontend **po zbudowaniu**, a nie przez `npm run dev`. Wtedy nie ma ikonki narzędzi Next.js w rogu ekranu, a strony otwierają się od razu. Polecenia w `cmd`, po jednym:

Terminal 1, katalog główny repozytorium:
```
docker compose up -d
```

Terminal 2, backend:
```
cd backend
venv\Scripts\python.exe -m app.demo.seed --reset-students
venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
```
Seed musi na końcu wypisać: `profil uczen.demo@imsu.pl: styl V, wagi V 7 / A 8 / K 3, propozycja: A`.

Terminal 3, frontend (jeśli działa `npm run dev`, najpierw zatrzymaj go przez Ctrl+C):
```
cd frontend
npm run build
npm run start
```
Aplikacja: http://localhost:3001. Jeśli `build` się nie uda, nagrywaj na `npm run dev` (ikonka w rogu jest mała i nie przeszkadza w odbiorze).

Terminal 4, backend: zostaw otwarty do resetu kont uczniów między ujęciami (`venv\Scripts\python.exe -m app.demo.seed --reset-students`).

### A2. Ekran i przeglądarka

1. Windows: **Nie przeszkadzać** (Ustawienia → System → Powiadomienia), zamknij komunikatory i pocztę.
2. Większy kursor, żeby było go widać na filmie: Ustawienia → Dostępność → Wskaźnik myszy i dotyk → rozmiar 2–3.
3. Chrome: osobny profil „Nagranie” (prawy górny róg → Dodaj), bez rozszerzeń. Ukryj pasek zakładek (Ctrl+Shift+B) i zostaw jedną kartę.
4. Powiększenie strony **125%** (Ctrl i +), żeby tekst był czytelny na filmie.
5. Na czas nagrania przełącz okno na pełny ekran (**F11**). Znikną wtedy pasek adresu i pasek zadań. Adres wpisujesz przed nagraniem, a przed sceną naciskasz F11.
6. Słuchawki na uszach: lektorka z nagrań nie wejdzie wtedy do mikrofonu jako echo.

### A3. OBS Studio: konfiguracja krok po kroku

1. Pobierz OBS ze strony **obsproject.com** i zainstaluj. Przy pierwszym uruchomieniu kreator zapyta o cel: wybierz **„Optymalizuj do nagrywania”** i zostaw rozdzielczość ekranu.
2. W dolnym panelu **Źródła** kliknij **+**, wybierz **„Przechwytywanie ekranu”** i zatwierdź (OK, OK). Na podglądzie powinien się pojawić Twój pulpit. Przechwytywanie całego ekranu działa pewniej niż przechwytywanie okna Chrome, które bywa czarne.
3. Panel **Mikser audio** ma dwa paski: **„Dźwięk z pulpitu”** (lektorka z nagrań) i **„Mikrofon/Aux”** (Ty). Powiedz coś normalnym głosem: pasek mikrofonu powinien dochodzić do żółtego pola, a nie do czerwonego. Dźwięk pulpitu przycisz suwakiem o mniej więcej 1/4, żeby nie zagłuszał głosu.
4. **Ustawienia → Wyjście → Nagrywanie:** zapamiętaj **ścieżkę nagrań** (np. `Wideo`) i ustaw **format nagrywania MP4** (może być też „Fragmented MP4”).
5. **Ustawienia → Skróty klawiszowe:** „Rozpocznij nagrywanie” = **F9**, „Zatrzymaj nagrywanie” = **F10**. Dzięki temu nie musisz przełączać się na okno OBS w trakcie sceny.
6. **Test (2 minuty):** zminimalizuj OBS, otwórz lekcję z nagraniem, naciśnij F9, powiedz jedno zdanie, odtwórz kilka sekund nagrania lektorki i naciśnij F10. Obejrzyj plik: czy słychać Ciebie, czy słychać lektorkę i czy tekst jest czytelny?

### A4. Kolejność nagrywania (inna niż kolejność w filmie)

Sceny z uczniami zapisują dane (ankieta, wagi, rozwinięte materiały), a reset przywraca obu uczniów naraz. Dlatego nagrywaj w tej kolejności:

1. **Sceny 1–6 i 11** (gość, nauczyciel, administrator).
2. **Scena 10** (Kuba). Przed każdym ujęciem uruchom reset.
3. **Sceny 7–9** (Ola), na samym końcu.

Powtórka ujęcia:
- Scena 4 dodaje załącznik do lekcji. Przed powtórką usuń go w edytorze lekcji (ikona kosza → „Zapisz lekcję”), poza nagraniem.
- Sceny 7–9: reset, a jeśli powtarzasz scenę 8 lub 9, poza nagraniem wypełnij ankietę Oli tak samo jak w scenie 7.
- Scena 10: reset przed każdym ujęciem.

### A5. Jak nagrywać jedną scenę

1. Poza nagraniem zaloguj właściwe konto i otwórz **stronę startową sceny** (podana przy każdej scenie). Logowań nie nagrywamy.
2. F11 (pełny ekran) → **F9** → **2 sekundy ciszy** → mówisz i klikasz według scenariusza → **2 sekundy ciszy** → **F10**.
3. Mów wolniej niż zwykle i kursorem pokazuj to, o czym mówisz. Nie krąż nim po ekranie bez celu.
4. Pomyłka w zdaniu: nie przerywaj nagrania. Zrób 3 sekundy przerwy i powiedz zdanie jeszcze raz. Złą wersję wytniesz w montażu.
5. Tekst narracji to podpowiedź, nie trzeba go recytować słowo w słowo. Najlepiej przeczytaj go raz na głos przed sceną.
6. Po udanym ujęciu zanotuj na kartce: „scena 4 – plik z godz. 14:32 – OK”.

---

## B. Plan filmu

| # | Czas | Konto | Co widać |
|---|---|---|---|
| 0 | 0:00–0:10 | — (plansza) | tytuł, autorzy, przedmiot |
| 1 | 0:10–1:00 | gość | strona startowa: idea V / A / K |
| 2 | 1:00–1:30 | gość | rejestracja: wybór roli |
| 3 | 1:30–2:30 | nauczyciel | „Moje kursy”, edytor kursu |
| 4 | 2:30–4:00 | nauczyciel | edytor lekcji, dodanie załącznika z formami V+K |
| 5 | 4:00–5:00 | nauczyciel | podgląd lekcji, edytor quizu |
| 6 | 5:00–5:45 | nauczyciel | klasy: uczniowie i kurs prywatny |
| 7 | 5:45–6:45 | Ola | wymuszona ankieta VAK (przyspieszona), wynik |
| 8 | 6:45–8:00 | Ola | lekcja pod styl: zwinięte materiały, rozwinięcie |
| 9 | 8:00–9:00 | Ola | quiz, adaptacja wag, ochrona przed nabijaniem |
| 10 | 9:00–10:30 | Kuba | propozycja zmiany stylu, kurs klasy, przełączenie |
| 11 | 10:30–11:00 | administrator | zarządzanie kontami |
| 12 | 11:00–12:00 | — (plansza) | podsumowanie: architektura, inteligencja, jakość |

---

## C. Sceny

### Scena 0 — Plansza tytułowa (montaż, 10 s)

Tekst planszy (dodajesz w Clipchampie, bez nagrywania):

> **IMSU – inteligentny multimedialny system uczący**
> [Imię Nazwisko], [Imię Nazwisko]
> Inteligentne multimedialne systemy uczące · Informatyka UwB · 2026/27

### Scena 1 — Strona startowa (gość, ok. 50 s)

**Start:** http://localhost:3001, niezalogowany, góra strony.

| Akcja | Narracja |
|---|---|
| Kursor na nagłówku „Ucz się po swojemu” | „IMSU to multimedialny system uczący dla uczniów do szesnastu lat. Nauczyciel składa w nim kursy z tekstu, obrazów, nagrań, filmów i kart ćwiczeń, a system decyduje, jak podać lekcję konkretnemu uczniowi.” |
| Kursor po kolei na kartach V, A, K | „Opieramy się na modelu VAK: wzrokowiec uczy się przez patrzenie, słuchowiec przez słuchanie i rozmowę, kinestetyk przez działanie. Każdy materiał w kursie jest oznaczony jedną lub kilkoma z tych form.” |
| Przewiń do „Jak to działa” | „Uczeń zaczyna od ankiety, która daje mu styl i wagi V, A, K. Lekcje są podawane według stylu, a po każdym quizie system koryguje wagi. Gdy wyniki wskazują na inną formę, system proponuje zmianę stylu, ale decyzja należy do ucznia.” |
| Przewiń do pasa „Uczysz innych?” | „Cała ta »inteligencja« to jawne reguły: każda decyzja ma na ekranie uzasadnienie »dlaczego to widzisz«. Pokażę to na kontach demonstracyjnych.” |

### Scena 2 — Rejestracja (gość, ok. 30 s)

**Start:** http://localhost:3001/register.

| Akcja | Narracja |
|---|---|
| Kliknij kafelek „Uczeń”, potem „Nauczyciel” | „System ma trzy role. Przy rejestracji wybiera się ucznia albo nauczyciela i tej roli nie da się później zmienić. Konto administratora tworzy się wyłącznie poleceniem w konsoli serwera.” |
| Kursor na polach formularza (**nie wysyłaj**) | „Mamy przygotowane konta demonstracyjne, więc zaczniemy od nauczycielki, Anny Nowak.” |

### Scena 3 — Nauczyciel: kursy i edytor kursu (ok. 60 s)

**Start:** zalogowana `nauczyciel.demo@imsu.pl`, strona `/dashboard`.

| Akcja | Narracja |
|---|---|
| Kursor na kartach dashboardu, potem „Moje kursy” | „Moduł nauczyciela jest w systemie modułem głównym. Anna ma trzy kursy: matematykę, angielski i programowanie. Dwa są opublikowane, czyli widzi je każdy uczeń, a jeden jest prywatny.” |
| Wejdź w „Matematyka: funkcja liniowa” | „Kurs ma tytuł, krótki opis do katalogu i wstęp, który uczeń czyta na stronie kursu. Wstęp pisze się w edytorze wizualnym, a tekst można wkleić z Worda razem z formatowaniem.” |
| Kursor na przełączniku publikacji | „Tym przełącznikiem nauczyciel publikuje kurs albo wycofuje publikację.” |
| Kursor na liście lekcji (strzałki, zmiana nazwy) | „Niżej są lekcje: można je dodawać, przestawiać i usuwać. Otwórzmy pierwszą.” |
| Kliknij edycję lekcji „Wzór i wykres funkcji liniowej” | — |

### Scena 4 — Nauczyciel: edytor lekcji i nowy załącznik (ok. 90 s)

**Start:** edytor lekcji „Wzór i wykres funkcji liniowej”. Przygotuj okno Eksploratora z plikiem `backend\app\demo\assets\m2_tabela.png` (wybierzesz go w oknie wyboru pliku, więc zapamiętaj ścieżkę).

| Akcja | Narracja |
|---|---|
| Przewiń wolno przez bloki | „Lekcja to ciąg bloków, jak w notatniku. Bloki tekstu widzi każdy uczeń. Załączniki to obraz, film, nagranie, PDF albo link. Przy każdym widać plakietki form: ten film jest wzrokowo-słuchowy, nagranie słuchowe, a karta ćwiczeń kinestetyczna.” |
| Pod ostatnim blokiem kliknij „+ Załącznik” | „Dodam nowy materiał.” |
| Wybierz kafelek „Obraz” | „Najpierw rodzaj materiału.” |
| „Wybierz plik” → `m2_tabela.png`; poczekaj na pasek postępu | „Plik wgrywa się na serwer. System przyjmuje tylko bezpieczne typy plików, do 50 MB.” |
| Tytuł: `Tabela wartości – uzupełnij i narysuj`, opis alternatywny: `Tabela wartości funkcji liniowej` | — |
| Zaznacz formy **V** i **K** | „Najważniejsze jest to: nauczyciel zaznacza, dla jakiego stylu jest materiał. Tabela jest do oglądania i do samodzielnego uzupełniania, więc oznaczam ją jako wzrokową i kinestetyczną.” |
| „Dodaj” → „Zapisz lekcję” | „Nauczyciel nie układa osobnej wersji lekcji dla każdego stylu. Dodaje materiały z oznaczeniem, a o tym, co zobaczy konkretny uczeń, decyduje system.” |

### Scena 5 — Nauczyciel: podgląd i edytor quizu (ok. 60 s)

**Start:** ten sam edytor lekcji (po zapisie).

| Akcja | Narracja |
|---|---|
| „Podgląd” | „W podglądzie nauczyciel widzi wszystkie materiały rozwinięte, a pasek u góry przypomina, że uczeń zobaczy tę lekcję dopasowaną do swojego stylu.” |
| Przewiń na dół do quizu → „Edytuj quiz” | „Na końcu lekcji jest quiz.” |
| Kursor na pierwszym pytaniu, odpowiedziach i zaznaczonej poprawnej | „Pytania są jednokrotnego wyboru, mają trzy albo cztery odpowiedzi, a próg zaliczenia wynosi 70 procent.” |
| Otwórz pole **„Dotyczy materiału”** w pytaniu V (nie zmieniaj wartości, zamknij Escape) | „Każde pytanie jest wspólne albo dotyczy materiału konkretnej formy. Uczeń dostanie pytania wspólne i tylko te o materiałach, z których korzystał. Pytanie o film, którego nie oglądał, byłoby nieuczciwe.” |
| Przewiń przez pytania A i K, potem wróć (bez zapisu) | „Ocenia wyłącznie serwer: przeglądarka ucznia nie dostaje poprawnych odpowiedzi przed wysłaniem quizu.” |

### Scena 6 — Nauczyciel: klasy (ok. 45 s)

**Start:** menu „Klasy”.

| Akcja | Narracja |
|---|---|
| Wejdź w „Klasa 7a” | „Nauczyciel może też tworzyć klasy. W Klasie 7a jest dwoje uczniów i przypisany kurs programowania.” |
| Kursor na plakietce „Prywatny” przy kursie | „Ten kurs jest prywatny: nie ma go w ogólnym katalogu i widzą go tylko uczniowie tej klasy.” |
| „Dodaj ucznia” → wpisz powoli `uczen` | „Ucznia dodaje się po adresie e-mail. Wyniki pojawiają się w trakcie pisania, od trzech znaków. Ci uczniowie są już w klasie.” |
| Zamknij okno; kursor na „Przypisz kurs” (bez klikania) | „Kurs przypisuje się klasie jednym przyciskiem. Teraz zobaczmy system oczami ucznia.” |

### Scena 7 — Ola: wymuszona ankieta i wynik (ok. 60 s po przyspieszeniu)

**Start:** zalogowana `uczen.nowy@imsu.pl`. Po zalogowaniu system sam przenosi na `/survey`, więc nagranie zaczynasz na ankiecie.

| Akcja | Narracja |
|---|---|
| Kursor na pasku postępu ankiety | „To Ola, nowa uczennica. Zaraz po zalogowaniu system przeniósł ją do ankiety VAK.” |
| Kliknij w menu „Kursy” → wraca ankieta | „Bez ankiety nie wejdzie do żadnej lekcji. Aplikacja kieruje ją tu z każdej strony, a serwer bez ankiety nie poda lekcji ani quizu.” |
| Wypełnij 20 pytań **w milczeniu** (fragment przyspieszysz w montażu ×4): w każdym pytaniu wybierz odpowiedź o **słuchaniu, rozmowie albo czyimś wyjaśnieniu**, a w 3–4 pytaniach inną odpowiedź | — (ewentualnie na początku: „Ankieta ma 20 pytań, a odpowiedzi są w każdym pytaniu w innej kolejności.”) |
| „Zobacz mój styl uczenia się” | „Punkty liczy serwer. Ola wyszła słuchowcem: punkty V, A i K stają się jej wagami startowymi. To tylko punkt wyjścia, dalej system patrzy na wyniki.” |

Sprawdź, czy wynik to **sam słuchowiec**. Jeśli wyszedł styl mieszany, zrób reset i nagraj ponownie.

### Scena 8 — Ola: lekcja pod styl (ok. 75 s)

**Start:** strona kursu „Matematyka: funkcja liniowa” (wejście: „Przejdź do kursów” → kurs).

| Akcja | Narracja |
|---|---|
| Kliknij lekcję „Wzór i wykres funkcji liniowej” | „Ola otwiera tę samą lekcję, którą przed chwilą edytowała nauczycielka.” |
| Kursor na ramce „Lekcja dopasowana do stylu…” | „Na górze system wyjaśnia, dlaczego lekcja wygląda tak, a nie inaczej: styl słuchowy, bo tak wyszło w ankiecie, z punktami. Cztery materiały dla innych stylów są zwinięte.” |
| Odtwórz 5–6 s nagrania „Posłuchaj: jak czytać wzór…” | — (niech wybrzmi lektorka) |
| Kursor na filmie i „Ćwiczeniu z lektorem” | „Rozwinięte są materiały słuchowe: nagrania z lektorką i film z narracją.” |
| Kursor na zwiniętej karcie „Tabela wartości” | „Tu jest tabela, którą przed chwilą dodała nauczycielka. Jest wzrokowo-kinestetyczna, więc u słuchowca jest zwinięta. Nic nie jest ukryte: Ola widzi, że materiał istnieje, i może go otworzyć.” |
| „Pokaż materiał” przy **„Karta ćwiczeń: narysuj wykres”** (K) | „Ola otwiera kartę ćwiczeń, która jest materiałem kinestetycznym. To ważny sygnał: system zapisuje, z czego uczeń naprawdę korzysta.” |

### Scena 9 — Ola: quiz i adaptacja (ok. 60 s)

**Start:** ta sama lekcja, przewinięta do karty „Sprawdź się”.

| Akcja | Narracja |
|---|---|
| Kursor na plakietkach pytań | „Quiz ma trzy pytania wspólne, pytanie o nagranie, bo Ola jest słuchowcem, i pytanie kinestetyczne, bo przed chwilą otworzyła kartę ćwiczeń. Gdyby jej nie otworzyła, tego pytania by nie było.” |
| Odpowiedz: *prosta*; *punkt przecięcia z osią y*; **„4” (celowo źle)**; *b to start, a to krok*; *1 w prawo, 2 w górę* → „Sprawdź odpowiedzi” | — |
| Kursor na zielonych i ceglastych odpowiedziach | „Poprawne odpowiedzi są na zielono. Przy błędnej Ola widzi, jaka odpowiedź była dobra.” |
| Kursor na ramce adaptacji | „80 procent, czyli quiz zaliczony. System podał uzasadnienie i podniósł wagi tych form, z których Ola korzystała w tej lekcji: słuchowej i kinestetycznej.” |
| „Rozwiąż jeszcze raz” → te same odpowiedzi → „Sprawdź odpowiedzi” | „Gdy rozwiąże quiz drugi raz, wagi się nie zmieniają. W lekcji liczy się tylko pierwszy sukces i pierwsza porażka, więc wag nie da się nabić klikaniem.” |

### Scena 10 — Kuba: propozycja zmiany stylu (ok. 90 s)

**Start:** reset → zalogowany `uczen.demo@imsu.pl`, strona „Mój styl” (`/profile`).

| Akcja | Narracja |
|---|---|
| Kursor na stylu i źródle | „To Kuba. W ankiecie wyszedł wzrokowcem. Na potrzeby pokazu przygotowaliśmy mu historię czterech quizów: jeden zaliczył, trzy oblał, a uczył się z materiałów wzrokowych.” |
| Kursor na paskach wag („Jak system Cię widzi”) | „Każda porażka obniżała wagę V. Teraz najwyższą wagę ma forma słuchowa.” |
| Kursor na banerze propozycji i „Dlaczego to widzisz” | „Gdy inna forma jest jedynym liderem wag, system proponuje zmianę stylu i podaje uzasadnienie z wagami. Nie zmienia stylu sam: decyduje uczeń. Jeśli Kuba odrzuci propozycję, ona nie wróci, a gdyby wybrał styl ręcznie, propozycji w ogóle by nie było.” |
| Menu „Kursy” | „Na razie Kuba się nie decyduje. W katalogu nie ma kursu programowania, bo jest prywatny.” |
| „Moje klasy” → „Klasa 7a” | „Kuba widzi go w swojej klasie, razem z nauczycielką i jej adresem e-mail do kontaktu.” |
| Kurs „Programowanie: pętle w Pythonie” → lekcja „Pętla for” | „Jako wzrokowiec ma rozwinięty schemat blokowy, przykład kodu i film, a nagranie jest zwinięte.” |
| Nad lekcją kliknij **„Przełącz”** w banerze | „Teraz Kuba przyjmuje propozycję…” |
| Przewiń przez lekcję i do quizu | „…i lekcja od razu się zmienia: nagranie jest rozwinięte, materiały wzrokowe zwinięte, a w quizie jest pytanie o nagranie. Ramka mówi, że styl zmieniono po propozycji opartej na wynikach quizów.” |

### Scena 11 — Administrator (ok. 30 s)

**Start:** zalogowany `admin.demo@imsu.pl`, strona „Użytkownicy”.

| Akcja | Narracja |
|---|---|
| Przełącz zakładki „Nauczyciele” / „Uczniowie” | „Administrator zarządza kontami nauczycieli i uczniów.” |
| „Dodaj” → kursor na polach → „Anuluj” | „Może zakładać konta i je edytować…” |
| Kursor na przycisku blokady (bez klikania) | „…a zamiast usuwać konto, blokuje je. Zablokowany użytkownik traci dostęp od razu, a jego historia nauki zostaje.” |

### Scena 12 — Podsumowanie (montaż, ok. 60 s)

Plansza w Clipchampie, a narrację nagrywasz osobno: w OBS samym mikrofonem albo w Clipchampie przyciskiem „Nagraj” (nagrywanie dźwięku). Opcjonalnie wstaw kilka sekund terminala z `venv\Scripts\python.exe -m pytest`, przyspieszone i zakończone wynikiem `349 passed`.

Tekst planszy:

> **Architektura:** Next.js · FastAPI · PostgreSQL — modularny monolit: konta, kursy i klasy, treść, styl uczenia się, quizy
> **Inteligencja:** ankieta VAK → styl i wagi · lekcja podana według stylu · quiz dobrany do materiałów · wagi ±1 po quizie · propozycja zmiany stylu z uzasadnieniem
> **Jakość:** 349 testów backendu · ocenianie tylko na serwerze · reguły jako czyste funkcje

Narracja:
„Podsumowując: nauczyciel składa kurs z materiałów oznaczonych formami V, A i K, a system decyduje, jak podać lekcję uczniowi. Styl z ankiety jest tylko punktem startowym. Potem system patrzy, z czego uczeń korzysta i jak mu idzie w quizach, i na tej podstawie proponuje zmianę stylu. Wszystkie reguły są jawne i mają uzasadnienie widoczne dla ucznia. Działają bez zewnętrznego modelu AI i są pokryte testami. Świadomie traktujemy styl VAK ostrożnie: badania nad dopasowaniem nauczania do stylu są niejednoznaczne, dlatego styl można zawsze zmienić, a system sprawdza go na wynikach. Dalsze kroki to baza pytań z losowaniem, panel nauczyciela ze stylami uczniów i wirtualny mentor. Dziękujemy.”

---

## D. Montaż w Clipchampie (ok. 1 godzina)

Clipchamp jest wbudowany w Windows 11 (menu Start → „Clipchamp”). Nazwy przycisków mogą się nieznacznie różnić.

1. **Nowy film** → przeciągnij udane pliki z folderu nagrań OBS do panelu „Twoje multimedia”.
2. Przeciągnij je na **oś czasu** w kolejności scen 1–11.
3. **Przycinanie:** chwyć lewą lub prawą krawędź klipu na osi i przeciągnij, żeby uciąć ciszę na początku i końcu (zostaw około pół sekundy).
4. **Wycinanie pomyłek:** ustaw wskaźnik na początku złego fragmentu → zaznacz klip → **S** (podziel) → wskaźnik na końcu fragmentu → **S** → zaznacz środkowy kawałek → **Delete**. Luka zamyka się sama.
5. **Przyspieszenie ankiety (scena 7):** wydziel podziałem fragment wypełniania (bez narracji), zaznacz go → panel po prawej **„Szybkość”** → **4×**.
6. **Plansze:** zakładka **„Tekst”** albo **„Tytuły”** → przeciągnij szablon na początek (scena 0) i na koniec (scena 12) → wpisz tekst z punktów C/0 i C/12. Tło planszy w kolorze indygo (`#4f46e5` albo zbliżonym) pasuje do aplikacji.
7. **Podpisy scen (opcjonalnie):** mały tekst w rogu przez pierwsze 3 sekundy sceny, np. „Nauczyciel: edytor lekcji”, „Uczeń: adaptacja po quizie”.
8. **Dźwięk:** odsłuchaj całość w słuchawkach. Jeśli któraś scena jest cichsza, zaznacz klip → „Audio” → zwiększ głośność.
9. **Eksport:** przycisk **„Eksportuj”** → **1080p** → zapis na dysk. Sprawdź długość: 10–12 minut.

---

## E. Lista kontrolna przed oddaniem

- [ ] Film trwa 10–12 minut, jest w 1080p i słychać zarówno narrację, jak i lektorkę.
- [ ] Widać wszystkie trzy role oraz pięć elementów „inteligencji”: ankietę → styl, zwinięte i rozwinięte materiały, pytanie dodane po rozwinięciu materiału, zmianę wag po quizie bez nabijania oraz propozycję zmiany stylu z uzasadnieniem.
- [ ] Na ekranie nie ma powiadomień ani prywatnych kart, a hasła nie są widoczne.
- [ ] Po nagraniu (opcjonalnie) usuń z lekcji „Wzór i wykres” dodaną „Tabelę wartości” i uruchom `seed --reset-students`, żeby dane demo wróciły do stanu ze `SCENARIUSZ-POKAZU.md`.
