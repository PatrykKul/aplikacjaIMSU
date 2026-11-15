# Plan etapów i status

## Etapy

Termin: **koniec listopada 2026**. Daty orientacyjne. Koncepcja: `02-koncepcja.md`. Plan zmieniony 10.11: etap 4 kolegi (styl uczenia się i quizy) zastąpił dawne etapy 5–8, a dostęp do kursów przybrał formę klas. 12.11: etap 9 (v3) przebudował adaptację, zastąpił klasy zapisami na kurs i wyprzedził etap 8. Tabela jest jedynym zapisem historii etapów w dokumentacji; opis wyników — w `moduly/`, szczegóły — w historii gita.

| # | Etap | Zakres | Moduły | Plan | Status |
|---|---|---|---|---|---|
| 0 | Szkielet | Docker + PostgreSQL, FastAPI, Alembic, testy, Next.js | `core` | — | **zrobione** 29.10 |
| 1 | Konta i role | rejestracja z wyborem roli, logowanie, sesja, blokada, `create-admin`, strona `/admin/users` | `identity` | — | **zrobione** 01.11 |
| 2 | Administracja kont | stałe role; nauczyciele i uczniowie osobno; tworzenie i edycja kont przez administratora; blokada | `identity`, frontend | 06–07.11 | **zrobione** 07.11 |
| 3 | Kursy nauczyciela i edytor lekcji | kurs → lekcje, CRUD kursów i lekcji, edytor bloków (TipTap, załączniki z wgrywaniem plików, formy V/A/K), podgląd; widok kursu i lekcji | `curriculum`, `content`, frontend | 09–12.11 | **zrobione** 09.11 |
| 4 | Styl uczenia się i quizy | ankieta VAK (wymagana), profil i ręczna zmiana stylu, personalizacja lekcji, quiz lekcji z edytorem, adaptacja wag i propozycja zmiany stylu, dane demo, scenariusz pokazu | `learning_style`, `assessment`, `demo`, frontend | 08–09.11 | **zrobione** 09.11 (kolega) |
| 5 | Poprawki stylu i quizów | poprawki po przeglądzie etapu 4; materiały innych stylów **zwinięte** zamiast ukrytych, zapis rozwinięć i styl efektywny w adaptacji i quizie; kontrolki shadcn | `learning_style`, `assessment`, frontend | 10–12.11 | **zrobione** 10.11 |
| 6 | Klasy i dostęp do kursów | klasy nauczyciela (uczniowie z wyszukiwaniem po e-mailu, przypisane kursy), dostęp ucznia do kursów swoich klas, katalog kursów opublikowanych, „Moje klasy” ucznia, klasa demo; administrator bez klas (O6 odroczona) | `curriculum`, `identity`, `demo`, frontend | 13–18.11 | **zrobione** 11.11 |
| 7 | Wygląd | paleta (indygo, informacja zwrotna, kolory form V / A / K), ikony stanów pustych i błędów, logo, strona startowa, dashboard i ścieżka kursu, kafelki ról na `RadioGroup` | frontend | 19–22.11 | **zrobione** 11.11 |
| 9 | **v3: przebudowa adaptacji** | jeden styl naraz i profil procentowy; lekcja w trzech wersjach V / A / K z pulą pytań; reguły R1–R11 (sugestia „przerób w formie X”, propozycja zmiany stylu tylko dla formy potwierdzonej, okres próbny, podpowiedź z kursu, blokada kolejności, gotowość lekcji); dziennik decyzji; statystyki ucznia i panel kursu; zapisy na kurs zamiast klas; zatwierdzanie nauczycieli; nowe dane demo 3 × 4 lekcje i scenariusz pokazu | wszystkie, nowy `authoring`, frontend, `demo` | 12.11 | **zrobione** 12.11, scalone do `main` 15.11 |
| 10 | **Statystyki „premium” i język komunikatów** | „Moje postępy”: podsumowanie, tabela form, „Do powtórki”; panel kursu: trudność lekcji, analiza pytań, macierz lekcja × forma, „wymaga uwagi”; R5 stopniowana (soft / strong), R12 seria porażek; dane demo 13 uczniów w Matematyce; przegląd wszystkich tekstów (forma K = „praktyczna”) | `learning_style`, `assessment`, frontend, `demo` | 15.11 | **zrobione** 15.11 (gałąź `feat/statystyki`, czeka na audyt Patryka) |
| 8 | Dokumentacja i pokaz | dokumentacja do oddania, kopia danych demo, scenariusz prezentacji (dokumentacja i scenariusz zaktualizowane w etapie 9) | docs | 23–27.11 | **następny** |
| — | Zapas | poprawki | | 28–30.11 | |
| 11 | Opcjonalne (O3) | test końcowy kursu, mentor, powtórki (baza pytań, panel nauczyciela i powtórka w innej formie — zrobione w etapie 9) | | jeśli starczy czasu | — |

Minimum na zaliczenie: etapy 0–6 i 8.

## Proces pracy nad etapem

0. **Gałąź** — dla większego etapu autor tworzy ją z aktualnego `main`: `git checkout -b feat/<nazwa>`; poprawki i małe etapy bezpośrednio na `main` (D4, `06-konwencje.md`).
1. **Analiza** (AI + autor) — przegląd kodu i dokumentacji modułów (`moduly/`); w razie potrzeby kod v1 pod tagiem `v1-final`.
2. **Decyzje odroczone** dotyczące etapu (`04-decyzje.md`) — rozstrzygamy teraz.
3. **Specyfikacja** — AI pisze ją w `docs/08-praca-biezaca.md` według szablonu niżej. **Autor akceptuje ją przed implementacją.**
4. **Implementacja z testami** — krok po kroku (commit po commicie): AI podaje kod w rozmowie (całe pliki albo dokładne zmiany) i nazwę commita; autor wprowadza zmiany, uruchamia testy, lint i build, zgłasza problemy i commituje. Na prośbę autora AI czyta jego zmiany (`git status`, `git diff`) i sprawdza je przed commitem.
5. **Zamknięcie** — AI przenosi wynik do `moduly/<nr>-<moduł>.md` (stan, nie historia: model, API, logika, frontend, testy, jak sprawdzić ręcznie, ograniczenia), decyzje do `04-decyzje.md`, aktualizuje status tutaj i w `00-START.md`, czyści `08-praca-biezaca.md`.
6. **Merge** (gdy była gałąź) — autor łączy ją z `main` (`git merge --no-ff`), wypycha i usuwa gałąź.

Etap jest gotowy, gdy: testy backendu przechodzą, `ruff`, lint, `format:check` i build frontendu przechodzą, funkcja działa ręcznie, dokumenty są zaktualizowane.

## Szablon specyfikacji (`docs/08-praca-biezaca.md`)

```
# Etap <nr> — <nazwa>   (data)
Status: szkic / zaakceptowana / zrealizowana

## Odpowiedzialność
## Analiza (obecny kod, co zmieniamy)
## Model danych (tabele, pola, migracje)
## API (endpointy, uprawnienia, kody błędów)
## Logika (reguły, algorytmy)
## Frontend (ekrany, komponenty)
## Testy (scenariusze)
## Kroki implementacji (pliki, commity)
## Poza zakresem
## Pytania do autora

---
## Stan realizacji
Kroki zrobione (commity) · Decyzje w trakcie · Weryfikacja · Do zrobienia
```
