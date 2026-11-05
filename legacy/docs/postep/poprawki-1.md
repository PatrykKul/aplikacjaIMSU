# Poprawki 1 – po audycie zewnętrznym   (01.10.2026)

## Plan (krótko)
1. Walidacja stylu wysyłanego z wynikiem quizu.
2. `.gitattributes` i normalizacja końców linii.
3. Dopisek w dokumentacji o kwestionowanej teorii stylów uczenia.
4. Weryfikacja i raport.

## Co zrobione (lista, z plikami)
**1. Styl przy zapisie wyniku quizu**
- `backend/app/services/adaptacja.py` – czysta funkcja `dozwolone_style_quizu(styl_ucznia, proponowany, wyprobowane)`.
- `backend/app/routers/kursy.py` – `_styl_quizu`: styl od klienta jest przyjmowany tylko wtedy, gdy należy do dozwolonych; inaczej `400` i **nic się nie zapisuje** (brak zdarzenia, postępu i zmiany wag). Brak stylu w żądaniu = styl ucznia (jak dotąd).
- `backend/app/models.py` + migracja `alembic/versions/0006_proponowany_styl_powtorki.py` – `postepy_tematow.proponowany_styl`: styl, który system zaproponował do powtórki danego tematu (zapisywany przy rekomendacji „spróbuj inaczej").
- Testy: `tests/test_nauka.py` (4 nowe scenariusze), `tests/test_adaptacja.py` (1 nowy), poprawiony scenariusz „wszystkie style wypróbowane" (szedł na skróty stylem, którego system nie proponował).

**2. Końce linii**
- `.gitattributes`: `* text=auto eol=lf` + binarne: png, jpg, jpeg, gif, webp, ico, mp3, ogg, wav, m4a, db.
- `git add --renormalize .` w osobnym commicie; dodatkowo pliki w katalogu roboczym przekonwertowane z CRLF na LF (67 plików), żeby drzewo robocze zgadzało się z repozytorium.

**3. Dokumentacja**
- `docs/dokumentacja.md`, sekcja 10: teoria stylów uczenia (VAK) jest kwestionowana (brak potwierdzenia *meshing hypothesis*) oraz dlaczego projekt mimo to ma sens: pokazuje mechanizm personalizacji, uczeń może ręcznie zmienić styl, adaptacja opiera się na wynikach quizów, model VAK jest wymienny (np. na VARK). Bez linków. W sekcji 5.3 dopisana reguła walidacji stylu; zaktualizowana liczba testów.

## Decyzje i dlaczego
- **Dozwolone style = litery stylu ucznia + styl zaproponowany do powtórki tego tematu + style, w których uczeń już (legalnie) podchodził do quizu w tym temacie.** Trzeci składnik jest potrzebny, żeby po udanej powtórce w stylu A przycisk „Spróbuj ponownie" na tej samej stronie nie kończył się błędem.
- **Propozycja powtórki jest zapisywana w bazie** (kolumna `proponowany_styl`), a nie wyliczana na nowo z wag — wagi zmieniają się po każdym quizie, więc wyliczenie „po fakcie" mogłoby dać inny styl niż ten, który uczeń zobaczył.
- **Propozycja dotyczy tylko swojego tematu** — styl zaproponowany w temacie 1 nie pozwala przypisać wyniku temu stylowi w temacie 2 (jest test).
- **Podgląd tematu w innym stylu (`GET /tematy/{id}?styl=`) zostaje dla ucznia otwarty** — samo oglądanie nie wpływa na wagi; ograniczony jest tylko zapis wyniku. Jeżeli uczeń sam wpisze w adresie niedozwolony styl i rozwiąże quiz, zobaczy komunikat „Quiz można rozwiązać tylko w swoim stylu albo w stylu zaproponowanym do powtórki".
- **Konwersja plików roboczych do LF** zamiast `git reset --hard` — ten sam efekt bez operacji destrukcyjnej.

## Weryfikacja (komendy + wynik)
- `pytest` → 229 passed
- `npm run lint` → 0 błędów (3 ostrzeżenia `<img>`)
- `npm run build` → OK
- `git status` → czysto; `git ls-files --eol` → 131 plików `i/lf w/lf`, 4 binarne, 0 z CRLF.
- Regresja w przeglądarce headless (personalizacja, adaptacja z powtórką w innym stylu, panele) → OK.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. `alembic upgrade head` (migracja 0006).
2. Swagger (`/docs`), token ucznia o stylu V: `POST /bloki/{id_quizu}/quiz` z `"styl": "K"` → 400; z `"styl": "V"` lub bez pola → 200.
3. Odpowiedz źle (system zaproponuje np. A) → to samo żądanie z `"styl": "A"` → 200.
4. `git status` po świeżym `git clone` na Windowsie → brak zmienionych plików.

## Znane problemy / TODO
- Uczniowie, którzy dostali propozycję powtórki **przed** tą poprawką, nie mają zapisanego `proponowany_styl`; jeśli nie zdążyli z niej skorzystać, propozycja odnowi się po kolejnym niezaliczonym quizie. Dotyczy tylko istniejących lokalnych baz.

## Propozycje (poza zakresem)
- Ograniczenie także podglądu `?styl=` dla ucznia do dozwolonych stylów, jeśli swobodne podglądanie innych wersji tematu jest niepożądane.

## Commity (hash + opis)
- 923c108 Quiz: styl wyniku przyjmowany tylko, gdy uczeń mógł w nim przerabiać temat (własny lub zaproponowany do powtórki)
- ddfb31a Dokumentacja: zastrzeżenie o teorii stylów uczenia i uzasadnienie projektu
- 34a5302 Końce linii: .gitattributes (LF) i normalizacja repozytorium
