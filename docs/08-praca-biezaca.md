# Praca bieżąca

Specyfikacja tego, co teraz robimy. Po zakończeniu: wynik trafia do `moduly/<nr>-<moduł>.md`, decyzje do `04-decyzje.md`, status do `05-plan-etapow.md` i `00-START.md`, a ten plik czyścimy (historia w gicie).

---

# Etap 7 — Wygląd   (11.11.2026)
Status: zaakceptowana (11.11, odpowiedzi autora w „Pytaniach”)

Gałąź: `feat/appearance`. Budżet: ok. 2–2,5 godziny pracy autora, przed pokazem roboczym 12.11. Kolejność kroków według `07-design.md` (kolory → stany → strona startowa → spójność → `RadioGroup`).

## Odpowiedzialność
Poprawa pierwszego wrażenia małym kosztem, **bez zmian w backendzie i w logice**: paleta (krok W6) z kolorami form V / A / K, ikony w stanach pustych i błędów, strona startowa pod `/`, logo, ujednolicenie kilku ekranów, kafelki ról w rejestracji na `RadioGroup`.

## Analiza (obecny kod, co zmieniamy)

Co najbardziej psuje wrażenie wizualne (od największego wpływu):

1. **Brak koloru.** `globals.css` ma paletę Neutral: kolor główny prawie czarny (`--primary: oklch(0.205 0 0)`), więc przyciski, paski stylu, plakietki i zaznaczenia są czarno-szare. Aplikacja dla dzieci wygląda jak panel administracyjny. *Dlaczego to pierwsze:* jeden plik zmienia wszystkie ekrany naraz — dlatego tokeny (W1) i zasada „nigdy surowych kolorów”.
2. **Informacja zwrotna quizu omija tokeny.** `LessonQuiz.tsx` używa surowych `border-green-600`, `bg-green-600/10`, `text-green-700`; tokeny `feedback-correct` / `feedback-incorrect` są zdefiniowane, ale **nigdzie nieużywane**. `AdaptationFeedback` przy niezaliczeniu ma wariant `destructive` (czerwony) — wbrew ustaleniu z `07-design.md`, że „Jeszcze nie” ma być łagodniejsze niż błąd formularza.
3. **Kontrast tekstu drugorzędnego.** `--muted-foreground` (`oklch(0.556 0 0)`) na tle `--muted` (`oklch(0.97 0 0)`) ma 4,34 : 1 — poniżej WCAG AA (4,5) dla zwykłego tekstu (np. opis w szarych paskach, nieaktywne pozycje nawigacji po najechaniu). Na białym: 4,73 — na granicy.
4. **Strona startowa nie istnieje.** `/` od razu przekierowuje na `/login`; pierwszy ekran pokazu to formularz. Nie widać, czym system jest i gdzie jest „inteligencja”.
5. **Stany puste i błędów to sam tekst** (`PageMessage`: tytuł, opis, przycisk). Działają poprawnie, ale wyglądają jak „coś nie zadziałało”. Brak elementu, który przyciąga wzrok i od razu mówi, *jaki* to stan.
6. **Niespójności:**
   - `/dashboard` ucznia ma 2 karty, a menu 3 pozycje (brak „Mój styl”) — wbrew zasadzie „karty odpowiadają pozycjom menu”; karty dashboardu to `Link` owinięty wokół `Card`, a nie wzór rozciągniętego linku jak w pozostałych listach; martwa gałąź z plakietką „Wkrótce”.
   - Hasło „Nauka matematyki na Twoją miarę”, `metadata.description` „…uczący matematyki” i kafelek „Uczę się matematyki”, a kursy demo to matematyka, angielski i Python.
   - Logo to sam napis „IMSU” w trzech miejscach, każdy ostylowany osobno.
   - Ścieżka „Kursy / …” na stronie kursu prywatnego otwartego z klasy prowadzi do katalogu, w którym tego kursu nie ma (ograniczenie z `moduly/02-curriculum.md`).
7. **Kafelki ról** w `RegisterForm` to natywne `<input type="radio">` (wbrew `06-konwencje.md`); brak widocznego znacznika „wybierz jedno”.

Co **nie** psuje wrażenia i zostaje: układ (`AppShell`, konwencja trzech części), typografia (W5), karty bloków i lekcja, spinner ładowania (lokalnie API odpowiada szybko; szkielety treści byłyby lepsze, ale to dużo pracy przy małym zysku).

### Pliki drugiego autora (zasada 4 w `00-START.md`)
Z etapu 4 (kolega), zmieniane tylko wizualnie: `features/assessment/components/LessonQuiz.tsx` (kolory odpowiedzi), `features/learning-style/components/AdaptationFeedback.tsx` (kolor wyniku), `features/learning-style/components/LearningStylePanel.tsx` (ikona w stanie błędu).

## Model danych
Bez zmian.

## API
Bez zmian.

## Logika
Bez zmian. Jedyna nowa reguła widoku: na stronie kursu ścieżka prowadzi do „Moje klasy” (`/classes`), gdy kurs jest prywatny (uczeń widzi go tylko przez klasę), a do „Kursy”, gdy opublikowany.

## Frontend (ekrany, komponenty)

### 1. Paleta (W6) — `globals.css`
Kolor główny **indygo** (kandydatura z `07-design.md`), neutralne zostają szare, kolory semantyczne tylko dla informacji zwrotnej.

| Token | Jasny | Ciemny | Kontrast / dlaczego |
|---|---|---|---|
| `--primary` / `-foreground` | `oklch(0.50 0.19 280)` / `oklch(0.985 0 0)` | `oklch(0.72 0.14 280)` / `oklch(0.205 0 0)` | 6,4 : 1 / 7,0 : 1 (AA z zapasem). Indygo: przyjazne, „szkolne”, ale nie dziecinne; daleko od zieleni sukcesu i czerwieni błędu, więc kolor główny nigdy nie zostanie odczytany jako ocena |
| `--ring` | `oklch(0.65 0.15 280)` | `oklch(0.60 0.15 280)` | fokus w kolorze marki, widoczny na białym i na indygo |
| `--accent` / `-foreground` | `oklch(0.96 0.025 280)` / `oklch(0.40 0.15 280)` | `oklch(0.30 0.06 280)` / `oklch(0.985 0 0)` | jasne tło w odcieniu marki (8,6 : 1): zaznaczenia, kółka ikon, pozycja menu pod kursorem |
| `--muted-foreground` | `oklch(0.50 0 0)` (było 0.556) | bez zmian | 5,5 : 1 na `--muted` i 6,0 na białym — naprawia AA |
| `--feedback-correct` / `-foreground` | `oklch(0.965 0.035 150)` / `oklch(0.42 0.11 150)` | `oklch(0.30 0.05 150)` / `oklch(0.85 0.10 150)` | 7,4 : 1 / 8,8 : 1 |
| `--feedback-incorrect` / `-foreground` | `oklch(0.965 0.025 30)` / `oklch(0.47 0.15 30)` | `oklch(0.30 0.06 30)` / `oklch(0.85 0.08 30)` | 6,5 : 1 / 8,6 : 1; ceglasty, cieplejszy i spokojniejszy niż `destructive` |
| `--form-v` / `-soft` / `-foreground` | `oklch(0.58 0.11 230)` / `oklch(0.955 0.03 230)` / `oklch(0.42 0.09 230)` | `oklch(0.72 0.11 230)` / `oklch(0.32 0.05 230)` / `oklch(0.86 0.08 230)` | błękit — wzrokowa; pasek ≥ 3 : 1 do tła (grafika), tekst na tincie ≥ 7 : 1 |
| `--form-a` / `-soft` / `-foreground` | `oklch(0.58 0.12 70)` / `oklch(0.955 0.03 70)` / `oklch(0.42 0.09 70)` | `oklch(0.72 0.12 70)` / `oklch(0.32 0.05 70)` / `oklch(0.86 0.08 70)` | bursztyn — słuchowa; jw. |
| `--form-k` / `-soft` / `-foreground` | `oklch(0.58 0.13 340)` / `oklch(0.955 0.03 340)` / `oklch(0.42 0.10 340)` | `oklch(0.72 0.12 340)` / `oklch(0.32 0.05 340)` / `oklch(0.86 0.08 340)` | malina — kinestetyczna; jw. |

- `secondary`, `muted`, `border`, `background` — bez zmian. *Dlaczego:* zasada 60-30-10 — dużo neutralnego tła, trochę struktury (karty, ramki), mało koloru akcentu. Kolor ma znaczyć „tu kliknij / to jest wybrane”; jeśli jest wszędzie, przestaje cokolwiek znaczyć.
- `Button` wariant `default`: najechanie `hover:bg-primary/90` zamiast `/80` (`shared/ui/button.tsx`). *Dlaczego:* 80% indygo na białym rozjaśnia przycisk tak, że biały napis spada w okolice 4,5 : 1 — stan hover też musi być czytelny.
- Tryb ciemny: tylko wartości tokenów (spójne na przyszłość), bez przełącznika.
- **Kolory form V / A / K** (decyzja autora: dla odróżnienia). Barwy wybrane tak, żeby nie myliły się z resztą palety: indygo (280°) — akcja, zieleń (150°) i cegła (30°) — wynik; formy na pozostałych odcinkach koła barw: błękit 230°, bursztyn 70°, malina 340°. Wszystkie trzy o tej samej jasności i podobnym nasyceniu — żadna forma nie „krzyczy” bardziej niż inne. Kolor formy nigdy nie występuje sam: zawsze z literą i nazwą (np. „V · Wzrokowa”), bo ok. 8% chłopców ma zaburzenia rozróżniania barw. Tinty (`-soft` + `-foreground`) na plakietkach, pełny kolor tylko na paskach `StyleBars`.

### 2. Stany pusty i błędu — `shared/layout/page-states.tsx`
- `PageMessage` dostaje opcjonalny `icon` (komponent lucide): ikona 24 px w kółku 48 px na `bg-accent text-accent-foreground` nad tytułem.
- Ikony według rodzaju stanu (zawsze te same — spójność): pusto — ikona rzeczy, której brakuje (`BookOpenIcon` kursy, `UsersIcon` klasy, `UserIcon` konta); błąd połączenia — `CloudOffIcon`; nie znaleziono — `SearchXIcon`.
- Stosujemy na ekranach z pokazu: `CourseList`, `CourseView`, `TeacherCoursesPage`, `TeacherClassroomsPage`, `StudentClassroomsPage`, `StudentClassroomView`, `ClassroomEditor`, `LessonFrame`, `LearningStylePanel`, `UsersTable`, `AuthGuard`. Pozostałe wywołania działają bez zmian (prop opcjonalny).
- *Dlaczego ikona, a nie ilustracja:* ilustracja to godziny pracy i osobny styl graficzny do utrzymania; ikona w kolorowym kółku daje to samo „zaczepienie wzroku” i od razu mówi, jaki to stan. Pusty stan to też miejsce na **następny krok** (przycisk „Nowy kurs” już jest — zostaje).

### 3. Strona startowa `/` i logo
- `shared/layout/Logo.tsx`: znak (ikona `GraduationCapIcon` biała na kwadracie `bg-primary`, zaokrąglenie `rounded-lg`) + napis „IMSU”. Używają go `AppShell`, layout `(auth)` (z linkiem do `/`) i strona startowa. *Dlaczego:* logo powtarza się na każdym ekranie — jeden komponent = jeden wygląd; znak w kolorze marki „spina” paletę.
- `features/landing/components/LandingPage.tsx` (gość pod `/`; zalogowany — jak dotąd przekierowanie na `/dashboard`, niezalogowany zamiast przekierowania na `/login` widzi stronę):
  - nagłówek (trzy części): logo · — · „Zaloguj się” (ghost) i „Załóż konto” (primary);
  - **hero**: nagłówek „Ucz się po swojemu”, zdanie o dopasowaniu lekcji do stylu i sprawdzaniu go na wynikach, przyciski „Załóż konto” (primary, `lg`) i „Mam już konto” (outline, `lg`); obok trzy małe karty V / A / K (ikony `EyeIcon`, `HeadphonesIcon`, `HandIcon` + jedno zdanie) jako „ilustracja” pojęcia;
  - **„Jak to działa”**: trzy ponumerowane kroki (`<ol>`): ankieta → lekcja pod Twój styl (materiały innych stylów zwinięte, „dlaczego to widzisz”) → quiz i propozycja zmiany stylu (decydujesz Ty);
  - pas dla nauczyciela: jedno zdanie (kursy z tekstem, obrazami, nagraniami i filmami, materiały V/A/K, klasy) + link „Załóż konto nauczyciela” (`/register`);
  - stopka: „Projekt zaliczeniowy · Inteligentne multimedialne systemy uczące · UwB 2026”.
- `RootRedirect` → zamiana na bramkę: sprawdzanie sesji — spinner; zalogowany — `/dashboard`; gość — `LandingPage`.
- *Dlaczego tak:* strona startowa odpowiada na trzy pytania w kolejności czytania: co to jest (hero), jak działa (kroki), co mam zrobić (jeden wyraźny przycisk główny, drugi obramowany). Pokazuje też od razu „inteligencję”, którą prowadzący ma ocenić.

### 4. Spójność
- **Kolory quizu** (`LessonQuiz`): poprawna odpowiedź `border-feedback-correct-foreground/50 bg-feedback-correct` + ikona `text-feedback-correct-foreground`; błędna analogicznie `feedback-incorrect` (zamiast `green-600` i `destructive`).
- **`AdaptationFeedback`**: zaliczenie — `bg-feedback-correct text-feedback-correct-foreground`, niezaliczenie — `bg-feedback-incorrect text-feedback-incorrect-foreground` (zamiast `destructive`); ikony bez zmian. *Dlaczego:* czerwień `destructive` znaczy „zrobiłeś coś źle w formularzu”; wynik quizu to informacja, nie błąd.
- **Dashboard**: uczeń dostaje trzecią kartę „Mój styl” („Zobacz swój styl uczenia się i jak zmienia się po quizach.”); karty z ikoną w kółku (`bg-accent`) i wzorem rozciągniętego linku (jak `CourseCard`); usunięta gałąź „Wkrótce”. Siatka `sm:grid-cols-2 lg:grid-cols-3`.
- **Teksty** (bez dziedziny): hasło przewodnie „Nauka na Twoją miarę”; `metadata.description` „Inteligentny system uczący — nauka na Twoją miarę”; opis kafelka „Uczniem”: „Uczę się z kursów”.
- **Wylogowanie** prowadzi na `/` (strona startowa) zamiast `/login`. Uwaga: `AuthGuard` po wyczyszczeniu sesji sam przekierowuje na `/login` — trzeba uniknąć wyścigu dwóch przekierowań (rozwiązanie w kroku 6).
- **Ścieżka na stronie kursu** (`CourseView`): kurs prywatny → „Moje klasy” (`/classes`), opublikowany → „Kursy”.

### 4a. Kolory form w komponentach
- `features/content/components/FormBadge.tsx`: plakietka formy (`bg-form-v-soft text-form-v-foreground` itd., tekst z `FORM_LABELS`) — zamiast `Badge` w `LessonQuiz` i `AttachmentSummary`.
- `StyleBars`: pasek każdej formy w jej kolorze (`bg-form-v`…) zamiast `bg-primary`.
- Strona startowa: kółka ikon kart V / A / K w kolorach form.

### 5. Kafelki ról — `RegisterForm`
- `Controller` z react-hook-form + `RadioGroup` (`grid-cols-2`) z `shared/ui`; każdy kafelek to `<label>` z ikoną, nazwą, opisem i widocznym `RadioGroupItem` w prawym górnym rogu; zaznaczony: `has-data-checked:border-primary has-data-checked:bg-accent`; fokus: `has-focus-visible:ring-3 ring-ring/50`.
- *Dlaczego:* `RadioGroup` z Base UI daje poprawną obsługę klawiatury (strzałki zmieniają wybór, Tab wchodzi do grupy raz) i role ARIA; widoczna kropka mówi „wybierz jedno” bez czytania instrukcji, a kolor marki na zaznaczonym kafelku wzmacnia stan (stan nie tylko kolorem — także kropka).

## Testy (scenariusze)
Frontend bez testów automatycznych — kontrola: `npm run lint`, `npm run format:check`, `npm run build`. Ręcznie:
- paleta: przyciski, plakietki, paski stylu, fokus z klawiatury (Tab) na każdym ekranie pokazu; tekst drugorzędny czytelny;
- quiz: zaliczenie i niezaliczenie (`uczen.demo`) — zielona i ceglasta ramka wyniku, poprawne / błędne odpowiedzi;
- stany: nowe konto nauczyciela (pusto „Moje kursy”, „Klasy”), nowy uczeń bez klasy, wyłączony backend (błąd z ikoną);
- `/` jako gość (strona startowa, przyciski prowadzą do `/register` i `/login`), jako zalogowany (przekierowanie), szerokość 375 px bez przewijania w poziomie;
- rejestracja: kliknięcie kafelka, strzałki, Tab, wysłanie jako nauczyciel i jako uczeń;
- kurs „Programowanie” z „Klasy 7a” — ścieżka „Moje klasy”.

## Kroki implementacji (pliki, commity)
Szacunki czasu autora; kolejność zależności (każdy krok działa sam).

| # | Pliki | Commit | Czas |
|---|---|---|---|
| 1 | `app/globals.css`, `shared/ui/button.tsx` | `style(frontend): add indigo color palette` | 15 min |
| 2 | `assessment/components/LessonQuiz.tsx`, `learning-style/components/AdaptationFeedback.tsx` | `style(frontend): use feedback colors in quiz results` | 10 min |
| 3 | `shared/layout/page-states.tsx` + ekrany z listy w p. 2 | `feat(frontend): add icons to empty and error states` | 20 min |
| 4 | `shared/layout/Logo.tsx`, `shared/layout/AppShell.tsx`, `app/(auth)/layout.tsx` | `feat(frontend): add logo` | 10 min |
| 5 | `features/landing/components/LandingPage.tsx`, `features/auth/components/RootRedirect.tsx`, `app/page.tsx` | `feat(frontend): add landing page` | 30 min |
| 6 | `dashboard/components/DashboardHome.tsx`, `courses/components/CourseView.tsx`, `auth/components/AuthenticatedShell.tsx`, teksty (`app/layout.tsx`, `app/(auth)/layout.tsx`, `RegisterForm.tsx`) | `style(frontend): unify dashboard cards and texts` | 15 min |
| 7 | `content/components/FormBadge.tsx`, `LessonQuiz.tsx`, `AttachmentSummary.tsx`, `StyleBars.tsx`, `LandingPage.tsx` | `style(frontend): color learning style forms` | 20 min |
| 8 | `auth/components/RegisterForm.tsx` | `refactor(auth): use RadioGroup for role tiles` | 15 min |
| 9 | `docs/` (W6 i ustalenia w `07-design.md`, decyzje, status) | `docs: close stage 7` | AI |

Razem ok. 2 h 15 min. Jeśli zabraknie czasu: krok 5 w wersji skróconej (tylko nagłówek i hero), a „Jak to działa” po pokazie.

## Poza zakresem
Przełącznik trybu ciemnego; kolory form w edytorze załącznika i quizu (pola wyboru / `Select` zostają neutralne); szkielety ładowania; ilustracje; animacje; wspólna klasa klikalnej karty (powtórzona w 5 plikach — porządek kodu, nie wygląd); `collapsedText` w `PersonalizationNote` na `shared/lib/plural.ts`; tabela użytkowników jako karty na telefonie.

## Pytania do autora (odpowiedzi 11.11)
1. Kolor główny: **indygo**.
2. Teksty bez dziedziny: **„Nauka na Twoją miarę”**.
3. Zakres strony startowej — **tak**; „Wyloguj” → **`/`**.
4. Kolory form V / A / K — **tak**, dla odróżnienia (krok 7).
5. Tryb ciemny: tylko wartości tokenów — **tak**.
6. Informowanie kolegi o zmianach w jego plikach — **nie**.

---
## Stan realizacji
Kroki zrobione (commity) · Decyzje w trakcie · Weryfikacja · Do zrobienia — po akceptacji.
