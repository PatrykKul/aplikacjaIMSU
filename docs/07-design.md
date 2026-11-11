# Design system i plan nauki designu

Design tworzymy **razem, krok po kroku**: AI prowadzi autora przez proces projektowania i przy każdej decyzji wyjaśnia, *dlaczego* tak, żeby autor nauczył się robić to dobrze samodzielnie. Bez osobnych „lekcji” — wyjaśnienia przy realnej pracy nad ekranami systemu.

## Zasady

1. **Warstwy:**
   - **tokeny** (`src/app/globals.css`, zmienne CSS + `@theme`): kolory, fonty, zaokrąglenia — komponenty używają nazw (`bg-primary`), nigdy surowych kolorów (`bg-blue-600`);
   - **komponenty bazowe** (`src/shared/ui/`, z shadcn/ui): czysto wizualne, bez danych i logiki;
   - **komponenty feature'ów** (`src/features/…`): logika + składanie komponentów bazowych; najwyżej klasy układu (`flex`, `gap`, `grid`);
   - **układ strony** (`src/shared/layout/AppShell.tsx`).
2. **Plac zabaw `/dev/ui`:** wszystkie komponenty bazowe we wszystkich stanach, bez API i logowania. Niedostępny w buildzie produkcyjnym.
3. **shadcn/ui:** komponenty kopiowane do projektu (nasz kod), aliasy w `components.json` ustawione na `@/shared/ui` i `@/shared/lib`.
4. **Grupa docelowa (do 16 lat), wnioski z BPiT:** większy tekst bazowy, wyraźny kontrast (WCAG AA), proste i przewidywalne układy, komunikaty błędów z podpowiedzią, co zrobić, widoczny fokus z klawiatury.

## Kolejność pracy nad wyglądem

1. Treść i przepływ (szkic: co jest na ekranie, dokąd prowadzi).
2. Układ w szarości (struktura, odstępy, najpierw wąski ekran).
3. Typografia (skala rozmiarów, hierarchia).
4. Kolory (neutralne, jeden główny, semantyczne: sukces / ostrzeżenie / błąd; kontrast).
5. Stany (hover, fokus, disabled, ładowanie, błąd, pusto).
6. Efekty na końcu i oszczędnie.

## Kroki nauki designu

| Krok | Temat | Co powstaje | Status |
|---|---|---|---|
| W1 | Jak działa Tailwind 4 i tokeny shadcn (`globals.css`, `@theme`, zmienne CSS, tryb jasny/ciemny) | `shadcn init`, przegląd tokenów, zmiana koloru głównego | omówione |
| W2 | Komponenty bazowe i warianty (`Button`: warianty i rozmiary, `cn()`, `cva`) | `/dev/ui` z przyciskami we wszystkich stanach | do zrobienia |
| W3 | Formularze: `Input`, `Label`, komunikat błędu, stany | pola z błędem, wyłączone, ładowanie przycisku | zrobione |
| W4 | Układ strony: `AppShell`, siatka, responsywność | nagłówek z menu, obszar treści, wersja na telefon | zrobione |
| W5 | Typografia treści (tekst lekcji, wzory KaTeX) | skala tekstu, `math-markdown`, karty bloków | zrobione |
| W6 | Kolory dla dzieci do 16 lat | paleta: kolor główny, sukces / błąd, formy V / A / K, oba motywy, WCAG AA | zrobione (etap 7) |

Decyzje dotyczące wyglądu dopisujemy niżej po każdym kroku, razem z krótkim uzasadnieniem.

## Ustalenia

### Tokeny (W1)
- shadcn/ui w stylu `base-nova` (prymitywy **Base UI**), kolor bazowy **Neutral**, łączenie klas pakietem `cn` (oficjalny zamiennik `clsx` + `tailwind-merge`).
- `globals.css` ma trzy warstwy: wartości tokenów (`:root`, `.dark`) → mapowanie na klasy Tailwinda (`@theme inline`) → style bazowe (`@layer base`).
- Tokeny występują parami `X` / `X-foreground` (tło i tekst na tym tle) — kontrast pilnujemy w parze.
- Kolory w OKLCH (jasność, nasycenie, odcień). Neutralne z palety Neutral (nasycenie 0); kolor główny i semantyczne — W6.
- Tryb ciemny: klasa `.dark` na `<html>` (nie ustawienie systemu). Na razie aplikacja tylko w trybie jasnym; przełącznik — decyzja później.
- Poprawka po `shadcn init`: `--font-sans: var(--font-sans)` wskazywało samo na siebie (font się nie ładował) → `var(--font-geist-sans)`.
- Tailwind ładowany przez oficjalną integrację **PostCSS** (`@tailwindcss/postcss`, `postcss.config.mjs`) zamiast loadera `@tailwindcss/turbopack` z szablonu — z loaderem zmiany w `globals.css` pojawiały się z dużym opóźnieniem.

### Treść i przepływ ekranów kont
- **Adresy:** panel zalogowanego pod `/dashboard`; `/` — strona startowa dla gościa, zalogowany → `/dashboard` (etap 7).
- **Przepływ:** niezalogowany na stronie aplikacji → `/` (strona startowa z „Zaloguj się”); sukces logowania / rejestracji → `/dashboard`; zalogowany na `/login` lub `/register` → `/dashboard`; „Wyloguj” → `/`; zła rola → ekran „Brak dostępu”. `AuthGuard` i wylogowanie kierują w to samo miejsce — dwa różne cele dawały wyścig przekierowań (wygrywało `/login`).
- **`/login`:** nazwa systemu i hasło przewodnie, nagłówek „Zaloguj się”, alert błędu nad polami, e-mail, hasło z przyciskiem „pokaż hasło”, przycisk na całą szerokość, link do rejestracji.
- **`/register`:** wybór roli jako **dwa duże kafelki** (Uczeń / Nauczyciel) na początku formularza (`RadioGroup`: kropka w rogu, zaznaczony — ramka `primary`, tło `accent`, ikona w kolorze; strzałki zmieniają wybór), imię, e-mail, hasło z „pokaż hasło” i podpowiedzią „co najmniej 8 znaków” (**bez pola „powtórz hasło”**), link do logowania.
- **`/dashboard`:** układ aplikacji (nagłówek: nazwa, nawigacja wg roli, menu użytkownika z imieniem, rolą i „Wyloguj”), powitanie „Cześć, {imię}!” i karty zależne od roli.
- **`/admin/users`:** zakładki **Nauczyciele / Uczniowie**; tabela (imię, e-mail, status, akcje); „+ Dodaj” i „Edytuj” w oknie; **blokada / odblokowanie z oknem potwierdzenia**; na telefonie przewijanie tabeli w poziomie. Szczegóły: `moduly/01-identity.md`.
- **Stany wspólne:** sprawdzanie sesji — spinner na środku; brak dostępu — komunikat i „Wróć na stronę główną”; brak połączenia — komunikat i „Spróbuj ponownie”.

### Formularze i rozmiary kontrolek (W3)
- Stany pola: domyślny, fokus, z podpowiedzią, błąd, wyłączony, wysyłanie. Zasady: etykieta zawsze nad polem (nie sam placeholder); komunikat błędu mówi, jak naprawić; błąd to zawsze tekst, nie tylko kolor (`aria-invalid`, `role="alert"`).
- Powiązania dostępności: `htmlFor`/`id`, `aria-describedby` na podpowiedź lub błąd; `data-invalid` / `data-disabled` na `Field` — przy prawdziwych formularzach zamknąć w jednym komponencie.
- Teksty w komponentach shadcn są po angielsku (np. `aria-label` spinnera) — przy każdym nowym komponencie sprawdzić i przetłumaczyć.
- **Wysokość kontrolek: 44 px** (token `--spacing-control: 2.75rem` → klasy `h-control`, `size-control`). Domyślne 32 px shadcn jest za małe dla dzieci i ekranów dotykowych (zalecany cel dotykowy ok. 44 px). Wariant `sm` przycisku: 36 px, `lg`: 48 px.
- Zakładki (`TabsList`) też 44 px (`h-control`), pozycja zakładki `px-3`.
- Rozmiar tekstu w kontrolkach bez zmian (14 px) — wygodny wg autora.
- Pozycje menu rozwijanego (`DropdownMenuItem`, `DropdownMenuSubTrigger`): `px-2 py-2.5` zamiast domyślnych `px-1.5 py-1` (ok. 40 px zamiast 28 px); etykieta menu `px-2`, żeby tekst był wyrównany z pozycjami.

### Układ strony (W4)
- Mobile first; treść w kontenerze `max-w-5xl` (aplikacja) / `max-w-sm` (logowanie, rejestracja), wyśrodkowana.
- Odstępy ze skali 4 px; bliskość = powiązanie.
- Ekrany logowania i rejestracji: grupa tras `(auth)` — wyśrodkowana karta na tle `bg-muted`, nad nią nazwa i hasło przewodnie.
- `AppShell` (`src/shared/layout/AppShell.tsx`): nagłówek 64 px, `sticky`, cienka linia zamiast cienia; nagłówek w **konwencji trzech części** (patrz niżej); aktywna pozycja nawigacji: tło + `aria-current`; menu użytkownika z inicjałami (bez zdjęć); na telefonie imię ukryte, przycisk z `aria-label`. Komponent czysto wizualny (użytkownik, nawigacja i wylogowanie przez propsy); podgląd: `/dev/shell`.
- Base UI łączy komponenty propsem `render` (nie `asChild` jak Radix); `DropdownMenuLabel` musi być w `DropdownMenuGroup`.

### Tabele na wąskim ekranie
- Na telefonie **tabela przewijana w poziomie** (prostsza niż lista kart, jeden układ; panel administratora rzadko używany na telefonie). Przy testach w trybie urządzenia DevTools ustawiać „Fit to window” — przy powiększeniu 100% przewija się emulowany ekran, co wygląda jak „rozjechana” strona.
- Wzorzec „karty zamiast tabeli na telefonie” rozważyć ponownie dla tabel używanych przez nauczyciela (np. na tablecie).
- Zasada: responsywność zmienia **układ**, a nie rozmiar tekstu; tekst nie zmniejsza się na telefonie.
- Sprawdzenie, czy strona naprawdę wystaje w poziomie: `document.documentElement.scrollWidth > document.documentElement.clientWidth`.
- Kontrolki tabeli wydzielone do małych komponentów (np. `StatusBadge` w `UsersTable.tsx`).

### Konwencja nagłówków: trzy części

- Każdy nagłówek (aplikacji, lekcji, przyszłe) to siatka o trzech kolumnach: `grid-cols-[minmax(max-content,1fr)_minmax(0,<szerokość treści>)_minmax(max-content,1fr)]`, odstęp od krawędzi `px-4 sm:px-6` (lekcja na telefonie `px-2`).
- **Lewa** część przy lewej krawędzi ekranu (`justify-self-start`): logo / powrót. **Środkowa** wyrównana z kolumną treści strony i z takim samym odstępem wewnętrznym jak `<main>`: nawigacja (`64rem` = `max-w-5xl`) / tytuł lekcji (`48rem` = `max-w-3xl`, jak karty bloków). **Prawa** przy prawej krawędzi (`justify-self-end`): menu użytkownika / akcje strony.
- `minmax(max-content, 1fr)` w bocznych kolumnach: nigdy węższe od zawartości; na wąskim ekranie najpierw kurczy się środek (`minmax(0, …)`), więc nic nie nachodzi na siebie.
- `justify-self-*` na elemencie, który faktycznie jest w siatce (np. przycisk `DropdownMenuTrigger`, nie `DropdownMenu` — Base UI `Menu.Root` nie renderuje elementu).

### Wspólny wzór klikalnych kart i wierszy

- Jedna krawędź dla wszystkich kart: ta z `Card` (`ring-1 ring-foreground/10`, `rounded-xl`, odstęp 16 px = `--card-spacing`); nie `border` (inny kolor i grubość).
- Najechanie: `hover:bg-muted/50`; fokus: `ring-3 ring-ring/50` (na karcie z rozciągniętym linkiem — `has-[a:focus-visible]:…`).
- Tekst w kartach list (dashboard, kursy, lekcje): tytuł `text-lg font-medium` (waga jak `CardTitle`), opis `text-base text-muted-foreground`; drobne informacje `text-sm`.
- **Zbiory kart to listy:** kolejność ma znaczenie (lekcje, numeracja) → `<ol>`; bez kolejności (kursy) → `<ul>`. Czytnik ekranu ogłasza „lista, 6 elementów” i pozycję. Zawsze z `role="list"`, bo Tailwind usuwa znaczniki list (`list-style: none`), a Safari z VoiceOver traktuje wtedy listę jak zwykły blok. Karta w `<li>` siatki — `h-full`, żeby karty w rzędzie miały równą wysokość.
- Nagłówki stron i sekcji zostają `font-semibold` (h1 `text-2xl`, h2 `text-xl`).
- **Klikalne karty zawsze na `Card`** (kursy, dashboard, lekcje): wygląd z jednego miejsca, więc krok palety zmieni je wszystkie naraz. Wzór „rozciągniętego linku”: `Card` z `relative`, link w `CardTitle` z `after:absolute after:inset-0` — cała karta klikalna, a nazwa linku dla czytnika ekranu to sam tytuł. Kontrolki w karcie (np. przełącznik, menu) — `relative z-10`.

### Typografia treści (W5)

- **Skala M:** tekst lekcji 17 px, interlinia 1,65, kolumna maks. 65 znaków (`max-w-[65ch]`), tytuł lekcji 24 px / 500, etykiety („Pytanie 2 z 6”) 14 px w kolorze drugorzędnym. Porównane S (16 px / 1,6 / 60 znaków) i L (18 px / 1,7 / 68 znaków) — S za mała dla młodszych na laptopie, L za dużo przewijania.
- **KaTeX:** wzory w tekście zmniejszone z domyślnego `1.21em` do `1.1em` (`.katex { font-size: 1.1em }`), żeby nie dominowały nad Geist; wzory blokowe z odstępem `0.8em`.
- **Bloki jako karty** (zamiast linii między blokami): obramowanie 1 px, zaokrąglenie 12 px, wewnętrzny odstęp 32 × 36 px (porównane 24 × 28 i 40 × 44), odstęp między kartami 20 px. Na telefonie wewnętrzny odstęp ok. 20 px.

### Pytania i informacja zwrotna (quiz)

- Pytanie: pole liczby z jednostką obok (klawiatura numeryczna na telefonie) albo kafelki wyboru (≥ 44 px); przy pustym / nieliczbowym — komunikat przy polu („Wpisz odpowiedź”, „Wpisz liczbę, np. 12,5”).
- Słowa: „Dobrze!” / „Jeszcze nie” + komunikat (typowy błąd z treści pytania albo wyjaśnienie); nigdy „Źle!”. Wynik podawany neutralnie (bez czerwieni i gwiazdek).
- **Przyciski:** jeden wypełniony (primary) na akcję główną; pozostałe obramowane (outline). Pole odpowiedzi i przyciski 44 px.
- **Kolor tylko w bloku informacji** (jasne tło + ciemny tekst), ramka karty bez zmian po odpowiedzi (kolorowanie ramek przy kilku kartach to za dużo koloru). Stan nie jest przekazywany tylko kolorem — zawsze słowo i ikona (`check` / `x`).
- **Nazwy semantyczne** kolorów: `feedback-correct` / `feedback-correct-foreground` i `feedback-incorrect` / `feedback-incorrect-foreground` (klasy `bg-feedback-correct`, `text-feedback-correct-foreground`…), wartości w `globals.css` (W6). Nie `destructive`: w motywie shadcn jest czerwony i służy błędom formularzy, a „Jeszcze nie” ma być łagodniejsze.
- Poprawna / błędna odpowiedź: tło `bg-feedback-*`, ramka `border-feedback-*-foreground/50`, ikona `text-feedback-*-foreground`; ramka wyniku (`AdaptationFeedback`) w tych samych kolorach, z opisem w kolorze tekstu ramki (`text-current`).

### Nagłówek lekcji — tryb skupienia

- Na stronie lekcji własny stały nagłówek (`sticky top-0`) **zamiast** nagłówka `AppShell` (dwa stałe paski zajęłyby ok. 130 px ekranu telefonu); konwencja trzech części; przycisk powrotu bez obramowania (`ghost`, jak pozycje nawigacji).
- Komputer (64 px): „← Kurs”, nad tytułem nazwa kursu (13 px), tytuł lekcji (16 px / 500, skracany wielokropkiem). Telefon (56 px): ikona powrotu i tytuł. Tytuł lekcji przenosi się z treści do nagłówka.
- Komponent `features/courses/components/LessonHeader.tsx` (etap 3, napisany od nowa — wersja z historii miała licznik kroków i pasek postępu).

### Edytor lekcji i widok lekcji (etap 3)

- **Edytor lekcji:** bloki jako karty z paskiem (ikona typu, w górę / w dół, edytuj, usuń; przyciski 44 px z nazwą bloku dla czytnika ekranu); między blokami ciche „+ Tekst / + Załącznik” (`ghost`, `sm`), pod listą wyraźne (`outline`); pasek „Zapisz lekcję / Podgląd” przyklejony pod nagłówkiem (`sticky top-16`).
- **Okno załącznika:** krok 1 — kafelki typu (ikona, nazwa, krótki opis), krok 2 — pola typu, tytuł, opis, formy jako pola wyboru w wierszach 44 px; źródło wideo / nagrania w zakładkach; wszystkie błędy naraz.
- **Karta załącznika w edytorze:** miniatura obrazu (80 px) albo ikona typu, tytuł, plik / adres, plakietki form.
- **Strefa pliku:** przerywana ramka, „Przeciągnij plik tutaj albo [Wybierz plik]”, dozwolone typy i limit drobnym tekstem; w trakcie przeciągania „Upuść plik tutaj” i podświetlenie; potem pasek postępu, potem wiersz z nazwą i „Zmień plik”.
- **Widok lekcji:** karty bloków wg W5; tytuł i opis załącznika nad odtwarzaczem; obraz do 70% wysokości ekranu; YouTube 16 : 9; PDF — przycisk i (od `sm`) ramka; na dole „Poprzednia lekcja” (obramowany) i „Następna lekcja” / „Wróć do kursu” (wypełniony).
- **Podgląd autora:** pasek na `bg-muted` z ikoną oka: „Podgląd: tak uczeń widzi kurs / lekcję (zapisaną wersję).” + „Wróć do edycji”.

### Ankieta, profil, quiz i zwinięte materiały (etapy 4–5)

- **Ankieta:** pytania jako karty z kafelkami odpowiedzi (`RadioGroup`, 44 px), przyklejony pasek postępu „Odpowiedziano na X z Y”; po próbie wysłania z brakami — czerwona ramka przy pytaniu i przewinięcie do pierwszego brakującego.
- **Wynik i profil:** styl słownie („wzrokowiec + słuchowiec”) z opisem, wagi / punkty V / A / K jako trzy poziome paski (`StyleBars`), źródło stylu plakietką; propozycja zmiany stylu jako baner z „Przełącz” (primary) i „Zostaję przy swoim” (outline) oraz zdaniem „Dlaczego to widzisz”.
- **Lekcja:** nad blokami ramka `Alert` „Lekcja dopasowana do stylu…” z uzasadnieniem i linkiem „Zmień styl”. Zwinięty załącznik: karta w miejscu materiału — ikona i nazwa rodzaju („Nagranie”, „PDF”…), tytuł, przycisk „Pokaż materiał” (outline; na telefonie pod treścią); bez plakietek form — to, że materiał jest dla innego stylu, mówi notka nad lekcją. Rozwinięty ma pod spodem „Zwiń materiał” (ghost). W podglądzie nauczyciela wszystko rozwinięte, pod paskiem podglądu zdanie, co widzi uczeń.
- **Quiz pod lekcją:** karta „Sprawdź się”, pytania z plakietką formy (np. „Wzrokowa (V)”), po sprawdzeniu poprawna odpowiedź na zielono z ikoną `check`, błędna z `x`, wynik słownie i liczbowo, informacja o adaptacji (`AdaptationFeedback`), „Rozwiąż jeszcze raz” (outline).
- **Edytor quizu:** pytania jako karty; forma pytania w `Select` („Wspólne / Wzrokowa / Słuchowa / Kinestetyczna”); usunięcie quizu przez `AlertDialog`.

### Paleta (W6, etap 7)

- **Kolor główny indygo** `oklch(0.50 0.19 280)`, biały tekst 6,4 : 1 (ciemny motyw: `oklch(0.72 0.14 280)` z ciemnym tekstem, 7,0 : 1). Przyjazny, a nie dziecinny; daleko od zieleni sukcesu i czerwieni błędu, więc nie jest odczytywany jako ocena. Odrzucone: niebieski (bardziej „biurowy”), morski (za blisko zieleni sukcesu).
- `--ring` w odcieniu marki (`oklch(0.65 0.15 280)`); `--accent` — jasne indygo `oklch(0.96 0.025 280)` z tekstem `oklch(0.40 0.15 280)` (8,6 : 1): kółka ikon, zaznaczenia, pozycja menu pod kursorem, pas dla nauczyciela na stronie startowej.
- `--muted-foreground` `oklch(0.50 0 0)` zamiast 0.556 — stara wartość miała na tle `--muted` 4,34 : 1 (poniżej AA).
- Neutralne (`background`, `secondary`, `muted`, `border`) bez zmian — zasada **60-30-10**: dużo neutralnego tła, trochę struktury, mało akcentu; kolor znaczy „kliknij / wybrane”.
- Przycisk `default` po najechaniu `bg-primary/90` (było `/80`) — jaśniejsze indygo obniżało kontrast białego napisu.
- **Informacja zwrotna:** sukces tekst `oklch(0.42 0.11 150)` na `oklch(0.965 0.035 150)` (7,4 : 1), „Jeszcze nie” tekst `oklch(0.47 0.15 30)` na `oklch(0.965 0.025 30)` (6,5 : 1) — ceglasty, łagodniejszy niż `destructive`.
- **Formy V / A / K** (tokeny `form-x` — pełny, `form-x-soft` — tinta, `form-x-foreground` — tekst na tincie): V błękit 230°, A bursztyn 70°, K malina 340° — odcinki koła barw wolne od indygo (akcja), zieleni i cegły (wynik); ta sama jasność (0,58 pełny, 0,955 tinta), żadna forma nie dominuje. Pełny kolor tylko na paskach `StyleBars` (grafika, ≥ 3 : 1), plakietki (`FormBadge`) jako tinta z ciemnym tekstem (≥ 7 : 1). **Kolor formy zawsze z literą i nazwą** — nigdy jedyny nośnik informacji.
- Klasy z kolorami form zapisane w całości (`bg-form-v-soft`), nie składane z kawałków — Tailwind szuka nazw klas w tekście plików.
- Tryb ciemny: wartości wszystkich tokenów w `.dark`, bez przełącznika.

### Stany puste i błędów (etap 7)

- `PageMessage` z opcjonalnym `icon`: ikona 24 px w kółku 48 px na `bg-accent`, nad tytułem; ikona `aria-hidden`.
- Słownik ikon (zawsze te same): pusto — rzecz, której brakuje (`BookOpen` kursy, `Users` klasy, `ClipboardList` brak stylu); błąd połączenia — `CloudOff`; nie znaleziono — `SearchX`. Pusty stan to zaproszenie do pierwszego kroku, nie ostrzeżenie.
- Ikona zamiast ilustracji: ten sam „zaczep” dla wzroku za ułamek kosztu. Ładowanie bez zmian (spinner); szkielety treści — może później.

### Logo, strona startowa, dashboard (etap 7)

- `shared/layout/Logo.tsx`: biała czapka (`GraduationCap`) na kwadracie `bg-primary` + „IMSU”; rozmiary `default` (nagłówki) i `lg` (logowanie, rejestracja); czysto wizualne — link dookoła daje wywołujący (`AppShell` → `/dashboard`, `(auth)` → `/`), z `aria-label` mówiącym, dokąd prowadzi.
- Hasło przewodnie bez dziedziny: „Nauka na Twoją miarę” (kursy demo: matematyka, angielski, Python).
- **Strona startowa** (`features/landing`): nagłówek w konwencji trzech części (logo · — · „Zaloguj się” ghost, „Załóż konto” primary — na telefonie tylko „Zaloguj się”); hero „Ucz się po swojemu” z jednym wypełnionym przyciskiem (`lg`) i jednym obramowanym, obok trzy karty form V / A / K w ich kolorach; „Jak to działa” — trzy ponumerowane kroki (`<ol>`, numery `bg-primary`); pas „Uczysz innych?” na `bg-accent`; stopka. Kolejność: co to jest → jak działa → co zrobić.
- **Dashboard**: karty w kolejności menu (uczeń — także „Mój styl”), ikona w kółku `bg-accent`, wzór rozciągniętego linku jak w `CourseCard`, siatka `sm:grid-cols-2 lg:grid-cols-3`.
- Ścieżka na stronie kursu: uczeń na kursie prywatnym (widocznym tylko przez klasę) → „Moje klasy”, w pozostałych przypadkach „Kursy”.

