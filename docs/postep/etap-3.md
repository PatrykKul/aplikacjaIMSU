# Etap 3 – personalizacja bloków + kurs demonstracyjny V/A/K   (01.10.2026)

## Plan (krótko)
1. Backend: `Blok.styl`, nowe typy bloków, dane strukturalne quizu i ćwiczenia, filtrowanie bloków pod styl (czysta funkcja), podgląd stylu dla nauczyciela, sprawdzanie quizu, bezpieczny upload obrazków i nagrań.
2. Frontend: renderowanie nowych typów, wybór stylu bloku w edytorze, podgląd tematu „oczami" V / A / K.
3. Seed kursu, w którym każdy temat ma bloki wspólne oraz dla V, A i K.

## Co zrobione (lista, z plikami)
**Backend**
- `app/models.py` – `Blok.styl` (`V`/`A`/`K`/`NULL` = wspólny), `Blok.media_url`, `Blok.dane_json` (+ właściwość `dane`); migracja `alembic/versions/0004_blok_styl_media_dane.py`.
- `app/schemas.py` – typy bloków: `teoria, przyklad, uwaga, zadanie, wideo, obraz, diagram, audio, cwiczenie, quiz`; walidacja `QuizDane` i `CwiczenieDane` (`waliduj_dane_bloku`).
- `app/services/personalizacja.py` – czyste funkcje `filtruj_bloki`, `blok_widoczny`, `style_ucznia`, `ukryj_klucz_quizu`.
- `app/services/quiz.py` – czysta funkcja `ocen_quiz`.
- `app/routers/kursy.py`:
  - `GET /tematy/{id}` – uczeń dostaje bloki wspólne + swojego stylu (quiz bez klucza odpowiedzi); nauczyciel/admin wszystko; `?styl=V|A|K` = podgląd (edytor) lub powtórka w innym stylu (uczeń); odpowiedź zawiera `styl_widoku`;
  - `POST /bloki/{id}/quiz` – ocena quizu po stronie serwera;
  - `POST /upload-image`, `POST /upload-audio` – biała lista rozszerzeń, limit rozmiaru, losowe nazwy.
- `app/media.py` + `app/main.py` – pliki zapisywane w `backend/uploads` (`MEDIA_ROOT`) i serwowane pod `/media`.
- `app/seed_kurs.py` + `app/seed.py` – kurs „Podstawy programowania w Pythonie": 2 działy, 4 tematy; każdy temat: teoria (wspólna), obraz + diagram (V), audio z lektorem (A), ćwiczenie krok po kroku (K), przykład, uwaga, quiz (wspólny).

**Frontend**
- `src/components/temat/bloki/` – `DiagramBlock`, `AudioBlock` (nagranie lub lektor przeglądarki + transkrypcja), `CwiczenieBlock`, `QuizBlock`, `WideoBlock` (link YouTube / plik / iframe).
- `src/components/temat/edytory/` – `QuizEditor`, `CwiczenieEditor`.
- `src/components/temat/TematLessonView.tsx` – nowe typy w menu dodawania, wybór „dla kogo" (wspólny / V / A / K) przy edycji bloku, plakietka stylu na bloku, wgrywanie nagrania.
- `src/app/tematy/[tematId]/TematPageClient.tsx` – nauczyciel: pasek „Podgląd oczami ucznia" (wszystkie / V / A / K); uczeń: informacja „Materiały dobrane do stylu: …" z linkiem do zmiany.
- `public/demo/*.svg` – 4 ilustracje do kursu demonstracyjnego.

**Testy**: `tests/test_personalizacja.py` (52 przypadki: funkcje czyste, API, quiz, upload, seed kursu).

## Decyzje i dlaczego
- **Filtrowanie po stronie serwera** – uczeń fizycznie nie dostaje bloków innych stylów ani klucza quizu.
- **Styl mieszany** (`VA`) widzi bloki obu stylów.
- **Quiz i ćwiczenie mają dane strukturalne (JSON)** walidowane przy zapisie; pozostałe typy używają `tresc` (Markdown), dzięki czemu istniejący edytor działa bez zmian.
- **Diagram z tekstu** (pierwsza linia = tytuł, kolejne = kroki, `?` = decyzja) zamiast biblioteki do diagramów – działa offline i jest łatwy do edycji.
- **Audio bez pliku czyta lektor przeglądarki** (Web Speech API, `pl-PL`) – kurs demo działa bez nagrań; nauczyciel może wgrać prawdziwe nagranie (mp3/ogg/wav/m4a).
- **Upload przeniesiony do backendu (`/media`)** z białą listą rozszerzeń (bez `.svg`, `.html`) i limitem rozmiaru – wcześniej dowolny plik trafiał do katalogu publicznego frontendu.
- **Quiz kończący temat jest wspólny** – ten sam sprawdzian dla każdego stylu (podstawa adaptacji w Etapie 4).
- **Kurs demo bez filmów** – nie wstawiam linków do cudzych filmów, których nie mogę zweryfikować; typ `wideo` działa (link YouTube / plik / iframe) i nauczyciel może go dodać.
- Usunięte `lazy="noload"` na `Temat.bloki` (przestarzałe w SQLAlchemy 2.1, zwracało puste bloki).

## Weryfikacja (komendy + wynik)
- `pytest` → 141 passed
- `npm run lint` → 0 błędów
- `npm run build` → OK
- Smoke w przeglądarce headless: trzech uczniów (V, A, K) otwiera ten sam temat – każdy widzi bloki wspólne i tylko swojego stylu (V: obraz + diagram; A: „Posłuchaj"; K: „Zrób to sam"); ćwiczenie przechodzi 5 kroków; quiz jest oceniany; nauczyciel widzi wszystkie bloki, podgląd „A" ukrywa bloki V i K; dodany blok zapisuje się ze stylem K. Wynik: OK, brak błędów w konsoli. Zrzuty ekranu obejrzane ręcznie.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. `alembic upgrade head`, `python -m app.seed` (doda kurs demo), uruchom backend i frontend.
2. Zaloguj się jako uczeń, wypełnij ankietę, otwórz kurs „Podstawy programowania w Pythonie" → temat „Zmienne i typy danych".
3. W profilu zmień styl na inny i wróć do tematu – zestaw bloków się zmienia.
4. Jako nauczyciel otwórz ten sam temat: pasek „Podgląd oczami ucznia" → V / A / K.
5. Włącz „Tryb Edycji", dodaj blok „Quiz" lub „Ćwiczenie (K)", kliknij ołówek, ustaw „dla kogo", zapisz.

## Znane problemy / TODO
- Lektor zależy od głosów zainstalowanych w systemie/przeglądarce; bez polskiego głosu czyta domyślnym. Zawsze dostępna jest transkrypcja.
- Generator AI tworzy tylko bloki wspólne (bez stylu).
- Wynik quizu nie jest jeszcze zapisywany – robi to Etap 4.

## Propozycje (poza zakresem)
- Statystyki dla nauczyciela: ile bloków V/A/K ma każdy temat (wykrywanie tematów bez pokrycia któregoś stylu).
- Generator AI tworzący od razu warianty V/A/K (Etap 7).

## Commity (hash + opis)
- 9eb9cf5 Backend: styl bloku, typy multimedialne, filtrowanie pod styl ucznia, quiz, upload do /media, kurs demo
- 9a99a34 Backend: testy personalizacji, quizu, uploadu i kursu demo
- 4b366b3 Frontend: bloki obraz/diagram/audio/ćwiczenie/quiz, styl bloku w edytorze, podgląd V/A/K
- 44eb6ae README i CLAUDE.md: seed kursu demo, MEDIA_ROOT, status etapów
