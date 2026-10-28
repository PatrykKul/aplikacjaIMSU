> **Najpierw sprawdź, czy istnieje katalog `docs/v2/`.** Jeśli tak, zacznij od `docs/v2/00-START.md`, a w razie sprzeczności dokumenty z `docs/v2/` mają pierwszeństwo przed tym plikiem. Jeśli katalogu nie ma, ten plik obowiązuje bez zmian.

# Projekt zaliczeniowy – Inteligentne multimedialne systemy uczące (IMSU)

Studia magisterskie, Informatyka UwB, 1 semestr (2026/27). Autor: Patryk Kulesza.
Notatka z wymaganiami i pytaniami do prowadzącego: `../Projekt-zaliczeniowy.md` – przeczytaj ją przed startem.

## Cel aplikacji
Platforma z kursami, która **dopasowuje się do ucznia**: na start według stylu uczenia (ankieta VAK), potem według tego, jak mu faktycznie idzie (adaptacja – sekcja niżej). Rdzeń jest regułowy (działa offline, jest przewidywalny i testowalny); LLM to opcjonalny dodatek.
1. Rejestracja / logowanie.
2. Po rejestracji uczeń **musi** wypełnić ankietę (~20 pytań) – flaga `ankieta_wypelniona` na użytkowniku.
   Jeśli ktoś się zarejestrował i nie dokończył ankiety, przy **każdym** kolejnym logowaniu flaga wykrywa brak i przekierowuje na ankietę.
   Backend też pilnuje: endpointy materiałów dla ucznia bez ankiety zwracają 403 z kodem `ANKIETA_WYMAGANA`.
3. Ankieta = test VAK: każda odpowiedź daje punkt dla jednego stylu – **V** wzrokowiec, **A** słuchowiec, **K** kinestetyk.
   Wynik: punkty V/A/K + styl dominujący (remis → styl mieszany / pokazujemy oba).
4. Materiały wyświetlają się zależnie od stylu (patrz „Model danych – personalizacja").
5. Uczeń może powtórzyć ankietę (nowy wynik nadpisuje styl, historia zostaje).
6. **Uczeń może ręcznie zmienić styl**, jeśli dobrany mu nie pasuje (profil → „Mój styl uczenia": V / A / K).
   Zapisujemy `styl_uczenia` + `styl_zrodlo` (`ankieta` / `reczny`), a w UI pokazujemy np. „Wynik ankiety: wzrokowiec · wybrany ręcznie: słuchowiec".
   Ręczna zmiana nie kasuje wyniku ankiety. Nauczyciel widzi obie informacje.

## Model danych – personalizacja
Hierarchia Kurs → Dział → Temat zostaje. Rozgałęzienie robimy na poziomie **Bloku**:
- `Blok.styl`: `V` / `A` / `K` / `null` (null = wspólny dla wszystkich, np. definicja, zadanie sprawdzające).
- Uczeń widzi w temacie: bloki wspólne + bloki swojego stylu (kolejność wg `kolejnosc`).
- Nowe typy bloków (multimedia): `obraz`, `diagram`, `wideo` (YouTube/plik) → głównie V; `audio` (nagranie/podcast) → A;
  `cwiczenie` interaktywne / `quiz` / zadanie „zrób sam" krok po kroku → K. Istniejące typy (teoria/przyklad/uwaga/zadanie) zostają.
- Nauczyciel w edytorze tematu przy bloku wybiera styl i widzi podgląd tematu „oczami" V / A / K.
Nowe tabele: `uzytkownicy` (email, haslo_hash, rola, ankieta_wypelniona, styl_uczenia, styl_zrodlo), `pytania_ankiety` + `odpowiedzi_ankiety`
(treść odpowiedzi + przypisany styl), `wyniki_ankiety` (user_id, punkty_v, punkty_a, punkty_k, styl_dominujacy, data).
Seed: 20 pytań VAK + 1 przykładowy kurs, w którym każdy temat ma bloki dla V, A i K – żeby na prezentacji było widać różnicę.


## Adaptacja w czasie (rdzeń „inteligencji", bez LLM)
1. **Start**: wagi V/A/K z ankiety (punkty).
2. **Zdarzenia nauki** – tabela `zdarzenia_nauki` (user, blok/temat, typ zdarzenia: otwarcie, odtworzenie wideo/audio, ukończenie ćwiczenia, wynik quizu, czas).
3. **Quiz na końcu tematu** (blok `quiz`, wspólny). Wynik ≥ 70% → temat zaliczony, proponujemy następny. < 70% → proponujemy **powtórkę w innym stylu** (drugi najwyższy) – „spróbuj inaczej".
4. **Aktualizacja wag**: po każdym quizie styl, w którym uczeń przerabiał temat, dostaje +1 przy sukcesie / −1 przy porażce (z ograniczeniem zakresu). Gdy inny styl zacznie dominować → komunikat „Lepiej Ci idzie z materiałami słuchowymi – przełączyć?". **Uczeń decyduje**; ręczny wybór stylu ma pierwszeństwo.
5. **Poziom trudności**: bloki z polem `poziom` (1–3). Dwa słabe quizy z rzędu → łatwiejsze przykłady; dobre → rozszerzenia.
6. **Wyjaśnialność**: przy rekomendacji krótkie „dlaczego to widzisz" (np. „bo quiz z tematu X: 45%").
Logika adaptacji jako czyste funkcje w `services/` + testy pytest na konkretnych scenariuszach.

## LLM – opcjonalny dodatek (ostatni etap, jeśli starczy czasu)
- 2–3 pytania otwarte w ankiecie → Gemini zwraca JSON korekty wag V/A/K (walidowany). Brak klucza / offline → pytania otwarte pomijane w wyniku.
- Przycisk „Wyjaśnij inaczej" przy bloku → Gemini tworzy alternatywne wyjaśnienie w stylu ucznia. Fallback: pokazujemy bloki innego stylu.
- Personalizacja i adaptacja **nigdy nie zależą** od dostępności LLM.

## Role (aktorzy)
| Rola | Może |
|---|---|
| **Admin** | zarządza użytkownikami i rolami, widzi wszystko |
| **Nauczyciel** | tworzy/edytuje kursy, działy, tematy, bloki; tworzy ankiety; widzi wyniki ankiet i ścieżki swoich uczniów |
| **Uczeń** | wypełnia ankietę, widzi swoją ścieżkę i materiały, oznacza postęp |

## Stos i struktura
Szczegóły: `docs/dokumentacja.md` (architektura, model danych, reguły adaptacji) i `README.md` (uruchomienie, konta testowe).
**Backend** `backend/` – FastAPI + SQLAlchemy + SQLite (`stylnauki.db`, `DATABASE_URL` w `.env`), migracje Alembic, testy pytest w `backend/tests`.
- `routers/`: `auth`, `uzytkownicy`, `ankieta`, `kursy`, `nauka`, `nauczyciel`; `deps.py` (role, bramka ankiety), `security.py` (bcrypt, JWT).
- `services/`: czyste funkcje `vak.py`, `personalizacja.py`, `quiz.py`, `adaptacja.py`; `nauka.py` (operacje na bazie); `ai_generator.py` (Gemini, opcjonalny).
- `seed.py` + `seed_ankieta.py` + `seed_kurs.py`: konta testowe, 20 pytań VAK, kurs demonstracyjny.

**Frontend** `frontend/` – Next.js 16 + React 19 + Tailwind 4 + KaTeX/Markdown + dnd-kit + zustand + react-query.
Strony: `app/ankieta`, `app/profil`, `app/panel`, `app/kursy`, `app/dzialy`, `app/tematy`, `app/nauczyciel`, `app/admin/uzytkownicy`; API w `lib/api.ts`; ochrona stron w `components/auth/AuthGate.tsx`.
⚠ Przeczytaj `frontend/AGENTS.md` – ta wersja Next.js ma zmiany łamiące zgodność.

## Do zbudowania
1. **Auth + role**: rejestracja/logowanie (JWT, hasła bcrypt), rola w tokenie, zabezpieczenie endpointów zależnie od roli, seed: 1 admin, 1 nauczyciel, 1 uczeń.
2. **Ankieta VAK**: 20 pytań jednokrotnego wyboru (seed), flaga `ankieta_wypelniona`, liczenie punktów V/A/K, zapis wyniku. Logika liczenia jako czysta funkcja + testy.
3. **Personalizacja**: pole `styl` na bloku, filtrowanie bloków pod styl ucznia, nowe typy bloków multimedialnych.
4. **Panel ucznia**: ankieta (wymuszona flagą) → wynik („jesteś wzrokowcem: V 12 / A 5 / K 3") → kursy → tematy z materiałami w jego stylu → postęp.
5. **Panel nauczyciela**: kursy (istniejący edytor + wybór stylu bloku + podgląd V/A/K), lista uczniów z ich stylami.
6. **Panel admina**: lista użytkowników, zmiana ról.

## Zasady pracy
- **Tryb autonomiczny (od 01.10.2026).** Autor nie czyta czatu na bieżąco – zadania i audyty robi osobny agent nadzorujący, który czyta pliki w `docs/postep/`. Dlatego:
  - **Nie czekaj na akceptację planu** – plan zapisz w raporcie etapu i wykonuj.
  - Pracuj **etapami** (niżej), po kolei. Etap kończy się dopiero, gdy przechodzą: `pytest`, `npm run lint`, `npm run build` (i ręczny smoke test przez curl/uruchomienie, jeśli to możliwe).
  - Po każdym etapie zapisz raport `docs/postep/etap-N.md` (szablon niżej) i zaktualizuj `docs/postep/STATUS.md`, potem commit.
  - Decyzje, których nie da się rozsądnie podjąć samemu → wpisz do `docs/postep/PYTANIA.md`, wybierz najbezpieczniejszy wariant, oznacz w kodzie `TODO(decyzja)` i jedź dalej. Zatrzymaj się tylko przy blokerze nie do obejścia (wtedy opisz go w STATUS.md).
  - Nie wychodź poza zakres etapów; pomysły spoza zakresu → sekcja „Propozycje" w raporcie.

### Szablon `docs/postep/etap-N.md`
```
# Etap N – <nazwa>   (data, godzina)
## Plan (krótko)
## Co zrobione (lista, z plikami)
## Decyzje i dlaczego
## Weryfikacja (komendy + wynik: pytest X passed, lint OK, build OK)
## Jak sprawdzić ręcznie (kroki dla człowieka)
## Znane problemy / TODO
## Propozycje (poza zakresem)
## Commity (hash + opis)
```
### `docs/postep/STATUS.md` – zawsze aktualny, krótki
Ostatni ukończony etap · co w toku · blokery · otwarte pytania (link do PYTANIA.md) · jak uruchomić teraz.
- Repo git od pierwszego etapu, małe commity z sensownymi opisami.
- Testy backendu w pytest dla nowej logiki (auth, uprawnienia, flaga ankiety, liczenie wyniku VAK, filtrowanie bloków pod styl).
- Żadnych sekretów w repo (`.env` w `.gitignore`, `env.example` z nazwami zmiennych).
- UI po polsku. W kodzie krótkie angielskie komentarze nazywające sekcje – bez długich wywodów.
- Czego nie wiadomo (wymagania prowadzącego – patrz notatka) – **nie zgaduj**, zostaw `TODO(prowadzący)` i dopisz pytanie.
- README w katalogu głównym: jak uruchomić backend i frontend, konta testowe.

## Etapy
- **Etap 0** ✅ – czysty start: repo git, README, migracje Alembic, pusta baza + szkielet seeda, porządki w backendzie (jeden endpoint zmiany kolejności kursów, błędy 500 bez treści wyjątku, wywołanie Gemini nie blokuje serwera).
- **Etap 1** ✅ – auth + role + seed użytkowników.
- **Etap 2** ✅ – ankieta VAK + flaga + wymuszenie po logowaniu (frontend i backend).
- **Etap 3** ✅ – personalizacja bloków (`styl`, nowe typy multimedialne, filtrowanie) + seed przykładowego kursu V/A/K.
- **Etap 4** ✅ – adaptacja: zdarzenia nauki, quiz po temacie, aktualizacja wag, poziom trudności, „dlaczego to widzisz".
- **Etap 5** ✅ – panele ucznia, nauczyciela, admina.
- **Etap 6** ✅ – dopracowanie UI, dokumentacja do zaliczenia.
- **Etap 7 (opcjonalny)** – dodatek LLM.

Generator AI (`generuj_materialy_ai`) zostaje jako narzędzie dla nauczyciela.
