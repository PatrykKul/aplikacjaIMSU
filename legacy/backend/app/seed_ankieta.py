"""Pytania ankiety VAK (seed). Każde pytanie ma po jednej odpowiedzi dla stylu V, A i K."""

# (question, answer V, answer A, answer K)
PYTANIA_VAK: list[tuple[str, str, str, str]] = [
    (
        "Gdy uczysz się czegoś nowego, najchętniej…",
        "oglądasz schematy, ilustracje lub film",
        "słuchasz, jak ktoś to tłumaczy",
        "od razu próbujesz zrobić to samodzielnie",
    ),
    (
        "Jak najłatwiej zapamiętujesz nowy materiał?",
        "Gdy widzę go zapisany, z kolorami i wykresami",
        "Gdy powtarzam go na głos albo ktoś mi o nim opowiada",
        "Gdy przerabiam go w praktyce, na przykładach i ćwiczeniach",
    ),
    (
        "Kupiłeś nowe urządzenie. Co robisz najpierw?",
        "Oglądam rysunki w instrukcji albo film pokazowy",
        "Proszę kogoś, żeby mi wyjaśnił, jak to działa",
        "Włączam je i sprawdzam wszystko metodą prób i błędów",
    ),
    (
        "Ktoś pyta Cię o drogę. Najchętniej…",
        "rysujesz mapkę albo pokazujesz trasę na ekranie",
        "opisujesz trasę słowami",
        "idziesz kawałek razem z nim i pokazujesz, gdzie skręcić",
    ),
    (
        "Co najbardziej rozprasza Cię podczas nauki?",
        "Bałagan i ruch w zasięgu wzroku",
        "Hałas i rozmowy w tle",
        "Długie siedzenie bez ruchu",
    ),
    (
        "Na lekcji lub wykładzie najbardziej pomaga Ci…",
        "prezentacja, tablica i wykresy",
        "to, co mówi prowadzący, i dyskusja",
        "ćwiczenia, doświadczenia i zadania do wykonania",
    ),
    (
        "Jak przygotowujesz się do sprawdzianu?",
        "Robię notatki, mapy myśli i zakreślam ważne fragmenty",
        "Opowiadam materiał na głos albo omawiam go z kimś",
        "Rozwiązuję dużo zadań i testów próbnych",
    ),
    (
        "Po spotkaniu z nową osobą najdłużej pamiętasz…",
        "jej twarz i wygląd",
        "jej imię i sposób mówienia",
        "to, co razem robiliście",
    ),
    (
        "Kiedy musisz zapamiętać numer telefonu…",
        "wyobrażasz sobie, jak wygląda zapisany",
        "powtarzasz go kilka razy na głos",
        "zapamiętujesz ruch palców przy wpisywaniu",
    ),
    (
        "Gdy masz chwilę wolnego, najchętniej…",
        "oglądasz film, zdjęcia albo czytasz",
        "słuchasz muzyki lub podcastu albo rozmawiasz",
        "uprawiasz sport, majsterkujesz albo gotujesz",
    ),
    (
        "Jak sprawdzasz, czy wyraz jest poprawnie napisany?",
        "Patrzę, czy „dobrze wygląda”",
        "Wymawiam go po cichu i słucham, jak brzmi",
        "Zapisuję go i czuję, czy ręka „pisze dobrze”",
    ),
    (
        "W jaki sposób najłatwiej rozwiązujesz trudny problem?",
        "Rozrysowuję go na kartce",
        "Omawiam go z kimś albo mówię do siebie",
        "Testuję różne rozwiązania w praktyce",
    ),
    (
        "Która forma kursu online przekonałaby Cię najbardziej?",
        "Filmy, animacje i infografiki",
        "Nagrania audio i omówienia lektora",
        "Interaktywne ćwiczenia i symulacje",
    ),
    (
        "Uczysz się obsługi nowego programu. Wolisz…",
        "zrzuty ekranu i film instruktażowy",
        "żeby ktoś opowiedział Ci krok po kroku, co robić",
        "klikać samodzielnie i sprawdzać, co się stanie",
    ),
    (
        "Co najlepiej pamiętasz z ostatniej wycieczki?",
        "Widoki i to, jak wyglądały odwiedzone miejsca",
        "Rozmowy, dźwięki i opowieści przewodnika",
        "To, co robiłem: wędrówkę, zwiedzanie, atrakcje",
    ),
    (
        "Kiedy ktoś tłumaczy Ci coś zbyt długo…",
        "prosisz, żeby to narysował albo pokazał",
        "prosisz, żeby powiedział to inaczej, prostszymi słowami",
        "prosisz, żeby dał Ci spróbować samemu",
    ),
    (
        "Przepis kulinarny najchętniej poznajesz…",
        "ze zdjęć lub filmu pokazującego kolejne etapy",
        "słuchając, jak ktoś go opowiada",
        "gotując od razu i ucząc się w trakcie",
    ),
    (
        "Jak najłatwiej uczysz się słówek z języka obcego?",
        "Z fiszek, obrazków i zapisanych list",
        "Słuchając nagrań i powtarzając na głos",
        "Używając ich w rozmowie, grach i scenkach",
    ),
    (
        "Po czym poznajesz, że dobrze coś rozumiesz?",
        "Potrafię to sobie wyobrazić lub narysować",
        "Potrafię to komuś wytłumaczyć własnymi słowami",
        "Potrafię to samodzielnie wykonać",
    ),
    (
        "W jakim miejscu uczy Ci się najlepiej?",
        "W uporządkowanym, z notatkami i kolorowymi materiałami pod ręką",
        "W cichym albo z ulubioną muzyką w tle",
        "W takim, gdzie mogę wstać, chodzić i coś robić",
    ),
]

STYLE_W_KOLEJNOSCI = ("V", "A", "K")
