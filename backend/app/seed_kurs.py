"""Kurs demonstracyjny (seed): każdy temat ma bloki wspólne oraz osobne bloki dla stylu V, A i K."""

NAZWA_KURSU_DEMO = "Podstawy programowania w Pythonie"


def _quiz(*pytania: tuple[str, list[str], int]) -> dict:
    return {"pytania": [{"tresc": t, "odpowiedzi": o, "poprawna": p} for t, o, p in pytania]}


def _kroki(*kroki: tuple[str, str | None]) -> dict:
    return {"kroki": [{"polecenie": p, "podpowiedz": h} for p, h in kroki]}


# --- Topic 1 -------------------------------------------------------------

TEMAT_ZMIENNE = {
    "tytul": "Zmienne i typy danych",
    "bloki": [
        {
            "typ": "teoria",
            "tresc": (
                "## Czym jest zmienna?\n\n"
                "**Zmienna** to nazwana „szufladka” w pamięci komputera, w której przechowujemy wartość. "
                "Tworzymy ją, przypisując wartość znakiem `=`:\n\n"
                "```python\nwiek = 17\nimie = \"Ola\"\n```\n\n"
                "Każda wartość ma **typ**. Cztery podstawowe typy to:\n\n"
                "- `int` – liczba całkowita, np. `17`\n"
                "- `float` – liczba z ułamkiem, np. `4.5`\n"
                "- `str` – tekst w cudzysłowie, np. `\"Ola\"`\n"
                "- `bool` – prawda lub fałsz: `True` / `False`"
            ),
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": "/demo/zmienne.svg",
            "tresc": "Zmienne jak podpisane pudełka: nazwa na etykiecie, wartość w środku, typ zależy od zawartości.",
        },
        {
            "typ": "diagram",
            "styl": "V",
            "tresc": (
                "Co się dzieje przy `wiek = 17`\n"
                "Python oblicza wartość po prawej stronie: 17\n"
                "Rozpoznaje jej typ: int\n"
                "Zapisuje wartość w pamięci\n"
                "Przykleja do niej etykietę: wiek\n"
                "Od teraz `wiek` oznacza 17"
            ),
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Posłuchaj. Zmienna to po prostu nazwa, pod którą komputer pamięta jakąś wartość. "
                "Kiedy piszesz: wiek równa się siedemnaście, mówisz komputerowi: zapamiętaj liczbę siedemnaście "
                "i nazwij ją wiek. Znak równości nie oznacza tu porównania, tylko polecenie: zapisz. "
                "Każda wartość ma swój typ. Liczba całkowita to int. Liczba z przecinkiem, a właściwie z kropką, "
                "to float. Tekst w cudzysłowie to string, w skrócie str. A prawda albo fałsz to typ bool. "
                "Powtórz na głos: int, float, str, bool. Liczba całkowita, liczba z ułamkiem, tekst, prawda lub fałsz."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": "Zrób to sam. Otwórz dowolny interpreter Pythona (np. w przeglądarce) i wykonuj kroki po kolei.",
            "dane": _kroki(
                ("Wpisz `wiek = 17` i naciśnij Enter.", "Nic się nie wyświetli — przypisanie nie drukuje wyniku."),
                ("Wpisz `print(wiek)`. Co widzisz?", "Powinno pojawić się 17."),
                ("Sprawdź typ: `print(type(wiek))`.", "Zobaczysz <class 'int'>."),
                ("Zmień wartość: `wiek = 17.5` i ponownie sprawdź typ.", "Teraz to <class 'float'> — typ zależy od wartości."),
                ("Utwórz zmienną `imie` ze swoim imieniem i wypisz `print(\"Cześć\", imie)`.", "Tekst musi być w cudzysłowie."),
            ),
        },
        {
            "typ": "przyklad",
            "tresc": (
                "```python\ncena = 12.5      # float\nsztuk = 4        # int\nrazem = cena * sztuk\nprint(razem)     # 50.0\n```\n\n"
                "Wynik mnożenia `float` przez `int` jest typu `float`."
            ),
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": "Zacznijmy prościej. Zmienna to nazwa i wartość:\n\n```python\nkolor = \"zielony\"\nprint(kolor)   # zielony\n```\n\nPo lewej stronie znaku `=` zawsze stoi **nazwa**, po prawej **wartość**.",
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": "Dla chętnych: typ można zmieniać funkcjami `int()`, `float()` i `str()`.\n\n```python\ntekst = \"25\"\nliczba = int(tekst) + 5\nprint(liczba)        # 30\nprint(str(liczba) + \" lat\")   # 30 lat\n```",
        },
        {
            "typ": "uwaga",
            "tresc": "Nazwa zmiennej nie może zaczynać się od cyfry ani zawierać spacji. `moj_wiek` – dobrze, `2wiek` i `moj wiek` – źle.",
        },
        {
            "typ": "zadanie",
            "tresc": "Jaki typ ma wartość zmiennej po wykonaniu `x = \"25\"`?",
            "odpowiedz": "`str`",
            "rozwiazanie": "Cudzysłów oznacza tekst. `\"25\"` to napis złożony z dwóch znaków, a nie liczba 25.",
        },
        {
            "typ": "quiz",
            "tresc": "Sprawdź, ile zostało Ci w głowie.",
            "dane": _quiz(
                ("Jaki typ ma wartość `3.14`?", ["int", "float", "str", "bool"], 1),
                ("Co robi zapis `x = 5`?", ["Sprawdza, czy x jest równe 5", "Zapisuje 5 pod nazwą x", "Wypisuje 5 na ekranie"], 1),
                ("Która nazwa zmiennej jest poprawna?", ["2miejsce", "moje miejsce", "miejsce_2"], 2),
                ("Jaki typ ma wartość `True`?", ["str", "int", "bool"], 2),
            ),
        },
    ],
}

# --- Topic 2 -------------------------------------------------------------

TEMAT_IF = {
    "tytul": "Instrukcja warunkowa if",
    "bloki": [
        {
            "typ": "teoria",
            "tresc": (
                "## Program, który podejmuje decyzje\n\n"
                "Instrukcja `if` wykonuje fragment kodu **tylko wtedy**, gdy warunek jest prawdziwy. "
                "Część `else` wykonuje się w przeciwnym razie.\n\n"
                "```python\nif wiek >= 18:\n    print(\"Pełnoletni\")\nelse:\n    print(\"Niepełnoletni\")\n```\n\n"
                "Ważne są **dwukropek** na końcu linii z `if` oraz **wcięcie** (4 spacje) kodu, który należy do warunku."
            ),
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": "/demo/if.svg",
            "tresc": "Warunek jak rozwidlenie drogi: prawda prowadzi w jedną stronę, fałsz w drugą.",
        },
        {
            "typ": "diagram",
            "styl": "V",
            "tresc": (
                "Jak Python wykonuje if / else\n"
                "Oblicz warunek: wiek >= 18\n"
                "? Czy wynik to True?\n"
                "TAK → wykonaj wcięty blok pod if\n"
                "NIE → wykonaj wcięty blok pod else\n"
                "Idź dalej, do kodu bez wcięcia"
            ),
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Wyobraź sobie bramkarza przed klubem. Pyta: czy masz co najmniej osiemnaście lat? "
                "Jeśli tak, wchodzisz. W przeciwnym razie zostajesz na zewnątrz. Dokładnie tak działa instrukcja if. "
                "Najpierw słowo if, potem warunek, na końcu dwukropek. W następnej linii, z wcięciem, to, co ma się stać, "
                "gdy warunek jest prawdziwy. Potem else z dwukropkiem i, znów z wcięciem, to, co ma się stać w przeciwnym razie. "
                "Zapamiętaj rytm: if, warunek, dwukropek, wcięcie. Else, dwukropek, wcięcie."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": "Napisz własny „bramkarski” program. Wykonuj kroki po kolei i uruchamiaj kod po każdym z nich.",
            "dane": _kroki(
                ("Utwórz zmienną `wiek = 16`.", None),
                ("Dopisz `if wiek >= 18:` i w następnej linii, z wcięciem, `print(\"Wchodzisz\")`.", "Nie zapomnij o dwukropku."),
                ("Uruchom program. Co się wyświetliło?", "Nic — warunek jest fałszywy, więc blok został pominięty."),
                ("Dopisz `else:` i z wcięciem `print(\"Zostajesz\")`. Uruchom ponownie.", "else musi być na tym samym poziomie co if."),
                ("Zmień `wiek` na 20 i sprawdź, która gałąź się wykona.", "Teraz powinno pojawić się „Wchodzisz”."),
            ),
        },
        {
            "typ": "przyklad",
            "tresc": (
                "```python\ntemperatura = 3\nif temperatura < 0:\n    print(\"Mróz\")\nelif temperatura < 15:\n    print(\"Chłodno\")\nelse:\n    print(\"Ciepło\")\n```\n\n"
                "`elif` pozwala sprawdzić kolejny warunek. Tutaj program wypisze `Chłodno`."
            ),
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": "Zacznijmy prościej — sam `if`, bez `else`:\n\n```python\npada = True\nif pada:\n    print(\"Weź parasol\")\n```\n\nJeśli `pada` ma wartość `True`, napis się pojawi. Jeśli `False` — nie wydarzy się nic.",
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": "Dla chętnych: warunki można łączyć słowami `and` i `or`.\n\n```python\nwiek = 20\nma_bilet = True\nif wiek >= 18 and ma_bilet:\n    print(\"Zapraszamy na seans\")\n```",
        },
        {
            "typ": "uwaga",
            "tresc": "Porównanie zapisujemy podwójnym znakiem `==`. Pojedynczy `=` to przypisanie i w warunku spowoduje błąd.",
        },
        {
            "typ": "quiz",
            "tresc": "Krótki quiz z instrukcji warunkowej.",
            "dane": _quiz(
                ("Co musi stać na końcu linii z `if`?", ["Średnik", "Dwukropek", "Kropka"], 1),
                ("Kiedy wykona się blok pod `else`?", ["Zawsze", "Gdy warunek jest prawdziwy", "Gdy warunek jest fałszywy"], 2),
                ("Którym operatorem sprawdzamy równość?", ["=", "==", "=>"], 1),
                ("Co wypisze kod: `x = 5`, `if x > 3: print(\"A\")`, `else: print(\"B\")`?", ["A", "B", "Nic"], 0),
            ),
        },
    ],
}

# --- Topic 3 -------------------------------------------------------------

TEMAT_FOR = {
    "tytul": "Pętla for",
    "bloki": [
        {
            "typ": "teoria",
            "tresc": (
                "## Powtarzanie bez przepisywania\n\n"
                "Pętla `for` wykonuje ten sam blok kodu dla **każdego elementu** z podanego zbioru. "
                "Funkcja `range(n)` daje kolejne liczby od `0` do `n - 1`.\n\n"
                "```python\nfor i in range(5):\n    print(i)\n```\n\n"
                "Ten program wypisze liczby 0, 1, 2, 3, 4 — blok wykona się pięć razy, a zmienna `i` za każdym razem ma inną wartość."
            ),
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": "/demo/petla-for.svg",
            "tresc": "Pętla jak okrążenia na bieżni: przy każdym okrążeniu zmienna `i` przyjmuje kolejną wartość.",
        },
        {
            "typ": "diagram",
            "styl": "V",
            "tresc": (
                "Jedno okrążenie pętli for\n"
                "Weź kolejną wartość z range(5)\n"
                "? Czy są jeszcze wartości?\n"
                "TAK → zapisz ją w zmiennej i\n"
                "Wykonaj wcięty blok kodu\n"
                "Wróć na początek pętli\n"
                "NIE → zakończ pętlę"
            ),
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Pomyśl o trenerze, który liczy okrążenia. Zero, jeden, dwa, trzy, cztery. Przy każdym okrążeniu "
                "zawodnik robi dokładnie to samo. Pętla for działa identycznie. Mówisz: dla i w zakresie pięciu, "
                "czyli for i in range pięć, dwukropek, a potem z wcięciem podajesz, co ma się powtarzać. "
                "Uwaga na liczenie: range pięć zaczyna od zera i kończy na czterech. To razem pięć powtórzeń, "
                "ale piątki wśród nich nie ma. Powtórz: od zera do czterech, pięć razy."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": "Zbuduj pętlę krok po kroku i obserwuj, co się zmienia po każdej modyfikacji.",
            "dane": _kroki(
                ("Napisz `for i in range(3):` i z wcięciem `print(\"Cześć\")`. Uruchom.", "Napis powinien pojawić się 3 razy."),
                ("Zamień `print(\"Cześć\")` na `print(i)`. Jakie liczby widzisz?", "0, 1, 2 — liczenie zaczyna się od zera."),
                ("Zmień `range(3)` na `range(1, 6)`. Co się zmieniło?", "Teraz liczby idą od 1 do 5."),
                ("Przed pętlą dopisz `suma = 0`, a w pętli `suma = suma + i`. Po pętli wypisz `suma`.", "Dla range(1, 6) wynik to 15."),
            ),
        },
        {
            "typ": "przyklad",
            "tresc": (
                "```python\nimiona = [\"Ala\", \"Olek\", \"Iza\"]\nfor imie in imiona:\n    print(\"Cześć,\", imie)\n```\n\n"
                "Pętla `for` potrafi przejść także po elementach listy — tu przywita po kolei trzy osoby."
            ),
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": "Zacznijmy prościej — pętla, która tylko powtarza:\n\n```python\nfor i in range(2):\n    print(\"Hej!\")\n```\n\n`range(2)` oznacza „zrób to 2 razy”. Na ekranie pojawią się dwa napisy `Hej!`.",
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": "Dla chętnych: `range` przyjmuje też krok, a pętle można zagnieżdżać.\n\n```python\nfor i in range(0, 10, 2):\n    print(i)          # 0 2 4 6 8\n\nfor a in range(1, 3):\n    for b in range(1, 3):\n        print(a * b)  # 1 2 2 4\n```",
        },
        {
            "typ": "uwaga",
            "tresc": "`range(5)` **nie zawiera** liczby 5. Jeśli chcesz liczyć od 1 do 5, użyj `range(1, 6)`.",
        },
        {
            "typ": "quiz",
            "tresc": "Quiz z pętli for.",
            "dane": _quiz(
                ("Ile razy wykona się blok w `for i in range(4):`?", ["3", "4", "5"], 1),
                ("Jaka jest ostatnia wartość `i` w `range(5)`?", ["4", "5", "6"], 0),
                ("Co wypisze `for i in range(1, 4): print(i)`?", ["0 1 2 3", "1 2 3", "1 2 3 4"], 1),
                ("Po czym może iterować pętla for?", ["Tylko po liczbach", "Po liczbach z range i po elementach listy", "Tylko po tekście"], 1),
            ),
        },
    ],
}

# --- Topic 4 -------------------------------------------------------------

TEMAT_FUNKCJE = {
    "tytul": "Funkcje",
    "bloki": [
        {
            "typ": "teoria",
            "tresc": (
                "## Własne polecenia\n\n"
                "**Funkcja** to nazwany fragment kodu, który można wywoływać wiele razy. "
                "Definiujemy ją słowem `def`, a wynik oddajemy słowem `return`.\n\n"
                "```python\ndef pole_prostokata(a, b):\n    return a * b\n\nprint(pole_prostokata(3, 4))   # 12\n```\n\n"
                "`a` i `b` to **parametry** — dane wejściowe funkcji. Wartość po `return` to jej **wynik**."
            ),
        },
        {
            "typ": "obraz",
            "styl": "V",
            "image_url": "/demo/funkcja.svg",
            "tresc": "Funkcja jak maszyna: wkładasz dane wejściowe (argumenty), maszyna je przetwarza i oddaje wynik.",
        },
        {
            "typ": "diagram",
            "styl": "V",
            "tresc": (
                "Co się dzieje przy wywołaniu pole_prostokata(3, 4)\n"
                "Python przeskakuje do definicji funkcji\n"
                "Podstawia: a = 3, b = 4\n"
                "Wykonuje ciało funkcji: 3 * 4\n"
                "return oddaje wynik: 12\n"
                "Program wraca w miejsce wywołania z wartością 12"
            ),
        },
        {
            "typ": "audio",
            "styl": "A",
            "tresc": (
                "Funkcja jest jak przepis kulinarny. Raz go zapisujesz, a potem korzystasz z niego, kiedy chcesz. "
                "Zaczynasz od słowa def, potem nazwa funkcji, w nawiasach składniki, czyli parametry, i dwukropek. "
                "Pod spodem, z wcięciem, piszesz kroki przepisu. Na końcu słowo return, czyli: oto gotowe danie. "
                "Samo zapisanie przepisu jeszcze niczego nie gotuje. Dopiero wywołanie funkcji, czyli jej nazwa z nawiasami, "
                "uruchamia kod. Zapamiętaj: def definiuje, nawiasy wywołują, return oddaje wynik."
            ),
        },
        {
            "typ": "cwiczenie",
            "styl": "K",
            "tresc": "Napisz i przetestuj własną funkcję. Po każdym kroku uruchom program.",
            "dane": _kroki(
                ("Napisz `def powitaj(imie):` i z wcięciem `print(\"Cześć,\", imie)`.", "Pamiętaj o dwukropku i wcięciu."),
                ("Uruchom program. Czy coś się wyświetliło?", "Nie — funkcja jest zdefiniowana, ale jeszcze niewywołana."),
                ("Pod definicją (bez wcięcia) dopisz `powitaj(\"Ola\")` i uruchom.", "Zobaczysz: Cześć, Ola"),
                ("Napisz funkcję `podwoj(x)`, która zwraca `x * 2`, i wypisz `print(podwoj(21))`.", "Użyj return, a nie print wewnątrz funkcji."),
                ("Wywołaj `podwoj` trzy razy z różnymi liczbami.", "Jedna definicja — wiele wywołań."),
            ),
        },
        {
            "typ": "przyklad",
            "tresc": (
                "```python\ndef czy_parzysta(n):\n    return n % 2 == 0\n\nprint(czy_parzysta(10))   # True\nprint(czy_parzysta(7))    # False\n```\n\n"
                "Funkcja może zwracać dowolny typ — tutaj `bool`."
            ),
        },
        {
            "typ": "przyklad",
            "poziom": 1,
            "tresc": "Zacznijmy prościej — funkcja bez parametrów i bez `return`:\n\n```python\ndef przywitaj():\n    print(\"Dzień dobry!\")\n\nprzywitaj()\n```\n\nNazwa z nawiasami `przywitaj()` uruchamia kod funkcji.",
        },
        {
            "typ": "przyklad",
            "poziom": 3,
            "tresc": "Dla chętnych: parametr może mieć wartość domyślną.\n\n```python\ndef potega(x, wykladnik=2):\n    return x ** wykladnik\n\nprint(potega(5))      # 25\nprint(potega(2, 10))  # 1024\n```",
        },
        {
            "typ": "uwaga",
            "tresc": "`print` tylko **wyświetla** wartość, a `return` ją **oddaje** — dopiero zwróconą wartość można zapisać w zmiennej lub użyć dalej.",
        },
        {
            "typ": "quiz",
            "tresc": "Quiz z funkcji.",
            "dane": _quiz(
                ("Którym słowem zaczynamy definicję funkcji?", ["function", "def", "func"], 1),
                ("Co robi `return`?", ["Wyświetla wartość na ekranie", "Kończy funkcję i oddaje wynik", "Powtarza funkcję"], 1),
                ("Kiedy wykonuje się kod funkcji?", ["Gdy ją zdefiniujemy", "Gdy ją wywołamy", "Na końcu programu"], 1),
                ("Co wypisze `def f(x): return x + 1` oraz `print(f(4))`?", ["4", "5", "x + 1"], 1),
            ),
        },
    ],
}

KURS_DEMO = {
    "nazwa": NAZWA_KURSU_DEMO,
    "opis": "Kurs demonstracyjny: ten sam materiał w wersji dla wzrokowca, słuchowca i kinestetyka.",
    "dzialy": [
        {"nazwa": "Pierwsze kroki", "tematy": [TEMAT_ZMIENNE, TEMAT_IF]},
        {"nazwa": "Pętle i funkcje", "tematy": [TEMAT_FOR, TEMAT_FUNKCJE]},
    ],
}
