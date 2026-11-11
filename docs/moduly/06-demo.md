# Dane demo (`backend/app/demo`)

Konta, kursy, materiały, quizy i klasa do pokazu. Decyzje: D14 (wyjątek), D21, D22, D30, D38. Scenariusz pokazu: `SCENARIUSZ-POKAZU.md`.

## Uruchomienie
Z katalogu `backend/` (po `alembic upgrade head`, bo pytania ankiety wstawia migracja):

```
python -m app.demo.seed
python -m app.demo.seed --reset-students
python -m app.demo.seed --refresh-demo-media
```

- Bez flag: tworzy brakujące konta, kursy, lekcje, bloki (po `id`), quizy i klasę demo; niczego nie nadpisuje, bloki dodane ręcznie przez nauczyciela zostają. Kurs rozpoznawany po (nauczyciel demo, tytuł), klasa — po (nauczyciel demo, nazwa).
- `--reset-students`: czyści ankietę, profil i próby quizów dwóch kont uczniów demo (stan startowy pokazu).
- `--refresh-demo-media`: wgrywa ponownie demo-nagrania MP3 i filmy (po ponownym nagraniu); stare pliki zostają w `uploads/` i `files`.
- Seed korzysta z serwisów modułów (te same walidacje co w aplikacji). Hasło kont demo jest w kodzie — seed nie trafia na serwer produkcyjny.

## Konta (hasło `Demo123!`)

| Konto | Rola | Stan |
|---|---|---|
| `nauczyciel.demo@imsu.pl` (Anna Nowak) | nauczyciel | właściciel 3 kursów (2 opublikowane, 1 prywatny kurs klasy) i klasy „Klasa 7a” |
| `admin.demo@imsu.pl` (Adam Admin) | administrator | — |
| `uczen.nowy@imsu.pl` (Ola Kowalska) | uczeń | bez ankiety — pokaz wymuszenia; w „Klasie 7a” |
| `uczen.demo@imsu.pl` (Kuba Wiśniewski) | uczeń | ankieta V 9 / A 8 / K 3 (styl V), quizy 85, 55, 40, 45% → wagi V 7 / A 8 / K 3 → propozycja A; w „Klasie 7a” |

## Kursy
- Matematyka: funkcja liniowa — Wzór i wykres; Współczynnik kierunkowy a; Miejsce zerowe.
- Angielski: Present Perfect — Budowa zdania; Present Perfect czy Past Simple?
- Programowanie: pętle w Pythonie — Pętla for; Pętla while. **Kurs prywatny „Klasy 7a”** (poza katalogiem).

Każda lekcja: tekst wspólny, obrazy (V), nagrania MP3 głosem neuronowym pl-PL (A), karty ćwiczeń PDF (K), materiały mieszane (V+K, A+K); dwa filmy V+A ze slajdem tytułowym; quiz: 3 pytania wspólne + po jednym V, A, K.

## Klasa demo
„Klasa 7a” nauczyciela demo: obaj uczniowie demo i kurs „Programowanie: pętle w Pythonie”. Kurs staje się **prywatny tylko przy tworzeniu klasy** (także w bazie, w której był opublikowany) — nauczyciel, który opublikuje go ponownie, zachowa tę zmianę przy kolejnym uruchomieniu seeda. Przy każdym uruchomieniu seed dokłada brakujących uczniów i kurs (`ensure_classroom`).

## Pliki
- `courses.py` — treść kursów i quizów; `seed.py` — logika seeda.
- `assets/` — 28 plików (PNG, PDF, MP3, MP4; ok. 4 MB) w repozytorium; przy ponownym nagrywaniu każda wersja zostaje w historii gita.
- Generatory (`generate_assets.py`, `generate_audio.py`, `generate_videos.py`) — jednorazowe narzędzia; wymagają Pillow, edge-tts (internet), imageio-ffmpeg i fontów Windows, czyli pakietów spoza `requirements.txt` (osobny venv narzędziowy).

## Testy
`backend/tests/demo/test_seed.py`: kursy z plikami (opublikowane poza kursem klasy) i quizem w każdej lekcji, klasa z dwoma uczniami i prywatnym kursem (poza katalogiem, widoczny dla ucznia klasy), ponownie opublikowany kurs klasy zostaje opublikowany, filmy V+A, audio jako MP3, nowy uczeń bez ankiety, uczeń demo z propozycją A, idempotencja (także klasy), dokładanie brakującego quizu, odświeżenie mediów nie rusza bloków nauczyciela, reset czyści tylko dane stylu.

## Ograniczenia
Seed przerwany w trakcie tworzenia kursu zostawia kurs uznawany za istniejący — trzeba go zarchiwizować i uruchomić seed ponownie.
