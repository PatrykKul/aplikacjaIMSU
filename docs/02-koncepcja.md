# Koncepcja systemu

Źródła: system prowadzącego z filmów, feedback ustny i slajdy wykładu (`01-kontekst-i-materialy.md`; odwołania „§3.x” dotyczą tamtego dokumentu). Ustalenia autorów: listopad 2026; stan po etapie 6 (11.11).

## 1. W skrócie

Multimedialny inteligentny system uczący (MITS, §3.1) z **głównym modułem nauczyciela**. Nauczyciel tworzy w edytorze kurs: opis, wstęp i lekcje. Lekcja to **bloki** układane jak w notatniku — tekst (edytor wizualny, wklejanie z Worda, wzory) i **załączniki** (obraz, wideo, nagranie, PDF, link) oznaczone formą **V / A / K** (jedną lub kilkoma) — oraz opcjonalny **quiz** na końcu. Uczeń po rejestracji wypełnia ankietę VAK i dostaje **styl** oraz **wagi V / A / K**. System podaje lekcję według stylu (materiały innych stylów **zwinięte**), dobiera pytania quizu do materiałów, z których uczeń korzystał, po quizie zmienia wagi i przy wyraźnej przewadze innej formy **proponuje zmianę stylu**, a decyduje uczeń. Każda decyzja ma uzasadnienie „dlaczego to widzisz”.

## 2. Role i dostęp

| Rola | Co robi |
|---|---|
| Uczeń | rejestracja → **ankieta VAK** (wymagana) → kursy (katalog opublikowanych) i „Moje klasy” (kursy klas, także prywatne; nauczyciel z e-mailem) → lekcje i quizy → „Mój styl” (styl, wagi, ręczna zmiana, propozycje, historia ankiet) |
| Nauczyciel | **moduł główny:** CRUD swoich kursów, lekcji, bloków, załączników (wgrywanie plików) i quizów; publikacja kursu; podgląd lekcji; **klasy** (uczniowie dodawani po e-mailu, przypisane kursy) |
| Administrator | zarządza **nauczycielami i uczniami**: lista, tworzenie i edycja kont, **blokada** (zamiast usuwania); bez klas i moderacji kursów (O6) |

- **Rola wybierana przy rejestracji (uczeń albo nauczyciel) i stała.** Administrator powstaje tylko poleceniem CLI.
- Nauczyciel widzi i edytuje **tylko swoje kursy**; nie ma współautorów.
- **Dostęp do kursów (D10, D35):** kurs opublikowany jest dostępny dla wszystkich uczniów (katalog). Nauczyciel tworzy klasy, dodaje do nich istniejących uczniów (wyszukiwanie po e-mailu) i przypisuje klasom swoje kursy — także prywatne, które widzą wtedy tylko uczniowie tych klas. Uczeń widzi swoje klasy (kursy, nauczyciel z e-mailem), bez listy uczestników. Szczegóły: `moduly/02-curriculum.md`.

## 3. Struktura kursu (model dziedziny)

**Kurs → lekcje** (kolejność ustala nauczyciel). Meta-model z wykładu (§3.4): Course = kurs, Learning Unit = lekcja, Content = blok tekstu, Multimedia Object / Content Link = załącznik, Exercise / Test = quiz lekcji.

| Element | Zawartość |
|---|---|
| Kurs | tytuł, **opis** (karta w katalogu), **wstęp** (strona kursu), autor, prywatny / opublikowany, archiwizacja |
| Lekcja | tytuł, **bloki** w kolejności nauczyciela, opcjonalnie **quiz** |
| Blok tekstu | dokument edytora wizualnego (TipTap): nagłówki, pogrubienia, listy, tabele, linki, wzory; widzi go każdy |
| Załącznik | **typ** (obraz, wideo — plik lub YouTube, nagranie — plik lub tekst czytany przez lektora przeglądarki, PDF, link), tytuł, opis, **formy: niepusty podzbiór {V, A, K}** zaznaczany przez nauczyciela |
| Quiz lekcji | do 20 pytań jednokrotnego wyboru (3–4 odpowiedzi); pytanie **wspólne** albo **o materiale formy V / A / K**; próg zaliczenia 70% |

Baza pytań z losowaniem i test końcowy kursu — opcjonalnie później (O5, O3).

## 4. Model ucznia

| Składnik (§3.5) | U nas |
|---|---|
| IP — preferencje | **styl** (`V`, `VA`, `VAK`…; źródło: ankieta / ręczny / adaptacja) i **wagi V / A / K** (0–30, start = punkty ankiety, korekta po quizach) |
| S — wyniki | próby quizów: wynik w procentach, styl efektywny w chwili próby, czy zmieniła wagi |
| obserwacja bierna (Tadeusiewicz) | rozwinięcia zwiniętych materiałów |
| Z — zaawansowanie | nie modelujemy (prototyp) |

## 5. Reguły adaptacji (moduł nauczania)

### 5.1 Lekcja podana uczniowi
- Bloki **w kolejności nauczyciela** (system nie przestawia toku lekcji).
- Bloki tekstu zawsze widoczne. Załącznik, którego **żadna forma nie należy do stylu** ucznia, jest **zwinięty w miejscu** („Pokaż materiał”); pozostałe rozwinięte.
- Nad lekcją „dlaczego to widzisz”: styl, jego źródło (ankieta z punktami, wybór ręczny, propozycja systemu), liczba zwiniętych materiałów.

### 5.2 Styl efektywny lekcji
Styl ucznia ∪ formy załączników, które uczeń **rozwinął** w tej lekcji. Rozwinięcie zapisuje się raz. Styl efektywny decyduje o pytaniach quizu i o tym, które wagi zmienia wynik.

### 5.3 Quiz
1. Uczeń dostaje pytania wspólne + pytania o materiały form jego stylu efektywnego (pytanie o materiał, którego nie oglądał, byłoby nieuczciwe).
2. Ocenia serwer; ≥ 70% = zaliczenie. Po podejściu uczeń widzi poprawne odpowiedzi; podejść bez limitu.

### 5.4 Aktualizacja wag
- Start: wagi = punkty ankiety (zakres 0–30).
- Wynik quizu: każda litera stylu efektywnego +1 (zaliczenie) / −1 (niezaliczenie).
- W lekcji liczy się tylko **pierwszy sukces i pierwsza porażka** dla danego stylu efektywnego — kolejne podejścia nie zmieniają wag (bez nabijania).
- Świadomie bez reguły z v1 „porażka → −1, powtórka w innym stylu, sukces → +1 dla nowego stylu”: przypisuje ona stylowi efekt powtórki (druga próba jest prawie zawsze łatwiejsza), więc wagi przesuwałyby się w stronę stylu „drugiej szansy” — do opisania w dokumentacji.

### 5.5 Propozycja zmiany stylu
**Propozycja**, gdy jedna forma ma samodzielnie najwyższą wagę i nie należy do stylu ucznia. Uczeń przyjmuje (styl = ta forma, źródło: adaptacja) albo odrzuca (ta propozycja nie wraca do kolejnej ankiety lub przyjęcia); **styl wybrany ręcznie wyłącza propozycje**. Nowa ankieta ustawia styl i wagi od nowa.

### 5.6 Wyjaśnialność
Uzasadnienia jako zdania z reguł: styl („…bo tak wyszło w ankiecie (V 9 / A 8 / K 3)”), wynik quizu („…quiz w lekcji »…«: 45% – poniżej progu (próg 70%)”), propozycja („Wagi stylów po quizach: V 7 / A 8 / K 3 …”).

### 5.7 Mapowanie na model z wykładu (§3.5)
Strategia = forma podania (V / A / K). Zamiast W(s, e) = argmax w(s, e) z pełnym silnikiem — reguły powyżej: profil wybiera formę startową, wynik quizu koryguje wagi tych form, z których uczeń faktycznie korzystał, a decyzję o zmianie strategii podejmuje uczeń na podstawie propozycji.

## 6. Widoki

- **Uczeń:** ankieta i wynik; kursy (katalog) i „Moje klasy” (strona klasy z kursami i kontaktem do nauczyciela); strona kursu (wstęp, lekcje); lekcja w trybie skupienia (bloki, zwinięte materiały, „dlaczego to widzisz”, quiz na końcu z wynikiem i informacją o adaptacji, nawigacja między lekcjami); „Mój styl” (styl, źródło, wagi, propozycja, ręczna zmiana, powrót do ankiety, historia).
- **Nauczyciel:** „Moje kursy”; edytor kursu (opis, wstęp, publikacja, lekcje z kolejnością); edytor lekcji (bloki: „+ Tekst”, „+ Załącznik”, przesuwanie, usuwanie; okno załącznika: typ, plik / adres / tekst lektora, tytuł, formy V / A / K); edytor quizu; podgląd lekcji; klasy (lista, strona klasy: uczniowie z wyszukiwaniem na żywo, kursy, usuwanie).
- **Administrator:** nauczyciele i uczniowie (tworzenie, edycja, blokada); podgląd wszystkich kursów (bez klas — O6).

## 7. Wirtualny mentor (opcjonalnie, O3)
Jedna stała postać, komunikaty z reguł („dlaczego to widzisz”, propozycja zmiany stylu, zachęta po porażce), bez LLM (§3.7).

## 8. Ocena skuteczności
Scenariusz na kontach demonstracyjnych (`SCENARIUSZ-POKAZU.md`): uczeń bez ankiety (wymuszenie), lekcja pod styl, quiz i zmiana wag, uczeń z historią quizów i propozycją zmiany stylu, nauczyciel z materiałami V/A/K i edytorem quizu. W dokumentacji zastrzeżenie o *meshing* (Pashler i in., 2008): styl z ankiety to punkt startowy, system sprawdza go na wynikach, uczeń może zmienić styl.

## 9. Kursy demonstracyjne
Trzy kursy z seeda (D21): Matematyka: funkcja liniowa, Angielski: Present Perfect, Programowanie: pętle w Pythonie — 7 lekcji z materiałami V / A / K / mieszanymi (obrazy, karty PDF, nagrania MP3, filmy) i quizami.

## 10. Pytania do prowadzącego (otwarte)
1. Czy ankieta VAK może być autorska (20 pytań z v1)?
2. Czy reguła propozycji zmiany stylu (samodzielny lider wag) jest w duchu jego systemu?
3. Czy test końcowy kursu jest oczekiwany?
4. Forma i dokładny termin oddania.
