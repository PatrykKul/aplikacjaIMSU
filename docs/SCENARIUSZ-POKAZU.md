# Scenariusz pokazu IMSU v3 (12–15 minut)

Aplikacja: http://localhost:3001 (backend: http://localhost:8001). Hasło wszystkich kont demo: `Demo123!`.
Reguły R1–R11 opisuje `docs/08-praca-biezaca.md`, a ich kod jest w `backend/app/modules/learning_style/rules.py`. Liczby w tym scenariuszu pochodzą z seeda; sprawdza je test `backend/tests/demo/test_seed.py`.

| Konto | Kto | Stan startowy (po `--reset-students`) |
|---|---|---|
| `uczen.nowy@imsu.pl` | Ola Kowalska | bez ankiety |
| `nauczyciel.nowy@imsu.pl` | Piotr Zieliński | nauczyciel, konto czeka na zatwierdzenie |
| `admin.demo@imsu.pl` | Adam Admin | administrator |
| `nauczyciel.demo@imsu.pl` | Anna Nowak | autorka 3 kursów po 4 lekcje; w Matematyce 7 uczniów i 1 prośba o zapis |
| `uczen.zapis@imsu.pl` | Zosia Mazur | ankieta A 50 / V 30 / K 20, styl słuchowy; prośba o zapis do Matematyki |
| `uczen.demo@imsu.pl` | Kuba Wiśniewski | styl wzrokowy, V 45 / A 40 / K 15; Matematyka 2/4, lekcja 3 dostępna („tuż przed sugestią”) |
| `uczen.zmiana@imsu.pl` | Marta Lewandowska | styl wzrokowy po zmianie z kinestetycznego; okres próbny: „Zmiana pomogła: średnia 40% → 90%” |
| `uczen1…6@imsu.pl` | klasa (Antoni, Julia, Szymon, Lena, Filip, Maja) | wyniki w Matematyce; Julia ma otwartą propozycję zmiany V → A |

## Przygotowanie (10 minut przed pokazem)

1. Uruchom bazę i aplikację (sekcja „Uruchomienie od zera” na końcu, jeśli to nowa maszyna):
   ```powershell
   docker compose up -d                                   # w katalogu aplikacja\
   cd backend
   .\venv\Scripts\python.exe -m uvicorn app.main:app --port 8001
   # drugi terminal: cd frontend; npm run dev             # http://localhost:3001
   ```
2. Przywróć wszystkie konta demo do stanu startowego (kursy zostają):
   ```powershell
   cd backend
   .\venv\Scripts\python.exe -m app.demo.seed --reset-students
   ```
   Na końcu wypisuje się „Stan kont”. Sprawdź dwie linie:
   - `uczen.demo@imsu.pl: styl V, V 45 / A 40 / K 15, Matematyka 2/4`
   - `Matematyka: funkcja liniowa: V 60% (3 ucz.) · A 86% (3 ucz.) · K 70% (2 ucz.)`
3. Otwórz dwie sesje przeglądarki: zwykłe okno (uczniowie) i okno incognito (nauczyciel i administrator). Dzięki temu nie trzeba się ciągle wylogowywać.
4. Sprawdź dźwięk: zaloguj się jako `nauczyciel.demo` → Matematyka → lekcja 1 → „Podgląd” → wersja słuchowa → odtwórz kilka sekund nagrania. Nagrania to gotowe pliki MP3 (głosy neuronowe), więc działają bez internetu.
5. Miej pod ręką klucz odpowiedzi do lekcji 3 Matematyki (na końcu dokumentu). Kuba musi na żywo trafić dokładnie 2 z 5, a potem 4 z 5.

## Przebieg

### 0:00–1:00 Wstęp
Pokaż stronę startową (okno bez logowania).

Co powiedzieć:
- „IMSU to platforma kursów dla uczniów do 16 lat. Każda lekcja ma tę samą treść w trzech wersjach: do oglądania (V), do słuchania (A) i do zrobienia samodzielnie (K). Uczeń uczy się zawsze w **jednej** formie naraz.”
- „System sprawdza wynikami, czy forma działa. Gdy uczniowi nie idzie, proponuje inną **z argumentami z danych**. Każdą decyzję zapisuje w dzienniku, a o zmianie stylu na stałe decyduje uczeń.”
- „Każda reakcja systemu wynika z reguły w czystej funkcji (R1–R11) i niesie liczby, z których wynika. Nie ma decyzji »z niczego« ani modelu językowego w środku.”

### 1:00–3:00 Nowy uczeń: ankieta, procenty, katalog, prośba (`uczen.nowy`) — R1
1. „Zaloguj się” → `uczen.nowy@imsu.pl`. Kliknij „Kursy”: system kieruje na ankietę.
   - „Bez ankiety nie ma stylu, więc serwer nie wyda lekcji ani quizu (`403 SURVEY_REQUIRED`).”
2. Wypełnij ankietę (20 pytań; wybieraj głównie odpowiedzi „słuchowe”, np. 11–12 razy). Kliknij „Zobacz wynik”.
3. Ekran wyniku: procenty V / A / K na paskach i styl.
   - **R1:** „Punkty z ankiety zamieniamy na procenty, które sumują się do 100, a każda forma ma co najmniej 5%. Na przykład V 6 / A 10 / K 4 daje A 50 / V 30 / K 20.”
   - „Przy remisie uczeń sam wybiera jeden z remisujących stylów (»Wybieram ten styl«). Styl jest zawsze jeden.”
4. „Przejdź do kursów” → **Katalog**: tytuł, opis, nauczyciel, liczba lekcji. Przy „Angielski: Present Perfect” kliknij „Zapisz się”. Pojawi się „Prośba wysłana – czeka na nauczyciela”.
   - „Kursy nie są otwarte dla wszystkich. Uczeń prosi o zapis, a nauczyciel przyjmuje go albo odrzuca.”

### 3:00–3:45 Nauczyciel czeka na zatwierdzenie (`nauczyciel.nowy`)
1. Okno incognito → `nauczyciel.nowy@imsu.pl`. Ekran: **„Konto czeka na zatwierdzenie przez administratora”**.
   - „Każdy może się zarejestrować jako nauczyciel, ale tworzyć kursy może dopiero po zatwierdzeniu konta. Serwer odrzuca każde żądanie nauczyciela z kodem `403 TEACHER_NOT_APPROVED`.”
2. „Wyloguj”.

### 3:45–4:30 Administrator zatwierdza (`admin.demo`)
1. `admin.demo@imsu.pl` → „Użytkownicy” → zakładka „Nauczyciele” → filtr **„Czekające (1)”** → przy Piotrze „Zatwierdź”.
   - „Kolumna »Konto« pokazuje stan tekstem: Zatwierdzone / Czeka na zatwierdzenie / Odrzucone.”
2. Opcjonalnie: zaloguj się ponownie jako Piotr. Widać już „Moje kursy” (puste).

### 4:30–7:00 Nauczycielka: lekcja w 3 wersjach, gotowość, prośby, panel kursu (`nauczyciel.demo`) — R11
1. `nauczyciel.demo@imsu.pl` → „Moje kursy”: 3 kursy po 4 opublikowane lekcje. Przy Matematyce widać prośbę Zosi, przy Angielskim świeżą prośbę Oli.
2. Matematyka → lekcja „Miejsce zerowe” → **edytor lekcji** z zakładkami „Zarys i wnioski”, „Wzrokowa (V)”, „Słuchowa (A)”, „Kinestetyczna (K)”, „Quiz (pula)”.
   - V: tekst, wykres miejsca zerowego i schemat przypadków (PNG).
   - A: krótki opis i nagranie rozmowy nauczycielki z Markiem (MP3, ok. 2 min).
   - K: instrukcja „1. Zapisz… 2. Oblicz…” i karta zadania PDF (ostatnia strona zawiera odpowiedzi).
   - „Quiz (pula)”: 8 pytań, przy każdym poprawna odpowiedź i **wyjaśnienie**; licznik „w puli (min. 5)”.
   - „Wszystkie trzy wersje uczą tego samego, a pytania z puli dotyczą wspólnej treści. Uczeń z każdej wersji musi umieć na nie odpowiedzieć.”
3. Panel **gotowości** (**R11**): lekcja jest kompletna, więc widać „Wycofaj publikację”.
   - „Lekcji nie da się opublikować, dopóki czegoś brakuje: zarysu, wniosków, obrazu w wersji V, nagrania i opisu w A, instrukcji i karty PDF w K albo 5 pytań w puli.”
   - „Opublikowana lekcja nie może stać się niekompletna: zapis, który usunąłby np. kartę PDF, serwer odrzuci (`409 PUBLISHED_LESSON_INCOMPLETE`). Wszystkie 12 lekcji demo opublikował seed przez ten sam moduł (`authoring`), więc każda przeszła tę kontrolę.”
4. Wróć do kursu → **„Panel kursu”**:
   - **„Prośby o zapis (1)”**: Zosia Mazur → „Przyjmij”.
   - **Uczniowie**: tabela ze stylem, procentami, postępem, średnią i ostatnią aktywnością. Julia Kamińska ma otwartą propozycję V → A.
   - **„Skuteczność form”** (policzone wyniki w tym kursie):

     | Forma | Średnia | Policzone wyniki | Podejścia | Uczniowie |
     |---|---|---|---|---|
     | V | 60% | 5 | 6 | 3 |
     | A | 86% | 7 | 7 | 3 |
     | K | 70% | 4 | 4 | 2 |

     „W tym kursie najlepiej wypada forma słuchowa. To dane tylko z tego kursu i tylko z pierwszych podejść w danej formie.”
   - **„Rozkład stylów”**: V 3 · A 2 · K 2.

### 7:00–7:45 Podpowiedź z kursu (`uczen.zapis`) — R8, R10
1. Zwykłe okno → wyloguj Olę → `uczen.zapis@imsu.pl` → „Kursy” → „Moje kursy” → Matematyka.
2. Ramka „Podpowiedź z kursu”: **„W tym kursie najlepiej wypada forma słuchowa (średnio 86%, 3 uczniów)”**.
   - **R8:** „Zosia nie ma jeszcze żadnego wyniku w tym kursie, więc system pokazuje, jak radzą sobie inni. Liczą się tylko formy, w których uczyło się co najmniej 2 uczniów. To tylko informacja: system niczego nie zmienia sam.”
3. Pokaż „Streszczenie kursu”: ponumerowane lekcje z zarysami. Lekcja 1 jest „Dostępna”, lekcje 2–4 „Zablokowana” z napisem „Najpierw zalicz lekcję …” (**R10**).

### 7:45–11:00 Sugestia, zmiana formy i propozycja (`uczen.demo`) — R2, R5, R9, R3, R6, R7
1. `uczen.demo@imsu.pl` → „Mój styl”: styl wzrokowy, V 45 / A 40 / K 15. Przy formach: V „potwierdzona wynikami”, A i K „tylko z ankiety”.
   - „Kuba ma za sobą 2 lekcje Matematyki: lekcję 1 w V na 80%, lekcję 2 w V na 40% (dostał wtedy sugestię A, ale ją zignorował) i powtórkę lekcji 2 w V na 80%. Powtórka zaliczyła lekcję, ale nie zmieniła procentów.”
2. „Kursy” → Matematyka: lekcje 1–2 zaliczone, lekcja 3 „Dostępna”, lekcja 4 zablokowana. Otwórz lekcję 3 „Miejsce zerowe”.
   - Pasek nad treścią: **„Przerabiasz tę lekcję w formie: Wzrokowej (V)”**. Widać „Zarys”, wersję wzrokową (tekst i wykresy) i „Wnioski”.
3. „Sprawdź się”: 5 pytań wylosowanych z puli 8. Odpowiedz **poprawnie na 2** (klucz na końcu) → „Sprawdź”.
   - Wynik: „Jeszcze nie: 2 z 5 (40%) – zaliczenie od 70%”. Przy każdym pytaniu poprawna odpowiedź z wyjaśnieniem.
   - „Co to zmieniło”: **„Wzrokowe 45% → 35%”**.
     **R2:** „Pierwsze podejście w danej formie w tej lekcji zmienia procent formy o 10 punktów. Pozostałe formy dzielą resztę proporcjonalnie, więc teraz jest V 35 / A 47 / K 18.”
   - Ramka sugestii (**R5**): **„Spróbuj tej lekcji w formie słuchowej. Wzrokowe: ten quiz 40%, poprzednia lekcja 40%. Słuchowe były drugie w Twojej ankiecie (40%), nie mamy jeszcze o nich wyników – warto sprawdzić.”**
     „Kuba nie ma jeszcze zaliczonej formy innej niż V, więc system sięga po drugą formę z ankiety. Uzasadnienie niesie liczby.”
4. Kliknij **„Przerób tę lekcję w formie słuchowej”**. Pasek pokazuje teraz „Słuchowej (A)”. Odtwórz kilka sekund nagrania.
   - „Wybór formy dotyczy tylko tej lekcji i trafia do dziennika. Styl Kuby się nie zmienił.”
5. „Sprawdź się” (nowe losowanie: najpierw pytania spoza poprzedniego zestawu, **R9**). Odpowiedz **poprawnie na 4** → „Sprawdź”.
   - „Zaliczone: 4 z 5 (80%)”. „Co to zmieniło”: **„Słuchowe 47% → 57% · Lekcja 4 odblokowana”** (**R2**, **R10**).
   - Baner propozycji (**R6**): **„Lepiej idzie Ci w formie słuchowej – przełączyć styl na stałe?”**, „Dlaczego: Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%”.
     „Słuchowa jest teraz **potwierdzona wynikami** (**R3**: zaliczenie w tej formie) i ma wyższy procent niż styl Kuby (57 wobec 28). Forma tylko z ankiety nigdy nie dostaje propozycji.”
6. Kliknij **„Przełącz na stałe”**.
   - **R7:** „Zaczyna się okres próbny: 2 lekcje w nowej formie. Średnia przed zmianą to 40%, czyli 2 ostatnie policzone wyniki w V. Po 2 lekcjach system porówna średnie. Wzrost o co najmniej 10 punktów oznacza, że zmiana pomogła. Spadek o 10 lub więcej oznacza propozycję powrotu.”
   - „Przy zmianie stylu system czyści wybory formy w niezaliczonych lekcjach. Kuba miał wybór tylko w lekcji 3, a tę już zaliczył, więc nic nie zostało wyczyszczone.”
   - „Mój styl” pokazuje styl słuchowy i „0 z 2 lekcji w nowej formie”.

### 11:00–12:30 Okres próbny, wykres, dziennik (`uczen.zmiana`) — R7, R4
1. `uczen.zmiana@imsu.pl` → „Moje postępy”:
   - **„Procenty form w czasie”**: wykres od ankiety (K 50 / V 35 / A 15) do stanu obecnego (V 72 / A 9 / K 19); pod wykresem tabela tych samych danych.
   - **„Wyniki lekcji”**: Programowanie. Lekcja 1: K 40% (niezaliczone), potem V 80%. Lekcja 2: V 100%. Lekcja 3: V 80%.
   - **„Dziennik decyzji”** (od najnowszego): koniec okresu próbnego **„Zmiana pomogła: średnia 40% → 90%”**, rozpoczęcie okresu próbnego („Średnia przed zmianą: 40%.”), przyjęta propozycja K → V, propozycja („Kinestetyczne: 1 lekcja, średnio 40% · Wzrokowe: 1 lekcja, średnio 80%”), zmiana formy lekcji według sugestii i sugestia („Kinestetyczne: ten quiz 40%. Wzrokowe miały w ankiecie 35%, nie mamy jeszcze o nich wyników – warto sprawdzić.”).
   - „Każda decyzja ma swoje dane. To jest odpowiedź na pytanie »dlaczego system tak zrobił«.”
2. Opcjonalnie, na żywo (**R4**): Programowanie → lekcja 4 „break i continue” (w V) → odpowiedz poprawnie na 4 z 5. Pojawi się pochwała **„4 lekcje z rzędu zaliczone w formie wzrokowej, średnio 85%”** i „Kurs ukończony”.
   - „Po lekcji 3 pochwała brzmiała: 3 lekcje z rzędu, średnio 87%. Seria liczy tylko policzone zaliczenia w tej samej formie.”

### 12:30–13:30 Nauczycielka: szczegóły ucznia (`nauczyciel.demo`)
1. Okno incognito → „Panel kursu” Matematyki → w tabeli „Uczniowie” kliknij Kubę.
2. Widać to samo co w „Moich postępach” Kuby: procenty form, procenty w czasie, wyniki lekcji w tym kursie, a w dzienniku decyzji świeżą sugestię, zmianę formy, propozycję i jej przyjęcie z liczbami.
   - „Nauczyciel widzi uzasadnienia, a nie tylko wyniki. Wie, dlaczego Kuba uczy się teraz w formie słuchowej i co system sprawdzi w okresie próbnym.”
3. Wróć do „Skuteczność form”: po pokazie forma A ma 8 policzonych wyników ze średnią 85%, a V 6 wyników ze średnią 57%.

### 13:30–15:00 Podsumowanie i pytania
- **Architektura:** FastAPI + PostgreSQL + Next.js. Moduły backendu: `identity` (konta, zatwierdzanie), `curriculum` (kursy, lekcje, zapisy, blokada), `content` (3 wersje lekcji, pliki), `learning_style` (ankieta, reguły R1–R8, dziennik, statystyki), `assessment` (pula, losowanie, ocena), `authoring` (gotowość i publikacja).
- **Ocena tylko na serwerze:** klucz nie trafia do przeglądarki, a wynik idzie jednym wywołaniem `record_quiz_result` przez reguły R2–R7.
- **Dane demo:** historie uczniów powstały przez prawdziwe serwisy, więc dziennik i procenty są prawdziwe. Seed tylko przesunął daty o dni wstecz.

## Pytania, które mogą paść

- **Skąd system wie, że forma działa?** Z wyników quizów: liczymy średnią policzonych wyników w każdej formie i to, czy forma ma choć jedno zaliczenie (**R3**). Propozycję zmiany na stałe dostaje tylko forma potwierdzona wynikami, nigdy forma tylko z ankiety (**R6**). Po zmianie okres próbny porównuje średnie przed i po (**R7**).
- **Dlaczego tylko jeden styl naraz?** Żeby dało się zmierzyć, co działa. Gdyby uczeń dostawał wszystko naraz, wynik quizu nie mówiłby nic o formie. Jedna forma na lekcję daje czysty pomiar: wynik w formie X. Uczeń zawsze może przerobić konkretną lekcję w innej formie, a ten wybór też jest zapisany.
- **Dlaczego +10 tylko za pierwsze podejście w formie?** Inaczej procenty dałoby się nabić powtarzaniem tego samego quizu. Kolejne podejścia w tej samej formie są zapisywane i mogą zaliczyć lekcję, ale procentów nie zmieniają (**R2**: „To kolejne podejście w tej formie – procenty bez zmian”).
- **Czy druga szansa w innej formie nie jest łatwiejsza?** Jest. Uczeń zna już część pytań i wyjaśnienia, więc +10 dla formy drugiej szansy może zawyżać jej procent. Łagodzą to trzy rzeczy: przy powtórce losujemy w pierwszej kolejności inne pytania (pula 8, zestaw 5: 3 nowe i 2 z poprzedniego, **R9**), liczy się tylko pierwsze podejście w każdej formie, a propozycja na stałe wymaga potwierdzenia formy. Mówimy o tym otwarcie jako o znanym ograniczeniu.
- **Przecież teoria stylów VAK jest krytykowana?** Tak. Pashler i in. (2008) pokazali, że brakuje dowodów na *meshing*, czyli na to, że dopasowanie formy do zadeklarowanego stylu poprawia wyniki. Dlatego ankieta jest tu tylko **hipotezą startową**. System nie zakłada, że jest prawdziwa: sprawdza ją wynikami ucznia, pokazuje dane, a decyzję o zmianie stylu zostawia uczniowi. Okres próbny sprawdza, czy zmiana rzeczywiście pomogła.
- **Czy uczeń może oszukać wynik?** Nie. Pytania losuje serwer i zapisuje zestaw, odpowiedzi ocenia serwer, klucz nie trafia do przeglądarki, a powtórki nie zmieniają procentów.
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
`.\venv\Scripts\python.exe -m app.demo.seed --reset-students`: wszystkie konta wracają do stanu startowego (Piotr znów czeka na zatwierdzenie, Zosia znów prosi o zapis, Kuba znów jest „tuż przed sugestią”). Kursy i ich treść zostają.

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
.\venv\Scripts\python.exe -m app.demo.seed             # konta, 3 kursy (43 pliki), historie uczniów
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --port 8001

# 3. Frontend (drugi terminal)
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev                                            # http://localhost:3001
```

Uwagi:
- Seed jest idempotentny: drugie uruchomienie niczego nie zmienia i wypisuje „bez zmian”. `--reset-students` przywraca stan startowy wszystkich kont demo. `--refresh-demo-media` wgrywa ponownie nagrania MP3 po ich ponownym wygenerowaniu.
- Zasoby demo (PNG, PDF, MP3) leżą w `backend/app/demo/assets/`. Tworzą je generatory `app.demo.generate_assets` i `app.demo.generate_audio`, uruchamiane w osobnym venvie narzędziowym (Pillow, edge-tts, imageio-ffmpeg; nagrania wymagają internetu).
- Komendy uruchamiaj przez `python -m ...`. Pliki `.exe` w `venv\Scripts` przestają działać po przeniesieniu folderu z projektem.
- Sprawdzenie kodu: w `backend`: `python -m pytest`, `python -m ruff check .`; we `frontend`: `npm run lint`, `npm run build`.
