# StylNauki – dokumentacja projektu

Projekt zaliczeniowy z przedmiotu *Inteligentne multimedialne systemy uczące* (Informatyka UwB, studia magisterskie, 1 semestr, 2026/27).
Autor: Patryk Kulesza.

> `TODO(prowadzący)`: termin i forma oddania, praca indywidualna czy grupowa oraz wymagany zakres dokumentacji nie są jeszcze potwierdzone — lista pytań w `docs/postep/PYTANIA.md`.

## 1. Cel i zakres

StylNauki to platforma z kursami, która **dopasowuje sposób podania materiału do ucznia**:

1. **na starcie** — według stylu uczenia się z ankiety VAK (wzrokowiec / słuchowiec / kinestetyk),
2. **w trakcie nauki** — według tego, jak uczniowi faktycznie idzie (wyniki quizów).

Rdzeń jest **regułowy**: działa bez internetu i bez modeli językowych, jest przewidywalny, wyjaśnialny i pokryty testami. Jedynym elementem korzystającym z LLM jest opcjonalny generator szkicu lekcji dla nauczyciela — personalizacja i adaptacja od niego nie zależą.

## 2. Aktorzy

| Rola | Co może |
|---|---|
| **Uczeń** | rejestruje się, wypełnia ankietę VAK, uczy się z materiałów w swoim stylu, rozwiązuje quizy, widzi swoją ścieżkę i postęp, może ręcznie zmienić styl albo przyjąć / odrzucić propozycję systemu |
| **Nauczyciel** | tworzy kursy, działy, tematy i bloki; przypisuje blokom styl i poziom; podgląda temat „oczami" V / A / K; edytuje pytania ankiety; widzi uczniów, ich style (z ankiety i aktualny) oraz ścieżki |
| **Admin** | zarządza użytkownikami: zmienia role, blokuje konta; ma też wszystkie uprawnienia nauczyciela |

## 3. Architektura

```
przeglądarka ──HTTP/JSON──> backend FastAPI ──SQLAlchemy──> SQLite (stylnauki.db)
 Next.js 16 / React 19        (port 8000)                    migracje Alembic
 (port 3000)                  /media → wgrane pliki
```

**Backend** (`backend/app`)

| Plik | Odpowiedzialność |
|---|---|
| `main.py` | aplikacja FastAPI, CORS, rejestracja routerów, serwowanie `/media` |
| `models.py` | modele ORM |
| `schemas.py` | schematy wejścia / wyjścia i walidacja (Pydantic) |
| `security.py`, `deps.py` | hasła bcrypt, tokeny JWT, zależności: zalogowany użytkownik, role, bramka ankiety |
| `routers/auth.py`, `uzytkownicy.py` | rejestracja, logowanie, zarządzanie kontami |
| `routers/ankieta.py` | ankieta VAK, profil i styl, edycja pytań |
| `routers/kursy.py` | kursy → działy → tematy → bloki, widok tematu pod styl, quiz, upload |
| `routers/nauka.py` | zdarzenia nauki, ścieżka ucznia, decyzja o zmianie stylu |
| `routers/nauczyciel.py` | lista uczniów i szczegóły ucznia |
| `services/vak.py` | **czysta funkcja** liczenia wyniku ankiety |
| `services/personalizacja.py` | **czyste funkcje** doboru bloków do stylu |
| `services/quiz.py` | **czysta funkcja** oceniania quizu |
| `services/adaptacja.py` | **czyste funkcje** adaptacji (wagi, poziom, rekomendacje, uzasadnienia) |
| `services/nauka.py` | operacje na bazie używane przez adaptację |
| `services/ai_generator.py` | opcjonalny generator szkicu lekcji (Gemini) |
| `seed.py`, `seed_ankieta.py`, `seed_kurs.py`, `seed_matematyka.py` | dane startowe: konta, ankieta, dwa kursy demonstracyjne |
| `wykresy.py` | generator wykresów funkcji liniowych (SVG) do kursu matematyki |

**Frontend** (`frontend/src`)

| Ścieżka | Zawartość |
|---|---|
| `app/logowanie`, `app/rejestracja` | formularze |
| `app/ankieta`, `app/ankieta/wynik`, `app/profil` | ankieta, wynik, „Mój styl uczenia" |
| `app/panel` | panel ucznia |
| `app/kursy`, `app/dzialy`, `app/tematy` | materiały (dla nauczyciela także edytor) |
| `app/nauczyciel`, `app/admin/uzytkownicy` | panele nauczyciela i admina |
| `components/auth/AuthGate.tsx` | ochrona stron: logowanie, role, wymuszenie ankiety |
| `components/temat/` | widok lekcji, bloki multimedialne, edytory quizu i ćwiczenia |
| `components/nauka/` | rekomendacja po quizie, propozycja zmiany stylu, ścieżka |
| `lib/api.ts` | wszystkie wywołania API |

## 4. Model danych

| Tabela | Najważniejsze pola |
|---|---|
| `uzytkownicy` | `email`, `imie`, `haslo_hash`, `rola`, `aktywny`, `ankieta_wypelniona`, `styl_uczenia`, `styl_zrodlo` (`ankieta` / `reczny` / `adaptacja`), `waga_v`, `waga_a`, `waga_k`, `odrzucona_propozycja` |
| `pytania_ankiety`, `odpowiedzi_ankiety` | treść pytania; odpowiedź z przypisanym stylem `V` / `A` / `K` |
| `wyniki_ankiety` | `user_id`, `punkty_v`, `punkty_a`, `punkty_k`, `styl_dominujacy`, `data` (historia) |
| `kursy` → `dzialy` → `tematy` → `bloki` | hierarchia materiałów |
| `bloki` | `typ`, `tresc`, `styl` (`V`/`A`/`K`/`NULL` = wspólny), `poziom` (1–3 / `NULL`), `dane_json` (quiz, ćwiczenie), `image_url`, `media_url`, `kolejnosc` |
| `zdarzenia_nauki` | `user_id`, `temat_id`, `blok_id`, `typ`, `styl`, `wartosc` (wynik quizu w %), `czas_s`, `data` |
| `postepy_tematow` | `user_id`, `temat_id`, `zaliczony`, `najlepszy_wynik`, `ostatni_wynik`, `ostatni_styl`, `liczba_prob` |

**Typy bloków:** `teoria`, `przyklad`, `uwaga`, `zadanie` (klasyczne) oraz multimedialne: `obraz`, `diagram`, `wideo` (głównie V), `audio` (A), `cwiczenie` krok po kroku i `quiz` (K / wspólny).

## 5. Jak działa „inteligencja"

### 5.1 Ankieta VAK (`services/vak.py`)
20 pytań jednokrotnego wyboru; każda odpowiedź daje 1 punkt jednemu stylowi. Styl dominujący to styl z największą liczbą punktów; przy remisie powstaje **styl mieszany** (np. `VA`) i uczeń widzi materiały obu stylów. Wynik jest zapisywany w historii; uczeń może ankietę powtórzyć (nowy wynik nadpisuje styl) albo zmienić styl ręcznie (wynik ankiety zostaje).

Uczeń, który nie wypełnił ankiety, jest przy każdym wejściu kierowany na ankietę, a serwer zwraca dla materiałów `403` z kodem `ANKIETA_WYMAGANA`.

### 5.2 Dobór materiałów (`services/personalizacja.py`)
Uczeń widzi w temacie **bloki wspólne + bloki swojego stylu**, w kolejności ustalonej przez nauczyciela. Filtrowanie odbywa się na serwerze — uczeń nie otrzymuje bloków innych stylów ani klucza odpowiedzi do quizu.

### 5.3 Adaptacja w czasie (`services/adaptacja.py`)

| Reguła | Działanie |
|---|---|
| Start | wagi V/A/K = punkty z ankiety |
| Zaliczenie | quiz ≥ 70% → temat zaliczony, proponowany następny temat |
| Powtórka | quiz < 70% → „spróbuj inaczej": ten sam temat w stylu o drugiej najwyższej wadze (jeszcze niewypróbowanym) |
| Wagi | styl, w którym uczeń przerabiał temat: +1 przy sukcesie, −1 przy porażce (zakres 0–30; liczy się pierwszy sukces i pierwsza porażka w danym temacie i stylu); serwer przyjmuje wynik tylko w stylu, w którym uczeń faktycznie mógł przerabiać temat — własnym albo zaproponowanym do powtórki) |
| Propozycja stylu | gdy inny styl zostaje samodzielnym liderem wag: „Lepiej Ci idzie z materiałami słuchowymi – przełączyć?" — **decyduje uczeń**; ręczny wybór stylu wyłącza propozycje; odrzuconej propozycji system nie powtarza |
| Poziom trudności | dwa ostatnie quizy < 70% → dodatkowe łatwiejsze przykłady (poziom 1); dwa ostatnie ≥ 90% → rozszerzenia (poziom 3); inaczej poziom standardowy |
| Wyjaśnialność | każda rekomendacja ma krótkie „dlaczego to widzisz", np. „bo quiz z tematu »Pętla for«: 45%" |

Wszystkie reguły to czyste funkcje (bez bazy danych), testowane na konkretnych scenariuszach.

### 5.4 Zdarzenia nauki
Zapisywane są: otwarcie tematu, czas w temacie, odtworzenie audio / wideo, ukończenie ćwiczenia i wynik quizu (ten ostatni tylko przez serwer). Wyniki quizów sterują adaptacją; pozostałe zdarzenia służą nauczycielowi do wglądu w aktywność ucznia.

## 6. Bezpieczeństwo

- Hasła: bcrypt; tokeny JWT (HS256) z rolą i czasem ważności; sekret w `.env`.
- Uprawnienia sprawdzane po roli z bazy przy każdym żądaniu (zmiana roli i blokada konta działają natychmiast).
- Uczeń widzi tylko opublikowane kursy; treści innych stylów i klucz quizu nie opuszczają serwera.
- Upload: biała lista rozszerzeń (obrazy, audio), limit rozmiaru, losowe nazwy plików.
- Błędy serwera nie ujawniają treści wyjątków; sekretów nie ma w repozytorium (`.env` w `.gitignore`).

## 7. Testy

`cd backend && pytest` — 452 testy:

| Plik | Zakres |
|---|---|
| `test_auth.py` | hasła, tokeny, rejestracja, logowanie, uprawnienia, seed kont |
| `test_vak.py` | liczenie wyniku ankiety (remisy, walidacja) |
| `test_ankieta.py` | flaga ankiety, wymuszenie, powtórka, ręczny styl, edycja pytań |
| `test_personalizacja.py` | filtrowanie bloków, quiz, upload, kurs demonstracyjny |
| `test_adaptacja.py` | reguły adaptacji na czystych funkcjach + pełny scenariusz |
| `test_nauka.py` | adaptacja przez API: wagi, rekomendacje, poziom, ścieżka, zdarzenia |
| `test_panele.py` | panel nauczyciela i admina |
| `test_kursy.py` | CRUD kursów, generator AI (błędy) |
| `test_seed_matematyka.py` | kurs matematyki: każda liczba z przykładów, zadań i kluczy quizów przeliczona na ułamkach; punkty na wykresach zgodne z treścią |

Testy budują bazę prawdziwymi migracjami Alembic. Frontend: `npm run lint`, `npm run build`.

## 8. Uruchomienie

Pełna instrukcja i konta testowe: `README.md` w katalogu głównym. Skrót:

```powershell
cd backend;  python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt
copy env.example .env; alembic upgrade head; python -m app.seed
uvicorn app.main:app --port 8000

cd frontend; npm install; npm run dev      # http://localhost:3000
```

## 9. Scenariusz prezentacji (ok. 10 minut)

1. **Wymuszona ankieta.** Zaloguj się jako `uczen@stylnauki.pl` → aplikacja od razu otwiera ankietę; próba wejścia na `/kursy` wraca na ankietę. Wypełnij ją → wynik „Jesteś: …, V x / A y / K z".
2. **Ten sam temat, trzy style.** W trzech oknach (lub po kolei) zaloguj się jako `wzrokowiec@…`, `sluchowiec@…`, `kinestetyk@…` (hasło `Uczen123!`) i otwórz w kursie „Matematyka: funkcja liniowa" temat **„Miejsce zerowe i punkty przecięcia z osiami"**:
   - wzrokowiec widzi dwa wykresy z zaznaczonym miejscem zerowym i przecięciem z osią $OY$,
   - słuchowiec dostaje omówienie do odsłuchania („dwa iks minus cztery równa się zero…") — bez ani jednego symbolu,
   - kinestetyk rozwiązuje równanie krok po kroku na kartce i sprawdza wynik podstawieniem.

   Teoria (ściąga ze wzorem), typowy błąd, zadanie i quiz są wspólne. Zwróć uwagę na ramkę „Dlaczego to widzisz". To samo można pokazać na kursie Pythona (temat „Zmienne i typy danych").
3. **Ręczna zmiana stylu.** Profil → „Mój styl uczenia" → inny styl → „Wynik ankiety: … · wybrany ręcznie: …"; wróć do tematu — bloki się zmieniły. „Wróć do wyniku ankiety".
4. **Adaptacja.** Jako uczeń z wyrównanym wynikiem ankiety (np. po kroku 1) odpowiedz źle na quiz → „Spróbuj inaczej: … w wersji dla stylu …" z uzasadnieniem → rozwiąż quiz dobrze w drugim stylu → „Temat zaliczony" i pytanie „Lepiej Ci idzie z materiałami … – przełączyć?".
5. **Poziom trudności.** Dwa słabe quizy z rzędu → w następnym temacie pojawia się przykład „Zacznijmy prościej"; dwa wyniki ≥ 90% → „Dla chętnych".
6. **Panel ucznia.** `/panel`: następny krok z uzasadnieniem, wagi stylów, ścieżka z postępem.
7. **Nauczyciel.** `nauczyciel@stylnauki.pl`: tabela uczniów (wynik ankiety obok aktualnego stylu), szczegóły ucznia; w temacie „Podgląd oczami ucznia" V / A / K; „Tryb Edycji" → dodaj blok, ustaw „dla kogo" i poziom; edytor ankiety.
8. **Admin.** `admin@stylnauki.pl`: zmiana roli i blokada konta.

## 10. Ograniczenia i możliwy rozwój

- **Teoria stylów uczenia jest w psychologii kwestionowana.** Podział na wzrokowców, słuchowców i kinestetyków (VAK) jest popularny, ale badania nie potwierdzają tzw. hipotezy dopasowania (*meshing hypothesis*), czyli tego, że uczeń uczy się lepiej, gdy materiał jest podany w „jego" stylu. Projekt mimo to ma sens, bo:
  - jego celem jest pokazanie **mechanizmu personalizacji i adaptacji** w systemie uczącym, a nie dowodzenie teorii VAK;
  - wynik ankiety jest tylko punktem startu — uczeń może w każdej chwili **ręcznie zmienić styl**;
  - adaptacja opiera się na **wynikach quizów**, a nie wyłącznie na deklaracji z ankiety: system proponuje inny sposób podania materiału, gdy obecny nie działa, i zostawia decyzję uczniowi;
  - model VAK jest **wymienny** — style są etykietą bloków i odpowiedzi ankiety, więc można go zastąpić innym podziałem (np. VARK) bez zmiany mechanizmu.
- Nauczyciel widzi wszystkich uczniów (brak klas i zapisów na kurs).
- Omówienia audio w kursie demonstracyjnym czyta lektor przeglądarki; nauczyciel może wgrać własne nagrania.
- Zdarzenia inne niż wyniki quizów nie wpływają jeszcze na adaptację.
- Możliwy dodatek LLM (pytania otwarte w ankiecie, „wyjaśnij inaczej") — poza zakresem tej wersji; rdzeń ma pozostać regułowy.
