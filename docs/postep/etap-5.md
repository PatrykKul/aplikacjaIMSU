# Etap 5 – panele ucznia, nauczyciela, admina   (01.10.2026)

## Plan (krótko)
1. Backend: lista uczniów i szczegóły ucznia dla nauczyciela, blokowanie kont dla admina.
2. Frontend: panel ucznia (ścieżka, postęp, styl), panel nauczyciela (uczniowie ze stylami, edytor ankiety), panel admina (użytkownicy, role), nawigacja zależna od roli.

## Co zrobione (lista, z plikami)
**Backend**
- `app/routers/nauczyciel.py` – `GET /nauczyciel/uczniowie` (styl z ankiety + styl aktualny i jego źródło, punkty ankiety, wagi, zaliczone tematy, próby, ostatnia aktywność), `GET /nauczyciel/uczniowie/{id}` (ścieżka ucznia, historia ankiet, 30 ostatnich zdarzeń).
- `app/routers/uzytkownicy.py` – `PUT /uzytkownicy/{id}/aktywny` (blokada / odblokowanie konta; nie można zablokować siebie).
- `app/routers/nauka.py` – `zbuduj_sciezke` współdzielone przez panel ucznia i widok nauczyciela.
- Testy: `tests/test_panele.py` (7 scenariuszy).

**Frontend**
- **Uczeń** – `src/app/panel/page.tsx`: „Twój następny krok" z uzasadnieniem, karta stylu (aktualny + wynik ankiety), wagi V/A/K, poziom materiałów, propozycja zmiany stylu, „Moja ścieżka" (`src/components/nauka/SciezkaView.tsx`). Na stronie działu przy tematach: „Zaliczony · najlepszy wynik: …" / „W trakcie".
- **Nauczyciel** – `src/app/nauczyciel/page.tsx`: skróty do kursów i ankiety + tabela uczniów (wynik ankiety, aktualny styl ze źródłem, wagi, postęp); `src/app/nauczyciel/uczniowie/[id]/` – szczegóły ucznia; `src/app/nauczyciel/ankieta/page.tsx` – edytor pytań ankiety (dodawanie, edycja, wyłączanie, usuwanie).
- **Admin** – `src/app/admin/uzytkownicy/page.tsx`: lista użytkowników, zmiana roli, blokowanie kont.
- `src/components/Navbar.tsx` – linki zależne od roli; `src/components/auth/AuthGate.tsx` – strona startowa wg roli (uczeń → `/panel`, nauczyciel → `/nauczyciel`, admin → `/admin/uzytkownicy`), `/panel` tylko dla ucznia.
- `src/lib/ui.ts` – wspólne klasy i format daty.

Edytor kursów z wyborem stylu bloku i podglądem V/A/K (część panelu nauczyciela) powstał w Etapie 3.

## Decyzje i dlaczego
- **„Swoi uczniowie" = wszyscy uczniowie** (brak modelu klas) – `TODO(decyzja)` w `routers/nauczyciel.py`, wpis w PYTANIA.md.
- **Admin widzi też panel nauczyciela** („widzi wszystko").
- **Blokowanie kont** dodane do panelu admina jako część „zarządza użytkownikami"; pole `aktywny` istniało od Etapu 1. Zablokowany użytkownik traci dostęp natychmiast (także z ważnym tokenem).
- **Widok ucznia u nauczyciela jest tylko do odczytu** – nauczyciel nie zmienia stylu ucznia (decyduje uczeń).
- Nie dodałem usuwania użytkowników – nieodwracalne, a blokada wystarcza.

## Weryfikacja (komendy + wynik)
- `pytest` → 223 passed
- `npm run lint` → 0 błędów (3 ostrzeżenia `<img>`)
- `npm run build` → OK
- Smoke w przeglądarce headless – 24 kroki: panel ucznia (następny krok z uzasadnieniem, styl ręczny + wynik ankiety, postęp 1/4, „Ucz się dalej", oznaczenie zaliczonego tematu, brak wejścia do paneli nauczyciela i admina); panel nauczyciela (wiersz ucznia: „wzrokowiec, V 12 / A 5 / K 3" + „słuchowiec, wybrany ręcznie", szczegóły ze ścieżką i zdarzeniem quizu, brak wejścia do panelu admina); edytor ankiety (dodanie, wyłączenie, usunięcie pytania); panel admina (zmiana roli, blokada i odblokowanie konta, własna rola zablokowana). Regresja etapów 1–4: OK. Zrzuty ekranu obejrzane.

## Jak sprawdzić ręcznie (kroki dla człowieka)
1. Uczeń (po ankiecie) → `/panel`: następny krok, styl, wagi, ścieżka.
2. Nauczyciel → `/nauczyciel`: tabela uczniów; kliknij imię → szczegóły; „Ankieta VAK" → dodaj i usuń pytanie.
3. Admin → `/admin/uzytkownicy`: zmień rolę nowego konta, zablokuj je i spróbuj się na nie zalogować.

## Znane problemy / TODO
- Tabela uczniów nie ma filtrowania ani stronicowania (wystarczające dla małej grupy).
- Na wąskich ekranach linki nawigacji są ukryte (poniżej 1024 px) – do poprawy w Etapie 6.

## Propozycje (poza zakresem)
- Klasy / zapisy na kurs, żeby nauczyciel widział tylko swoich uczniów.
- Zestawienie dla nauczyciela: które tematy sprawiają najwięcej trudności (średni wynik quizu per temat i styl).

## Commity (hash + opis)
- 3ad935d Backend: panel nauczyciela (uczniowie, szczegóły ucznia) i blokowanie kont przez admina + testy
- 0e69783 Frontend: panel ucznia, panel nauczyciela, edytor ankiety, panel admina, nawigacja wg roli
