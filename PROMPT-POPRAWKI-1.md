# Poprawki po audycie zewnętrznym (01.10.2026) – tryb autonomiczny jak dotąd

Audyt: backend 224/224 testów zielonych, auth/role/ukrywanie klucza quizu/niepublikowane kursy/upload – OK. Do poprawy:

1. **Styl przy zapisie wyniku quizu jest brany od klienta bez walidacji** (`POST /bloki/{id}/quiz`, `body.styl`).
   Uczeń może wysłać dowolny styl i „nabijać" wagi wybranego stylu. Przyjmuj tylko styl, w którym uczeń faktycznie mógł oglądać temat:
   jego `styl_uczenia` albo styl proponowany do powtórki (litery V/A/K zawarte w jednym z nich). Inny → 400. Test pytest na ten przypadek.
2. **Końce linii (CRLF/LF).** Na Windowsie `git status` pokazuje dziesiątki „zmienionych" plików, które różnią się tylko końcem linii.
   Dodaj `.gitattributes` (`* text=auto eol=lf` + wyjątki binarne: png, jpg, gif, webp, ico, mp3, ogg, wav, m4a, db) i znormalizuj repo
   (`git add --renormalize .`), osobny commit. Po tym `git status` ma być czysty.
3. **Dokumentacja (`docs/dokumentacja.md`, sekcja 10 „Ograniczenia"):** dopisz krótko, że teoria stylów uczenia (VAK) jest w psychologii
   kwestionowana (brak dowodów na „meshing hypothesis") i dlaczego projekt mimo to ma sens: demonstruje mechanizm personalizacji, uczeń może
   ręcznie zmienić styl, a adaptacja opiera się na wynikach quizów, nie tylko na deklaracji. Model VAK jest wymienny (np. na VARK).
   Bez linków, których nie sprawdziłeś.
4. Weryfikacja: `pytest`, `npm run lint`, `npm run build`. Raport: `docs/postep/poprawki-1.md` (ten sam szablon) + aktualizacja `STATUS.md` + commity.
