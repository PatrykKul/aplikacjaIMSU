# Etap 4 – adaptacja w czasie   (01.10.2026)

## Plan (krótko)
1. Czyste funkcje adaptacji w `services/adaptacja.py` + testy scenariuszy.
2. Baza: wagi V/A/K na użytkowniku, `zdarzenia_nauki`, `postepy_tematow`, `Blok.poziom`.
3. API: quiz ucznia zapisuje wynik i zwraca rekomendację z uzasadnieniem; ścieżka ucznia; decyzja o przełączeniu stylu; zdarzenia; ręczne ukończenie tematu bez quizu.
4. Frontend: karta „co dalej" po quizie, propozycja zmiany stylu, „dlaczego to widzisz", powtórka tematu w innym stylu, poziom bloku w edytorze.

## Co zrobione (lista, z plikami)
**Backend**
- `app/services/adaptacja.py` – reguły jako czyste funkcje: `czy_zaliczony` (próg 70%), `wagi_startowe`, `aktualizuj_wagi` (+1/−1, zakres 0–30), `styl_do_powtorki` (drugi najwyższy, z pominięciem już wypróbowanych), `propozycja_zmiany_stylu`, `poziom_trudnosci`, `blok_na_poziomie`, `liczy_sie_do_wag`, `rekomendacja_po_quizie`, `uzasadnienie_stylu`, `uzasadnienie_poziomu`.
- `app/services/nauka.py` – operacje na bazie (wyniki quizów, postęp, następny temat).
- `app/models.py` – `Uzytkownik.waga_v/a/k`, `Uzytkownik.odrzucona_propozycja`, `Blok.poziom`, `ZdarzenieNauki`, `PostepTematu`; migracja `0005_adaptacja.py` (z uzupełnieniem wag istniejących uczniów z ostatniej ankiety).
- `app/routers/kursy.py`:
  - `POST /bloki/{id}/quiz` – dla ucznia: zdarzenie `wynik_quizu`, postęp tematu, aktualizacja wag, `rekomendacja` (następny temat / powtórka w innym stylu / koniec kursu) z polem `dlaczego`, ewentualna `propozycja_stylu`;
  - `GET /tematy/{id}` – filtr po poziomie trudności i blok `personalizacja` (styl, poziom, lista „dlaczego to widzisz").
- `app/routers/nauka.py` – `POST /nauka/zdarzenia`, `GET /nauka/sciezka`, `POST /nauka/propozycja-stylu`, `POST /tematy/{id}/ukoncz`.
- `app/routers/ankieta.py` – ankieta ustawia wagi startowe = punkty.
- `app/database.py` – `PRAGMA foreign_keys=ON` (kaskadowe usuwanie zdarzeń i postępu razem z tematem).
- `app/seed_kurs.py` – w każdym temacie dodatkowy przykład łatwiejszy (poziom 1) i rozszerzający (poziom 3).

**Frontend**
- `src/components/nauka/RekomendacjaCard.tsx` – „Temat zaliczony! Następny: …" / „Spróbuj inaczej: …" + „Dlaczego to widzisz: bo quiz z tematu X: 45%".
- `src/components/nauka/PropozycjaStylu.tsx` – „Lepiej Ci idzie z materiałami słuchowymi – przełączyć?" z przyciskami Tak / Nie.
- `src/components/temat/TematLessonView.tsx` – ramka „Dlaczego to widzisz", zdarzenia (otwarcie tematu, czas, odtworzenie audio/wideo, ukończenie ćwiczenia), przycisk „Oznacz temat jako ukończony" (tematy bez quizu), wybór poziomu bloku i plakietka poziomu w edytorze.
- `src/app/tematy/[tematId]/TematPageClient.tsx` – powtórka w innym stylu przez adres `/tematy/{id}?styl=A`.
- `src/app/profil/page.tsx` – „Wynik ankiety: … · dopasowany po quizach: …".

**Testy**: `tests/test_adaptacja.py` (58 przypadków na czystych funkcjach, w tym pełny scenariusz), `tests/test_nauka.py` (20 scenariuszy przez API).

## Decyzje i dlaczego
- **Trzecie źródło stylu: `adaptacja`.** Gdy uczeń przyjmie propozycję systemu, zapisujemy `styl_zrodlo = "adaptacja"` (obok `ankieta` / `reczny`). Dzięki temu kolejne propozycje nadal działają, a ręczny wybór (`reczny`) dalej je blokuje.
- **Propozycja tylko przy samodzielnym liderze wag** spoza obecnego stylu; przy remisie nie pytamy. Odrzuconej propozycji nie powtarzamy (dopóki nie pojawi się inny lider).
- **Waga zmienia się tylko przy pierwszym sukcesie i pierwszej porażce w danym temacie i stylu** – powtarzanie tego samego quizu nie „nabija" wag.
- **Styl przerabiania tematu** = styl widoku wysłany z quizem (przy powtórce `?styl=A` punkt dostaje A); styl mieszany aktualizuje oba style.
- **Poziom trudności liczony z dwóch ostatnich quizów** (dowolnych tematów): oba < 70% → poziom 1 (dodatkowe łatwiejsze przykłady), oba ≥ 90% → poziom 3 (rozszerzenia), inaczej 2. Bloki bez poziomu i z poziomem 2 widzi każdy.
- **Temat raz zaliczony pozostaje zaliczony**; zapisujemy najlepszy i ostatni wynik oraz liczbę prób.
- **Ręczne „ukończone" tylko dla tematów bez quizu** – z quizem o zaliczeniu decyduje wynik.
- **Zdarzenia zbieramy tylko dla uczniów**; wyniku quizu nie da się zgłosić z przeglądarki (zapisuje go wyłącznie serwer).
- Nauczyciel rozwiązujący quiz dostaje tylko ocenę – bez śladów w adaptacji.

## Weryfikacja (komendy + wynik)
- `pytest` → 216 passed
- `npm run lint` → 0 błędów (3 ostrzeżenia `<img>`)
- `npm run build` → OK
- Smoke w przeglądarce headless (uczeń z ankietą V 8 / A 7 / K 5): ramka „Dlaczego to widzisz" pokazuje styl z ankiety → quiz 0% → „Spróbuj inaczej: … słuchowiec" + „bo quiz z tematu …: 0%" → powtórka pod `?styl=A` pokazuje blok audio zamiast diagramu → quiz 100% → „Temat zaliczony! Następny: …" + „Lepiej Ci idzie z materiałami słuchowymi – przełączyć?" (wagi V 7 / A 8 / K 5) → „Tak" → styl A, źródło `adaptacja` → następny temat w nowym stylu; ścieżka: 1 temat zaliczony. Regresja etapów 1–3: OK.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. `alembic upgrade head`, `python -m app.seed`; jeżeli kurs demo powstał przed Etapem 4, usuń go jako nauczyciel i uruchom seed ponownie (doda przykłady na poziomach 1 i 3).
2. Zarejestruj ucznia i wypełnij ankietę tak, by wynik był wyrównany (np. V 8 / A 7 / K 5).
3. Otwórz pierwszy temat kursu demo, odpowiedz źle na quiz → karta „Spróbuj inaczej" → kliknij.
4. W wersji dla drugiego stylu odpowiedz dobrze → „Temat zaliczony" i pytanie o przełączenie stylu.
5. Dwa słabe quizy z rzędu → w kolejnym temacie pojawia się przykład „Zacznijmy prościej"; dwa wyniki ≥ 90% → przykład „Dla chętnych".
6. `GET /nauka/sciezka` (Swagger) – wagi, poziom, następny krok z uzasadnieniem.

## Znane problemy / TODO
- Ścieżka ucznia (`/nauka/sciezka`) ma API, a widok w panelu ucznia powstaje w Etapie 5.
- Zmiana wag o ±1 przy ankiecie z dużą przewagą jednego stylu (np. 12/5/3) wymaga kilku quizów, zanim pojawi się propozycja – to zamierzone (stabilność), ale na prezentacji warto użyć wyrównanego wyniku.
- `TODO(prowadzący)`: progi (70% zaliczenie, 90% rozszerzenia) i krok wag są stałymi w `adaptacja.py` – do potwierdzenia.

## Propozycje (poza zakresem)
- Wykorzystanie zdarzeń (czas w temacie, odtworzenia) w regułach adaptacji – dziś są tylko zbierane i raportowane.
- Zanikanie starych wyników (większa waga ostatnich quizów).

## Commity (hash + opis)
- a52dbd3 Backend: adaptacja – zdarzenia nauki, wagi V/A/K po quizach, poziom trudności, rekomendacje z uzasadnieniem, ścieżka ucznia
- 66da261 Backend: testy scenariuszy adaptacji (czyste funkcje i API)
- 97aec44 Frontend: rekomendacja po quizie, propozycja zmiany stylu, „dlaczego to widzisz", poziom bloku, zdarzenia nauki
