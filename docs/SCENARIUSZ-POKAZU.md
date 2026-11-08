# Scenariusz pokazu IMSU (ok. 10 minut)

Prezentacja: czwartek 12.11.2026. Aplikacja: http://localhost:3001. Hasło wszystkich kont demo: `Demo123!`.

| Konto | Do czego |
|---|---|
| `uczen.nowy@imsu.pl` (Ola Kowalska) | nowy uczeń: wymuszenie ankiety, styl, lekcja pod styl, quiz |
| `uczen.demo@imsu.pl` (Kuba Wiśniewski) | uczeń z historią quizów: propozycja zmiany stylu |
| `nauczyciel.demo@imsu.pl` (Anna Nowak) | kursy, materiały V/A/K, edytor quizu |
| `admin.demo@imsu.pl` | zarządzanie kontami (opcjonalnie) |

## Przed pokazem (5 minut wcześniej)

1. Uruchom aplikację (sekcja „Uruchomienie od zera”, jeśli to nowa maszyna).
2. Przywróć konta demo do stanu startowego:
   ```powershell
   cd backend
   .\venv\Scripts\python.exe -m app.demo.seed --reset-students
   ```
   Na końcu musi się wypisać: `profil uczen.demo@imsu.pl: styl V, wagi V 7 / A 8 / K 3, propozycja: A`.
3. W Chrome otwórz dwie karty: zwykłą i incognito (dwie sesje naraz, bez ciągłego wylogowywania).
4. Sprawdź dźwięk: w dowolnej lekcji kliknij „Posłuchaj”. Lektor korzysta z głosu systemu (Windows: „Paulina”), a film ma własną ścieżkę dźwiękową.

## Przebieg

### 0:00–1:00 Wstęp: co to jest i gdzie jest „inteligencja”

Co powiedzieć:
- „IMSU to platforma kursów, która dopasowuje **sposób podania materiału** do ucznia: na starcie według ankiety VAK, a potem według tego, jak uczniowi faktycznie idzie w quizach.”
- „Rdzeń jest **regułowy i wyjaśnialny**: każda decyzja systemu ma widoczne uzasadnienie »dlaczego to widzisz«. Nie zależy od zewnętrznego modelu AI, działa offline i jest pokryty testami (272 testy backendu).”
- Uczciwie: „Teoria stylów VAK jest w badaniach dyskusyjna, dlatego styl z ankiety to tylko **punkt startowy**. Dalej system patrzy na wyniki, a uczeń zawsze może zmienić styl sam.”

### 1:00–3:00 Nowy uczeń: wymuszona ankieta i styl (`uczen.nowy`)

1. Zaloguj się jako `uczen.nowy@imsu.pl`. System **od razu przenosi na ankietę**.
2. Kliknij „Kursy” w menu: znowu ankieta. „Bez ankiety uczeń nie wejdzie do materiałów. Pilnuje tego też serwer: API zwraca `403 SURVEY_REQUIRED`, więc ręczny adres nic nie da.”
3. Zaznacz odpowiedzi (20 pytań; dla stylu słuchowego wybieraj odpowiedzi typu „słuchasz…”, „opowiada…”). Pokaż pasek postępu.
   - „Odpowiedzi są w każdym pytaniu w innej kolejności, a przeglądarka nie dostaje klucza (który styl daje odpowiedź). Punkty liczy serwer.”
4. „Zobacz mój styl uczenia się” → **ekran wyniku**: styl dominujący, opis i punkty V/A/K na paskach. Przy remisie powstaje styl mieszany (np. wzrokowiec + słuchowiec).

### 3:00–5:30 Lekcja pod styl i quiz (`uczen.nowy`)

1. „Przejdź do kursów” → **Matematyka: funkcja liniowa** → lekcja **Wzór i wykres funkcji liniowej**.
2. Na górze ramka **„Lekcja dopasowana do stylu… Dlaczego to widzisz: … bo tak wyszło w ankiecie (V x / A y / K z). Ukryto N materiałów…”**.
   - „Nauczyciel oznacza każdy załącznik formą V, A lub K (albo kilkoma). Uczeń widzi tekst wspólny i materiały swojego stylu. Filtruje serwer, więc nie da się podejrzeć cudzych materiałów.”
3. Pokaż materiały swojego stylu: dla słuchowca nagrania z lektorem („Posłuchaj”) i film z lektorem (oznaczony V+A).
4. **Zmień styl na żywo:** „Mój styl” → zaznacz tylko V → „Zapisz styl” → wróć do lekcji. Teraz widać wykres, schemat i film. Ramka mówi: „…bo ten styl został wybrany ręcznie w profilu”.
5. Przewiń do **„Sprawdź się”**: 4 pytania (3 wspólne + 1 o materiale z Twojego stylu, z etykietą np. „Wzrokowa (V)”).
   - „Pytanie o materiał, którego uczeń nie widział, byłoby nieuczciwe, więc quiz też jest dopasowany do stylu.”
6. Odpowiedz i kliknij „Sprawdź odpowiedzi”. Pokaż zielone i czerwone odpowiedzi oraz **ramkę adaptacji**: „Zaliczone / spróbuj jeszcze raz, bo quiz w lekcji »…«: X% (próg 70%). System zaktualizował wagi Twoich stylów: V … / A … / K …”.
7. „Rozwiąż jeszcze raz” i ponownie wyślij: wagi już się nie zmieniają. „Liczy się tylko pierwszy sukces i pierwsza porażka w lekcji, więc wag nie da się nabić klikaniem.”

### 5:30–7:30 System proponuje zmianę stylu (`uczen.demo`)

1. Druga karta (incognito): zaloguj się jako `uczen.demo@imsu.pl` → **Mój styl**.
2. Baner: **„Lepiej Ci idzie z materiałami słuchowymi – przełączyć? Dlaczego to widzisz: Wagi stylów po quizach: V 7 / A 8 / K 3 – najlepiej wypadają materiały słuchowe.”**
   - „Kuba w ankiecie wyszedł wzrokowcem (V 9 / A 8 / K 3). Potem w 4 lekcjach zaliczył jeden quiz i oblał trzy, uczył się z materiałów wzrokowych. Każda porażka obniżyła wagę V. Gdy inny styl jest **jedynym** liderem, system proponuje zmianę.”
   - Reguły: „Propozycji nie ma, gdy uczeń wybrał styl ręcznie (jego decyzja wygrywa) albo gdy już ją odrzucił, wtedy nie wraca.”
   - Pokaż sekcję **„Jak system Cię widzi”**: paski wag.
3. Kurs **Programowanie: pętle w Pythonie** → **Pętla for**. Teraz (styl V) widać schemat blokowy, kod i film.
4. Kliknij **„Przełącz”** w banerze (w lekcji albo w profilu). Lekcja od razu pokazuje nagrania (A) i film, a quiz ma teraz pytanie o materiał słuchowy. Ramka: „…bo styl zmieniono po propozycji opartej na wynikach quizów”.

### 7:30–9:00 Nauczyciel: materiały i quiz (`nauczyciel.demo`)

1. Zaloguj się jako `nauczyciel.demo@imsu.pl` → **Moje kursy**: 3 kursy (matematyka, angielski, programowanie).
2. Wejdź w kurs → lekcja → **edytor lekcji**: bloki tekstowe i załączniki (obraz, PDF, nagranie, film) z oznaczeniem form **V / A / K**.
3. „Podgląd” → nauczyciel widzi **wszystkie** materiały (podgląd) i pod spodem quiz z linkiem **„Edytuj quiz”**.
4. **Edytor quizu**: pytania jednokrotnego wyboru, 3–4 odpowiedzi, zaznaczona poprawna i pole **„Dotyczy materiału”** (wspólny / V / A / K). Zmień treść pytania → „Zapisz quiz” → „Zapisano”.

### 9:00–10:00 Podsumowanie

- **Architektura:** FastAPI + PostgreSQL + Next.js. Moduły backendu: konta (`identity`), kursy (`curriculum`), treść (`content`), **styl uczenia (`learning_style`)**, **quizy (`assessment`)**. Ocenianie quizu tylko na serwerze, potem `record_quiz_result` aktualizuje wagi.
- **Inteligencja:** ankieta VAK → styl startowy; dobór materiałów i pytań pod styl; adaptacja wag po quizach (+1/−1, ochrona przed nabijaniem); propozycja zmiany stylu z uzasadnieniem; decyduje uczeń.
- **Jakość:** 272 testy backendu (logika jako czyste funkcje + testy API), lint i build frontendu.
- **Dalszy rozwój:** poziomy trudności, powtórka tematu w innym stylu (było w wersji 1), panel nauczyciela ze stylami uczniów, opcjonalne pytania otwarte analizowane przez LLM.

## Pytania, które mogą paść

- **Skąd wiadomo, że to działa?** Każda reguła to czysta funkcja z testami na konkretnych scenariuszach (`backend/tests/learning_style/test_adaptation.py`, `tests/assessment/`). Zachowanie jest przewidywalne i wyjaśnialne.
- **Czy uczeń może oszukać wynik?** Nie: odpowiedzi ocenia serwer, klucz nie trafia do przeglądarki, a powtórki nie zmieniają wag.
- **Co, jeśli styl z ankiety jest zły?** Po to są wagi i propozycja zmiany, a także ręczny wybór w profilu i ponowna ankieta.
- **Czy jest AI/LLM?** Rdzeń jest regułowy (świadomie: wyjaśnialność, działanie offline). LLM to możliwe rozszerzenie, nie warunek działania.

## Uruchomienie od zera

Wymagania: Docker Desktop, Python 3.12, Node.js. Wszystkie komendy w PowerShell, z katalogu `aplikacja\`.

```powershell
# 1. Baza danych (PostgreSQL w Dockerze)
Copy-Item .env.example .env
docker compose up -d

# 2. Backend
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# JWT_SECRET z .env.example jest za krótki (wymagane min. 32 znaki) – wygeneruj własny:
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
#   ...i wklej wynik do backend\.env jako JWT_SECRET=...
.\venv\Scripts\python.exe -m alembic upgrade head          # tabele + 20 pytań ankiety
.\venv\Scripts\python.exe -m app.demo.seed --reset-students  # kursy, quizy, filmy, konta demo
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app --port 8001

# 3. Frontend (drugi terminal)
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev                                                # http://localhost:3001
```

Uwagi:
- Komendy uruchamiaj przez `python -m ...`. Pliki `.exe` w `venv\Scripts` przestają działać po przeniesieniu folderu z projektem.
- `EADDRINUSE` przy `npm run dev` oznacza, że serwer już działa na porcie 3001.
- Seed można uruchamiać wielokrotnie: dokłada tylko brakujące rzeczy i nie usuwa niczego poza danymi ankiety/quizów dwóch kont uczniów demo (z `--reset-students`).
- Sprawdzenie kodu: `backend`: `python -m pytest`, `python -m ruff check .`; `frontend`: `npm run lint`, `npm run build`.
