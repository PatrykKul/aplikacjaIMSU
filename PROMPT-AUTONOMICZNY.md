Przeczytaj ponownie `CLAUDE.md` – zmieniły się zasady pracy: od teraz **tryb autonomiczny** (sekcja „Zasady pracy"). Nie czekaj na moją akceptację; raporty zapisuj w `docs/postep/`.

Stan, który zastałem (sprawdzone z zewnątrz): Etap 0 jest zrobiony częściowo – frontend wyczyszczony, Alembic + migracja bazowa, `stylnauki.db`, `seed.py` (szkielet), testy smoke. **Brakuje do domknięcia Etapu 0:**
1. Usuń `frontend/.git`, `frontend/.vercel`, `frontend/.vercelignore` oraz `backend/korepetycje.db`.
2. `git init` w katalogu głównym `aplikacja/` + commity (sensowny podział, nie jeden wielki).
3. README w katalogu głównym (uruchomienie backendu i frontendu, zmienne `.env`, konta testowe – „pojawią się w Etapie 1").
4. Usuń z `CLAUDE.md` sekcje „Stan wyjściowy" i „Do usunięcia"; grepem upewnij się, że w kodzie/README/UI nie ma „DuoKorki", „korepetycje", „KORKUŚ".
5. Weryfikacja: `pytest`, `npm run lint`, `npm run build`.
6. Utwórz `docs/postep/etap-0.md` + `docs/postep/STATUS.md` (+ `PYTANIA.md`, jeśli są pytania).

Następnie realizuj kolejno **Etap 1, 2, 3, 4, 5, 6** wg `CLAUDE.md`, każdy zakończony raportem `docs/postep/etap-N.md`, aktualizacją `STATUS.md` i commitem. Etap 7 (LLM) pomiń.
Jeśli skończy Ci się kontekst/limit w trakcie – przed tym zapisz w STATUS.md dokładnie, na czym stanąłeś, żeby kolejna sesja mogła kontynuować od tego miejsca.
