# RAPORT: ankieta VAK, profilowanie, adaptacja (gałąź `feat/ankieta-vak`)

## Etap 0: porządki (2026-11-08)

**Zrobione**
- Utworzona gałąź `feat/ankieta-vak` od `v2` (`45a252f`).
- Kopia starego `backend/.env` (z v1) przeniesiona z katalogu tymczasowego do `backend/.env.v1.bak`.
- Środowisko lokalne: odtworzony `backend/venv` (stary miał zapisaną ścieżkę `Magisterka 1 semestr`, przez co `uvicorn.exe` i `alembic.exe` nie startowały), utworzone `.env` i `frontend/.env.local` z przykładów, do `backend/.env` dopisane brakujące klucze v2.

**Jak sprawdzone**
- `git check-ignore -v`: `.env`, `backend/.env` (`.gitignore`) i `frontend/.env.local` (`frontend/.gitignore`) są ignorowane.
- Wartości z plików env nie były wypisywane.

**Co nie działa / do uwagi**
- `*.bak` **nie było** w `.gitignore`, więc `backend/.env.v1.bak` (zawiera klucze) mógł trafić do commita. Tymczasowo zabezpieczone lokalnym `.git/info/exclude` (`*.bak`), bez zmiany plików w repo. Docelowo dopisać `*.bak` do `.gitignore`: zmiana B3 w specyfikacji, czeka na akceptację.
- `frontend/package-lock.json` jest zmodyfikowany po `npm install` z innej wersji npm. To nie są moje zmiany i nie są commitowane.
- Rejestracja z rolą `teacher` przez `/auth/register`: zgodnie z poleceniem nie poprawiane, zgłasza autor.

## Etap 1: specyfikacja (2026-11-08)

**Zrobione**
- `docs/SPEC-ankieta-vak.md`: tabele i migracja, endpointy, ekrany, adaptacja z interfejsem dla quizu, lista zmian w istniejących plikach (B1–B3, F1–F4), plan testów, kolejność commitów.

**Jak sprawdzone**
- Logika przeniesiona z v1: `services/vak.py`, `personalizacja.py`, `adaptacja.py`, `routers/ankieta.py`, `seed_ankieta.py`.
- Punkty styku w v2 sprawdzone w kodzie: `main.py`, `alembic/env.py`, `content/service.get_blocks`, `curriculum/service.get_visible_lesson`, `tests/conftest.py`, frontend `LessonView.tsx`, `(app)/layout.tsx`, `(focus)/layout.tsx`, `AuthenticatedShell.tsx`.
- Stan wyjściowy: `pytest` 178 passed, `npm run lint` czysty, aplikacja uruchomiona lokalnie.

**Co nie działa / do uwagi**
- Kodu jeszcze nie ma. **Czeka na akceptację specyfikacji** (sekcja 8 SPEC).

## Etap 2: backend, czyli ankieta, profil, lekcje pod styl i adaptacja (2026-11-08)

**Zrobione** (commity `772307f`, `f05fbee`, `0cf0e27`)
- Moduł `backend/app/modules/learning_style/`: `models.py`, czyste funkcje `scoring.py`, `personalization.py` i `adaptation.py` (logika z v1), `service.py`, `router.py`, `schemas.py`, `hooks.py`.
- Migracja `ea197399889b`: 5 tabel + 20 pytań ankiety z v1 (po 3 odpowiedzi V/A/K).
- Endpointy zgodne ze SPEC: `/survey/questions|answers|results`, `/profile/learning-style` (GET/PUT/DELETE, `/proposal/accept|reject`), `/lessons/{id}/personalized-blocks`.
- `record_quiz_result(db, user=..., lesson_id=..., block_id=..., percent=...)` dla quizu Bartka.
- Zmiany w plikach Bartka zgodne z akceptacją: B1 `main.py` (import + 3× `include_router`), B2 `alembic/env.py` (+1 import), B3 `.gitignore` (`*.bak`).

**Decyzje podjęte samodzielnie**
- `QuizFeedback` jest modelem Pydantic, a nie dataclass (jak było w SPEC), żeby Bartek mógł go wprost dołożyć do odpowiedzi JSON swojego quizu.
- Teksty „dlaczego” mają formy neutralne („ten styl został wybrany ręcznie”), a nie „wybrałeś” jak w v1.
- `record_quiz_result` sam robi `commit` (opisane w docstringu).
- „Pierwszy sukces / pierwsza porażka” liczone na parę (lekcja, styl ucznia w chwili quizu).

**Jak sprawdzone**
- `pytest`: **244 passed** (178 Bartka + 66 nowych w `tests/learning_style/`).
- `ruff check .` i `ruff format --check .`: czyste. `ruff format` nie zmienił żadnego pliku Bartka (sprawdzone `git status`).
- Migracja: `alembic downgrade -1` + `upgrade head` działa, w bazie 20 pytań i po 20 odpowiedzi V, A i K.

**Co nie działa / do uwagi**
- Hook alembica `ruff_fix` (w `alembic.ini` Bartka) wymaga `ruff` na PATH. Bez aktywnego venv generowanie migracji kończy się błędem po zapisaniu pliku, a plik trzeba sformatować ręcznie (`python -m ruff format`). Nie zmieniam, to konfiguracja Bartka.

## Etap 3: frontend (2026-11-08)

**Zrobione** (commity `e904861`, `69affb8`)
- `frontend/src/features/learning-style/`: `api.ts`, `hooks.ts` (React Query), `types.ts`, `styles.ts`, `errors.ts` i komponenty `SurveyGate`, `SurveyForm`, `SurveyResult`, `LearningStylePanel`, `StyleBars`, `StyleProposalBanner`, `PersonalizationNote`, `AdaptationFeedback`.
- Strony: `/survey` (ankieta), `/survey/result` (wynik), `/profile` („Mój styl uczenia się”), wszystkie tylko dla roli `student` (`RoleGate` Bartka).
- Podpięcia zgodne z akceptacją: F1 `(app)/layout.tsx` i F2 `(focus)/layout.tsx` (`SurveyGate`), F3 link „Mój styl” w menu ucznia, F4 `LessonView.tsx` (`usePersonalizedBlocks` + `PersonalizationNote`).

**Decyzje podjęte samodzielnie**
- `SurveyGate` w `(app)/layout` stoi **wewnątrz** `AuthenticatedShell`, żeby na ekranie ankiety był nagłówek z wylogowaniem.
- Kolejność odpowiedzi w pytaniu jest mieszana deterministycznie (wg id), a nie `Math.random`, żeby uniknąć różnic przy renderowaniu i ostrzeżeń lintera. Efekt jest ten sam: V nie jest zawsze pierwsze.
- Komunikaty błędów nowych kodów (`SURVEY_*`, `NO_PROPOSAL`) są we własnym `errors.ts`, z fallbackiem do `errorMessage` Bartka, bez zmiany jego `error-messages.ts`.
- Notka „dlaczego to widzisz” pokazuje się tylko uczniom. Nauczyciel/admin w podglądzie widzi lekcję jak wcześniej.

**Jak sprawdzone**
- `npm run lint`: czysto. `tsc --noEmit`: 0 błędów w `src/`. `npm run build`: OK, nowe trasy `/survey`, `/survey/result`, `/profile`.

**Co nie działa / do uwagi**
- Pierwszy `npm run build` padał na `EPERM rmdir .next/server/...`: katalogi starego builda v1 (z 01.10) miały atrybut **tylko do odczytu** (pozostałość po kopiowaniu folderu). Usunąłem stare `.next/server|static|types|diagnostics` (artefakty, ignorowane przez git). `.next/dev` działającego serwera nie był ruszany.
- Przejście w przeglądarce: w etapie 5 (po decyzji o quizie).

## Etap 4: dane demo (2026-11-08)

**Zrobione**
- Komenda `python -m app.demo.seed` (z katalogu `backend/`), idempotentna; `--reset-students` czyści tylko dane ankiety i quizów **dwóch kont demo uczniów**.
- 3 opublikowane kursy nauczyciela demo, razem 7 lekcji. W każdej lekcji: blok tekstowy (wspólny), obrazy **V**, nagrania **A** (tekst czytany przez lektora przeglądarki), karty ćwiczeń PDF **K** i materiały mieszane (V+K, A+K):
  - Matematyka: funkcja liniowa (Wzór i wykres; Współczynnik kierunkowy a; Miejsce zerowe),
  - Angielski: Present Perfect (Budowa zdania; Present Perfect czy Past Simple?),
  - Programowanie: pętle w Pythonie (Pętla for; Pętla while).
- Materiały lokalne: 10 PNG (wykresy, schematy, schemat blokowy, kod) i 7 PDF (karty ćwiczeń) w `backend/app/demo/assets/`; zero linków zewnętrznych. Generator: `app/demo/generate_assets.py` (wymaga Pillow, którego **nie** dodałem do `requirements.txt`; wygenerowane pliki są w repo, więc seed nie potrzebuje niczego dodatkowego).
- Konta (hasło `Demo123!`):

| Konto | Rola | Stan |
|---|---|---|
| `nauczyciel.demo@imsu.pl` | nauczyciel | właściciel 3 kursów |
| `admin.demo@imsu.pl` | admin | – |
| `uczen.nowy@imsu.pl` | uczeń | bez ankiety → pokaz wymuszenia |
| `uczen.demo@imsu.pl` | uczeń | ankieta V 9 / A 8 / K 3 (styl V), 4 quizy przez `record_quiz_result` (85%, 55%, 40%, 45%) → wagi V 7 / A 8 / K 3 → **propozycja zmiany na A** z uzasadnieniem |

**Decyzje podjęte samodzielnie**
- SVG nie wchodzi w grę: moduł plików Bartka go nie przyjmuje (świadomie, ze względów bezpieczeństwa). Dlatego PNG.
- Brak wideo: nie ma lokalnego źródła, a YouTube to link zewnętrzny (zakazany przez polecenie).
- Lektor przeglądarki czyta po polsku (`pl-PL` w `SpeechReader` Bartka), więc transkrypcje A są po polsku, także w kursie angielskiego. Angielskie zdania są w tekście i PDF-ach.
- `# ruff: noqa: E501` na górze `courses.py` i `generate_assets.py`: to treść dydaktyczna, zdania zostają w całości; `pyproject.toml` Bartka bez zmian.
- Kurs rozpoznawany po (nauczyciel demo, tytuł). Jeśli istnieje, seed go nie dotyka (nie nadpisuje zmian zrobionych ręcznie).

**Jak sprawdzone**
- Seed uruchomiony dwa razy na bazie deweloperskiej: drugi przebieg niczego nie dubluje.
- `tests/demo/test_seed.py` (4 testy): kursy opublikowane z plikami, nowy uczeń bez ankiety, uczeń demo z propozycją A, idempotencja, reset czyści tylko dane stylu.
- `ruff check .` / `ruff format --check .`: czyste. Obrazy obejrzane, 2 poprawione (łączniki w schemacie wzoru, napis na osi czasu, strzałka powrotu w schemacie pętli).

**Co nie działa / do uwagi**
- Jeśli seed zostanie przerwany w połowie tworzenia kursu, kolejne uruchomienie uzna kurs za istniejący. Wtedy trzeba go zarchiwizować w UI nauczyciela i uruchomić seed ponownie.

## Etap 5: quiz w module `assessment` (2026-11-08/09)

**Zrobione** (commity `5a426ff`, `ddef85f`)
- Backend `backend/app/modules/assessment/`: tabela `lesson_quizzes` (1 quiz na lekcję, pytania w JSONB, migracja `2e7cf4c0d9fc`), czyste funkcje `grading.py` (dobór pytań pod styl, ocenianie), `service.py`, `router.py`:
  - `GET /lessons/{id}/quiz`: pytania **bez klucza**, dla ucznia tylko wspólne + o materiałach jego stylu (`hidden_count`),
  - `POST /lessons/{id}/quiz/attempts`: ocena **tylko na serwerze** → `record_quiz_result` → odpowiedź z `adaptation` (`QuizFeedback`),
  - `GET /lessons/{id}/quiz/edit`, `PUT`, `DELETE`: edytor autora lekcji.
- Pytania jednokrotnego wyboru, 3–4 odpowiedzi, opcjonalne `form` (V/A/K) = pytanie o konkretny materiał.
- Frontend `features/assessment/`: `LessonQuiz` (pod lekcją; wynik, zaznaczenie poprawnych/błędnych, `<AdaptationFeedback />`), `QuizEditor` na nowej stronie `/teach/courses/[id]/lessons/[id]/quiz`.
- Zmiany w plikach Bartka tylko w zaakceptowanych miejscach: B1 `main.py` (+1 router), B2 `alembic/env.py` (+1 import), F4 `LessonView.tsx` (`<LessonQuiz />` pod blokami; dla autora z `editHref`).

**Decyzje podjęte samodzielnie**
- **Uczeń dostaje tylko pytania wspólne i o materiałach swojego stylu.** Pytanie o materiał, którego nie widział, byłoby nieuczciwe. Serwer odrzuca odpowiedź na pytanie spoza zestawu (`QUIZ_INCOMPLETE`).
- **Link „Edytuj quiz” jest przy lekcji w podglądzie autora** (LessonView = F4). Ścieżka nauczyciela: edytor lekcji → „Podgląd” → „Edytuj quiz”. Link bezpośrednio w edytorze lekcji (`LessonEditor`/`LessonList` Bartka) wymagałby zmiany jego plików, więc go nie dodałem. Jeśli chcesz, to 1 link w `LessonEditor.tsx` obok „Podgląd”, do akceptacji.
- `block_id` w `quiz_attempts` = `quiz-{id}`.
- Nauczyciel/admin może rozwiązać quiz w podglądzie (wynik bez adaptacji: `adaptation: null`).

**Jak sprawdzone**
- `tests/assessment/`: 22 testy, w tym ocenianie (czyste funkcje), uprawnienia edytora, walidacja, ukrycie klucza, filtrowanie pod styl, `SURVEY_REQUIRED`, integracja z adaptacją (wagi po quizie, brak „nabijania” przy powtórkach, podgląd nauczyciela bez adaptacji).

## Etap 6: dane demo – quizy i filmy (2026-11-09)

**Zrobione** (commit `bf0a027`)
- Seed dokłada do **każdej z 7 lekcji** quiz: 3 pytania wspólne + po 1 o materiale V, A i K (uczeń jednego stylu odpowiada na 4).
- 2 lokalne filmy MP4 oznaczone **V+A**: `m_film.mp4` (40 s, funkcja liniowa) i `p_film.mp4` (32 s, pętle). To slajdy z grafik lekcji z polskim lektorem (głos Windows „Paulina”), 1280×720 H.264/AAC, ok. 0,5–0,7 MB. Generator: `app/demo/generate_videos.py` (wymaga `imageio-ffmpeg`, poza `requirements.txt`; pliki są w repo).
- Seed jest teraz **uzupełniający**: dla istniejącego kursu demo dokłada brakujące lekcje, bloki (po `id`) i quizy, a niczego nie nadpisuje. Bloki dodane przez nauczyciela ręcznie zostają.

**Jak sprawdzone**
- `tests/demo/test_seed.py` (6 testów): quiz w każdej lekcji, 2 filmy V+A, dokładanie brakującego quizu do istniejącego kursu, idempotencja.
- Seed na bazie deweloperskiej dołożył filmy i quizy do kursów utworzonych wcześniej.

## Etap 7: pełne sprawdzenie i przejście w przeglądarce (2026-11-09)

**Wyniki**
- `pytest`: **272 passed** (178 Bartka + 94 nowe). `ruff check .` / `ruff format --check .`: czyste.
- `npm run lint`: czysto. `npm run build`: OK (trasy `/survey`, `/survey/result`, `/profile`, `/teach/.../quiz`).

**Jak przechodziłem:** rozszerzenie Claude in Chrome nie było połączone, więc przejście zrobiłem **Playwrightem na zainstalowanym Chrome** (`channel="chrome"`, bez pobierania przeglądarki; pakiet tylko w narzędziowym venv poza projektem). Każde konto miało osobną sesję, a z każdego kroku zrobiłem zrzut ekranu.

**Co widać na ekranach**

| Konto | Ekran | Co widać |
|---|---|---|
| uczen.nowy | po zalogowaniu | od razu `/survey`: „Ankieta: jak najlepiej się uczysz?”, licznik „Odpowiedziano na 0 z 20 pytań”, pytania z 3 odpowiedziami w mieszanej kolejności. Wejście na `/courses` też wraca na ankietę |
| uczen.nowy | wynik | „Twój styl: słuchowiec”, opis stylu, paski punktów V 3 / A 9 / K 8, przyciski „Przejdź do kursów” i „Mój styl uczenia się” |
| uczen.nowy | lekcja „Wzór i wykres…” | ramka „Lekcja dopasowana do stylu: słuchowiec. Dlaczego to widzisz: … (V 3 / A 9 / K 8). Ukryto 3 materiały…”; tekst, film V+A, dwa nagrania z „Posłuchaj”; obrazy i karta PDF ukryte |
| uczen.nowy | quiz | 4 pytania (3 wspólne + „Słuchowa (A)”), po wysłaniu „Wynik: 3 / 4 (75%)”, „Zaliczone: 75%”, uzasadnienie z progiem 70% i „System zaktualizował wagi…: V 3 / A 10 / K 8” |
| uczen.demo | Mój styl | baner „Lepiej Ci idzie z materiałami słuchowymi – przełączyć?” + „Dlaczego to widzisz: Wagi stylów po quizach: V 7 / A 8 / K 3…”, styl „wzrokowiec · z ankiety”, paski wag, zmiana stylu, historia ankiet |
| uczen.demo | lekcja „Pętla for” → „Przełącz” | przed: schemat, kod, film; po akceptacji: „Lekcja dopasowana do stylu: słuchowiec … bo styl zmieniono po propozycji opartej na wynikach quizów”, nagranie i film, quiz z pytaniem „Słuchowa (A)” |
| nauczyciel.demo | Moje kursy → kurs → edytor lekcji → Podgląd | 3 kursy; w podglądzie wszystkie materiały i quiz (6 pytań) z linkiem „Edytuj quiz” |
| nauczyciel.demo | edytor quizu | pytania z treścią, „Dotyczy materiału” (wspólny/V/A/K), odpowiedzi z wyborem poprawnej; zapis → „Zapisano” |

**Znalezione i naprawione błędy (prawdziwa przyczyna)**
1. **Po przełączeniu stylu quiz pokazywał pytanie dla starego stylu** (lekcja już A, quiz dalej „Wzrokowa (V)”). Przyczyna: zapytanie o quiz było w cache pod kluczem niezależnym od stylu, a treść quizu zależy od stylu. Naprawa: styl ucznia jest częścią klucza zapytania (`["quiz", lessonId, style]`), więc zmiana stylu sama powoduje pobranie quizu od nowa (`acb8d01`). Skrypt przejścia sprawdza to teraz wprost.
2. **Edytor quizu po zapisie nie pokazywał „Zapisano”** (i tracił stan). Przyczyna: `key={dataUpdatedAt}`, więc zapis aktualizował cache i komponent montował się od nowa. Naprawa: klucz zależny tylko od lekcji (`acb8d01`).
3. Awatar pokazywał „K(” zamiast inicjałów, bo nazwy kont demo miały nawiasy („Kuba (uczeń)”). Naprawa: zwykłe imiona i nazwiska; seed wyrównuje nazwę istniejących kont demo (`0cbfc6d`).

**Co nie działa / do uwagi**
- Błędy `401` w konsoli przeglądarki przed zalogowaniem to zapytanie `/auth/me` z kodu Bartka (tak sprawdza „czy ktoś jest zalogowany”), więc to nie jest błąd.
- Pytania ankiety (z v1) mają formy męskie („Kupiłeś nowe urządzenie…”). Poprawa wymagałaby nowej migracji danych; zostawiam do decyzji.
- `backend/.env.example` (Bartka) ma `JWT_SECRET` krótszy niż wymagane 32 znaki, więc uruchomienie od zera po samym skopiowaniu pliku się nie powiedzie. Opisane w `SCENARIUSZ-POKAZU.md` (jak wygenerować klucz); pliku Bartka nie zmieniałem.
- Film w podglądzie nie ma miniatury (czarny kadr do czasu odtworzenia); przy kliknięciu działa normalnie.
- Po przejściu testowym konta demo uczniów zostały przywrócone komendą `python -m app.demo.seed --reset-students`.
- `frontend/package-lock.json` jest dalej zmieniony po Twoim `npm install`; nie commitowany.

## Etap 8: scenariusz pokazu (2026-11-09)

- `docs/SCENARIUSZ-POKAZU.md`: pokaz na ok. 10 minut (konta, kliknięcia, co powiedzieć o „inteligencji”, pytania prowadzącego) i komendy uruchomienia od zera.

## Etap 9: poprawki po przeglądzie (2026-11-09)

**Decyzje autora:** link „Edytuj quiz” w `LessonEditor.tsx` Bartka nie jest dodawany (zostaje ścieżka przez Podgląd). `JWT_SECRET` w `.env.example` przekazuje Bartkowi autor.

**Zrobione**
- **Ankieta bez form płciowych** (commit `1b18758`): migracja danych `c3a91f2d7b40` (tylko nasze tabele `survey_questions`/`survey_answers`) zmienia 1 pytanie i 7 odpowiedzi, np. „Kupiłeś nowe urządzenie” → „Kupujesz nowe urządzenie”, „prosisz, żeby dał Ci spróbować samemu” → „prosisz o możliwość samodzielnej próby”, „To, co robiłem” → „To, co robisz na miejscu”. Odpowiedzi w 1. osobie czasu teraźniejszego („Oglądam…”) były już neutralne i zostały. Sens pytań i styl V/A/K każdej odpowiedzi bez zmian. Migracja zmienia tylko wiersze, które mają oczekiwany stary tekst; `downgrade` przywraca poprzednie brzmienie.
- **`frontend/package-lock.json` przywrócony** (`git restore`): diff to usunięte flagi `"peer": true` i dodane opcjonalne pakiety `@emnapi/*`, czyli efekt innej wersji npm. Aplikacja tego nie potrzebuje.
- **Głos neuronowy** (commit `e5e7d2b`), wyłącznie w naszych plikach:
  - `app/demo/generate_audio.py`: 9 bloków audio z kursów demo nagranych głosem **pl-PL-ZofiaNeural** (edge-tts, tempo −5%), z obcięciem ciszy na początku (ffmpeg). MP3 mono 24 kHz 64 kb/s, ok. 200 KB każdy.
  - `app/demo/generate_videos.py`: oba filmy z tym samym głosem, **pierwsza klatka to slajd tytułowy**: `m_film.mp4` 48,9 s, `p_film.mp4` 40,5 s.
  - Bloki audio w kursach demo to teraz **pliki MP3** (oznaczenie A bez zmian). `SpeechReader.tsx` i inne pliki Bartka nie były ruszane.
  - Seed: nowa opcja `--refresh-demo-media` podmienia **nasze** bloki audio/wideo (rozpoznawane po `id` i rodzaju) w istniejących kursach demo. Bloki dodane ręcznie przez nauczyciela zostają (test).
  - Narzędzia (`edge-tts`, `imageio-ffmpeg`, Pillow) są tylko w osobnym narzędziowym venv, nie w `requirements.txt`.

**Decyzje podjęte samodzielnie**
- Moduł treści Bartka przyjmuje dla audio **plik albo transkrypcję** (nie oba naraz), więc bloki MP3 nie pokazują już tekstu pod odtwarzaczem. Tekst nagrania zostaje w `courses.py` (źródło nagrań) i w opisie quizu „z nagrania”.
- Tytuł filmu „w 40 sekund” → „w skrócie” (film z tytułem trwa teraz 49 s).
- Opcja nazywa się `--refresh-demo-media` (a nie `--refresh-demo-audio`), bo podmienia też filmy.

**Jak sprawdzone**
- Audio, techniczny odsłuch (skrypt `check_audio.py`, ffmpeg `silencedetect`/`volumedetect` + znaczniki słów edge-tts):

| Plik | Długość | Tempo | Cisza na starcie | Głośność śr. | Słowa wypowiedziane / w tekście |
|---|---|---|---|---|---|
| m1_a-wyjasnienie.mp3 | 26,8 s | 12,8 zn/s | brak | −21,9 dB | 68/68 zgodne |
| m1_ak-cwiczenie.mp3 | 25,1 s | 12,3 zn/s | brak | −22,7 dB | 58/58 zgodne |
| m2_a-wyjasnienie.mp3 | 20,5 s | 13,6 zn/s | brak | −22,6 dB | 47/47 zgodne |
| m3_a-wyjasnienie.mp3 | 25,4 s | 11,4 zn/s | brak | −23,3 dB | 53/53 zgodne |
| e1_a-wyjasnienie.mp3 | 23,5 s | 13,5 zn/s | brak | −22,8 dB | 52/52 zgodne |
| e1_ak-powtorz.mp3 | 22,2 s | 12,4 zn/s | brak | −22,3 dB | 47/47 zgodne |
| e2_a-wyjasnienie.mp3 | 21,1 s | 14,5 zn/s | brak | −22,7 dB | 51/51 zgodne |
| p1_a-wyjasnienie.mp3 | 22,3 s | 13,6 zn/s | brak | −22,1 dB | 59/59 zgodne |
| p2_a-wyjasnienie.mp3 | 22,4 s | 14,3 zn/s | brak | −22,3 dB | 50/50 zgodne |

- Filmy: 48,9 s i 40,5 s, 1280×720 H.264 + AAC; pierwsza klatka obejrzana (slajd tytułowy na granatowym tle).
- Testy: `test_survey_wording.py` (brak form płciowych w całej ankiecie, nowe teksty przy właściwych stylach, 20 pytań × V/A/K) i nowe testy seeda (audio = pliki MP3; odświeżenie podmienia stary blok czytany przez przeglądarkę, bez flagi nic nie zmienia, blok nauczyciela zostaje na swoim miejscu).
- Seed na bazie deweloperskiej: `--refresh-demo-media` odświeżył 9 bloków audio i 2 filmy; drugi przebieg bez flag niczego nie zmienił.
- `pytest`: **277 passed**. `ruff check .` / `ruff format --check .`: czyste. `npm run lint`: czysto. `npm run build`: OK.
- Playwright, `uczen.nowy`: ankieta zawiera „Kupujesz nowe urządzenie” i żadnej formy płciowej → wynik „słuchowiec” → lekcja „Wzór i wykres…”: film 48,9 s (slajd tytułowy w podglądzie) i 2 odtwarzacze audio (26,8 s i 25,1 s, `readyState` 4), brak przycisku „Posłuchaj” lektora przeglądarki → quiz oceniony („Wynik: 1 / 4”). Brak błędów JS na stronie.
- Na koniec `python -m app.demo.seed --reset-students` (konta uczniów demo w stanie startowym).

**Co nie działa / do uwagi**
- Stare pliki z poprzednich wersji audio/wideo zostały w tabeli `files` i w `uploads/` lokalnej bazy (nic się do nich nie odwołuje). Na czystej maszynie ich nie będzie.
- Do ponownego nagrania potrzebny jest internet (edge-tts to usługa online). Odtwarzanie gotowych plików działa offline.
