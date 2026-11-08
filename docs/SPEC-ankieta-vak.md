# SPEC: ankieta VAK, profilowanie i uproszczona adaptacja (v2)

Status: **do akceptacji** · gałąź `feat/ankieta-vak` · termin: prezentacja 12.11.2026
Źródło logiki: v1 (`legacy/backend/app/services/vak.py`, `personalizacja.py`, `adaptacja.py`, `routers/ankieta.py`, `seed_ankieta.py`).

## 0. Zasada i zakres

**Dobudowujemy, nie zmieniamy kodu Bartka.** Całość trafia do nowego modułu `backend/app/modules/learning_style/`, nowej migracji Alembic i nowego katalogu `frontend/src/features/learning-style/` oraz nowych stron. Kilka miejsc, w których bez podpięcia się nie da, jest wypisanych w sekcji 5. Żadne z nich nie zostanie zmienione bez akceptacji.

| W zakresie | Poza zakresem (świadomie) |
|---|---|
| ankieta VAK (20 pytań z v1), wynik, historia wyników | edytor pytań ankiety dla nauczyciela (w v1 był; pytania są w migracji) |
| styl ucznia: z ankiety, ręczny, z adaptacji | poziomy trudności (bloki v2 nie mają poziomu) |
| filtrowanie bloków lekcji pod styl ucznia + „dlaczego to widzisz” | „powtórka tematu w innym stylu” z v1 |
| wagi stylów po quizie + propozycja zmiany stylu | panel nauczyciela ze stylami uczniów |
| interfejs (punkt styku) dla quizu Bartka | sam blok quiz i jego edytor (robi Bartek) |

Nazewnictwo jak u Bartka: kod i API po angielsku, teksty dla użytkownika po polsku, błędy jako `AppError(status, "KOD")`.

## 1. Tabele i migracja

Nowa migracja `backend/alembic/versions/<rev>_create_learning_style_tables.py`, `down_revision = "908770dc9db3"` (obecny head). **Tabela `users` nie jest zmieniana**: styl ucznia ma osobną tabelę 1:1 `learning_profiles`.

| Tabela | Kolumny | Uwagi |
|---|---|---|
| `survey_questions` | `id` PK, `text` varchar(300), `position` int, `is_active` bool default true | |
| `survey_answers` | `id` PK, `question_id` FK → `survey_questions` ON DELETE CASCADE, `text` varchar(300), `style` varchar(1) CHECK in (`V`,`A`,`K`), `position` int | po 3 odpowiedzi na pytanie (V, A, K) |
| `survey_results` | `id` PK, `user_id` FK → `users` ON DELETE CASCADE, `points_v`/`points_a`/`points_k` int, `dominant_style` varchar(3), `created_at` timestamptz default now() | historia: każde wypełnienie to nowy wiersz |
| `learning_profiles` | `user_id` PK + FK → `users` ON DELETE CASCADE, `style` varchar(3), `style_source` varchar(12) CHECK in (`survey`,`manual`,`adaptation`), `weight_v`/`weight_a`/`weight_k` int CHECK 0–30, `rejected_proposal` varchar(1) NULL, `updated_at` timestamptz | wiersz powstaje przy pierwszej ankiecie, więc brak wiersza = ankieta niewypełniona |
| `quiz_attempts` | `id` PK, `user_id` FK → `users` CASCADE, `lesson_id` FK → `lessons` CASCADE, `block_id` varchar(40), `percent` int CHECK 0–100, `style` varchar(3), `counted_for_weights` bool, `created_at` timestamptz | wpisy z quizu Bartka (sekcja 4); indeks (`user_id`, `lesson_id`) |

`style` ma postać jednej lub kilku liter w kolejności V, A, K: `V`, `VA`, `VAK`. Przy remisie w ankiecie powstaje styl mieszany, tak jak w v1.

**Dane:** ta sama migracja wstawia (`op.bulk_insert`) 20 pytań z `legacy/backend/app/seed_ankieta.py` z odpowiedziami V/A/K. Po samym `alembic upgrade head` ankieta działa, bez osobnego seeda, i jest też w bazie testowej. `downgrade()` usuwa tabele.

## 2. Endpointy

Moduł `learning_style`: `router.py`, `schemas.py`, `service.py` plus czyste funkcje `scoring.py`, `personalization.py`, `adaptation.py` (bez bazy i bez FastAPI, jak w v1). „Uczeń” = rola `student`. Nauczyciel i admin nie wypełniają ankiety i widzą lekcję bez filtrowania (podgląd).

### Ankieta (`survey_router`, prefiks `/survey`)

| Metoda i ścieżka | Kto | Działanie | Błędy |
|---|---|---|---|
| `GET /survey/questions` | zalogowany | aktywne pytania z odpowiedziami: `{id, text, answers: [{id, text}]}`, **bez pola `style`** (klucz nie trafia do przeglądarki) | 401 |
| `POST /survey/answers` | uczeń | body `{answers: [{question_id, answer_id}]}`, czyli odpowiedź na każde aktywne pytanie dokładnie raz. Liczy wynik, zapisuje `survey_results`, tworzy/aktualizuje `learning_profiles` (styl z ankiety, źródło `survey`, wagi = punkty, `rejected_proposal = NULL`). Zwraca `LearningProfileResponse` | 403 `FORBIDDEN` (nie uczeń), 409 `SURVEY_EMPTY`, 400 `SURVEY_INCOMPLETE`, 400 `SURVEY_DUPLICATE_ANSWER`, 400 `SURVEY_ANSWER_MISMATCH` |
| `GET /survey/results` | uczeń | historia wyników, od najnowszego | |

### Profil stylu (`profile_router`, prefiks `/profile/learning-style`)

| Metoda i ścieżka | Działanie | Błędy |
|---|---|---|
| `GET` | `LearningProfileResponse` (niżej); dla ucznia bez ankiety `survey_completed: false`, reszta `null` | |
| `PUT` body `{style: "V" \| "A" \| "K" \| "VA" \| …}` | ręczna zmiana stylu, źródło `manual`; wynik ankiety zostaje | 403 `SURVEY_REQUIRED`, 422 zły styl |
| `DELETE` | powrót do stylu z ostatniej ankiety, źródło `survey` | 403 `SURVEY_REQUIRED` |
| `POST /proposal/accept` | przyjęcie propozycji: styl = proponowany, źródło `adaptation` | 409 `NO_PROPOSAL` |
| `POST /proposal/reject` | `rejected_proposal = proponowany`; ta propozycja już nie wróci | 409 `NO_PROPOSAL` |

```jsonc
// LearningProfileResponse
{
  "survey_completed": true,
  "style": "V",                      // null, gdy brak ankiety
  "style_source": "survey",          // survey | manual | adaptation
  "weights": {"V": 9, "A": 6, "K": 5},
  "last_result": {"points": {"V": 9, "A": 6, "K": 5}, "dominant_style": "V", "created_at": "…"},
  "explanation": "Widzisz materiały dla stylu: wzrokowiec, bo tak wyszło w ankiecie (V 9 / A 6 / K 5).",
  "proposal": {                      // null, gdy brak propozycji
    "style": "A",
    "message": "Lepiej Ci idzie z materiałami słuchowymi – przełączyć?",
    "why": "Wagi po quizach: V 7 / A 10 / K 5 – styl słuchowy prowadzi."
  }
}
```

### Bloki lekcji pod styl (`personalized_router`)

`GET /lessons/{lesson_id}/personalized-blocks`. Ścieżka nie koliduje z `GET /lessons/{lesson_id}` ani `/lessons/{lesson_id}/blocks` Bartka.

- Dostęp i treść bierze z istniejącej funkcji `content.service.get_blocks(db, lesson_id, user)`. Tylko **import**, bez zmian: te same reguły widoczności, 404 i pola `file_url`/`youtube_id`.
- Filtr dla ucznia: blok `text` jest wspólny i widoczny zawsze. Blok `attachment` jest widoczny, gdy jego `forms` ma część wspólną ze stylem ucznia. Załącznik oznaczony V+A+K widzą więc wszyscy. Kolejność bloków zostaje taka, jaką ustalił nauczyciel.
- Uczeń bez ankiety dostaje 403 `SURVEY_REQUIRED`, więc wymuszenia ankiety nie da się obejść ręcznym URL-em.
- Odpowiedź ma ten sam kształt co `/blocks` plus metadane:

```jsonc
{"blocks": [...], "style": "V", "hidden_count": 3,
 "explanation": "Widzisz materiały dla stylu: wzrokowiec, bo tak wyszło w ankiecie (V 9 / A 6 / K 5)."}
```
Dla nauczyciela/admina: wszystkie bloki, `style: null`, `hidden_count: 0`, `explanation: "Podgląd nauczyciela: widzisz materiały dla wszystkich stylów."`.

Endpoint `/blocks` Bartka zostaje bez zmian i nadal służy edytorowi.

## 3. Ekrany (frontend)

Nowe pliki: `frontend/src/features/learning-style/` (`api.ts`, `hooks.ts`, `types.ts`, `components/*`) i nowe strony w `frontend/src/app/(app)/`.

| Ekran | Plik | Zachowanie |
|---|---|---|
| **Wymuszenie ankiety** | `components/SurveyGate.tsx` | dla ucznia z `survey_completed: false` przekierowuje na `/survey` z każdej strony poza `/survey`; dla innych ról nic nie robi. Podpięcie: zmiany Z1, Z2 |
| **Ankieta** | `app/(app)/survey/page.tsx` + `components/SurveyForm.tsx` | 20 pytań, jednokrotny wybór, pasek postępu, wysyłka dopiero po odpowiedzi na wszystkie. Kolejność odpowiedzi w pytaniu jest losowana raz przy wczytaniu, żeby V nie było zawsze pierwsze. Po wysłaniu przejście na `/survey/result` |
| **Wynik** | `app/(app)/survey/result/page.tsx` + `components/SurveyResult.tsx` | styl dominujący z opisem, punkty V/A/K jako trzy paski, przycisk „Przejdź do kursów” |
| **Profil, „Mój styl uczenia”** | `app/(app)/profile/page.tsx` + `components/LearningStylePanel.tsx` | aktualny styl i jego źródło, „dlaczego”, wagi; wybór ręczny (V / A / K / mieszany), „Przywróć styl z ankiety”, „Wypełnij ankietę ponownie”, historia wyników. Link w menu: zmiana Z3 |
| **Lekcja** | `components/PersonalizationNote.tsx` + hook `usePersonalizedBlocks` | nad treścią lekcji krótka notka „dlaczego to widzisz” i „Ukryto N materiałów dla innych stylów”. Uczeń dostaje bloki z `/personalized-blocks`, a renderuje je dalej `BlockView` Bartka. Podpięcie: zmiana Z4 |
| **Propozycja zmiany stylu** | `components/StyleProposalBanner.tsx` | baner z `message` + `why` i przyciskami „Przełącz” / „Zostaję przy swoim”; pokazywany w profilu i w notce lekcji, gdy `proposal != null` |
| **Odpowiedź po quizie** | `components/AdaptationFeedback.tsx` | gotowy komponent dla bloku quiz Bartka: pokazuje `QuizFeedback` (sekcja 4). Bartek wstawia go u siebie, gdy quiz będzie gotowy |

## 4. Adaptacja uproszczona i punkt styku z quizem

Reguły (czyste funkcje w `adaptation.py`, przeniesione z v1):

| Reguła | Działanie |
|---|---|
| Start | po ankiecie wagi V/A/K = punkty z ankiety (zakres 0–30) |
| Sukces / porażka | quiz ≥ 70% to sukces; każda litera stylu ucznia: +1 przy sukcesie, −1 przy porażce |
| Ochrona przed „nabijaniem” | waga zmienia się tylko przy **pierwszym** sukcesie i **pierwszej** porażce w danej lekcji i stylu (`counted_for_weights`) |
| Propozycja | gdy inny styl jest **samodzielnym** liderem wag i nie ma go w stylu ucznia, system proponuje zmianę. Nie proponuje, gdy styl jest ręczny (`manual`) albo gdy tę propozycję uczeń już odrzucił. Decyduje uczeń |
| Wyjaśnialność | każda zmiana ma tekst „dlaczego”, np. „bo quiz w lekcji »Procent składany«: 45% (próg 70%)” |

**Punkt styku (interfejs dla Bartka):** jedna funkcja w `backend/app/modules/learning_style/hooks.py`:

```python
def record_quiz_result(
    db: Session, *, user: User, lesson_id: int, block_id: str, percent: int
) -> QuizFeedback | None:
    """Wywołać PO ocenieniu quizu na serwerze. Dla ucznia bez profilu i dla nie-uczniów zwraca None."""

@dataclass(frozen=True)
class QuizFeedback:
    passed: bool                     # percent >= 70
    weights: dict[str, int]          # wagi po aktualizacji
    weights_changed: bool
    why: str                         # „bo quiz w lekcji »…«: 45% (próg 70%)”
    proposal: StyleProposal | None   # jak w LearningProfileResponse.proposal
```

- Wynik procentowy liczy **serwer** (endpoint sprawdzania quizu Bartka). Celowo nie dodajemy endpointu, na który przeglądarka sama wysyła wynik, bo uczeń mógłby go podrobić.
- Bartek w swoim endpoincie: `feedback = record_quiz_result(...)` i dokłada `feedback` do odpowiedzi (np. pole `adaptation`). Po stronie frontu wstawia `<AdaptationFeedback feedback={...} />`. To jest **jego** zmiana w **jego** kodzie (jedna linia + jedno pole), opisana tu jako kontrakt.
- Do czasu gotowego quizu funkcja jest w pełni testowana jednostkowo, a propozycja i tak pojawia się w profilu i w notce lekcji (sekcja 3), bo jest liczona z wag w `GET /profile/learning-style`.

## 5. Zmiany w istniejących plikach (wymagają akceptacji)

| # | Plik | Zmiana | Dlaczego nie da się bez niej |
|---|---|---|---|
| B1 | `backend/app/main.py` (importy l. 7–9, rejestracja l. 23–29) | +1 import `from app.modules.learning_style.router import survey_router, profile_router, personalized_router` i +3 linie `app.include_router(...)` | FastAPI widzi tylko routery zarejestrowane w `create_app()`; to jedyne takie miejsce |
| B2 | `backend/alembic/env.py` (po l. 10) | +1 linia `from app.modules.learning_style import models as _learning_style_models  # noqa: F401` | bez tego `alembic revision --autogenerate` (np. u Bartka) uzna nasze tabele za zbędne i wygeneruje ich **usunięcie**. Sama migracja działa i bez tego |
| B3 | `.gitignore` (koniec pliku) | +1 linia `*.bak` | `backend/.env.v1.bak` z kluczami nie jest ignorowany; teraz chroni go tylko lokalny `.git/info/exclude`, którego Bartek nie ma |
| F1 | `frontend/src/app/(app)/layout.tsx` (l. 8–10) | owinięcie `children` w `<SurveyGate>` wewnątrz `AuthGuard` | layout to jedyne wspólne miejsce wszystkich stron; bez tego nie da się przekierować ucznia na ankietę po zalogowaniu |
| F2 | `frontend/src/app/(focus)/layout.tsx` (l. 8–10) | jak F1 | lekcje mają osobny layout „focus”, więc bez tego wejście z linku prosto do lekcji omija bramkę. Backend i tak zwraca 403, ale bez przekierowania byłby tylko ekran błędu |
| F3 | `frontend/src/features/auth/components/AuthenticatedShell.tsx` (l. 13) | `student: [{ href: "/courses", label: "Kursy" }, { href: "/profile", label: "Mój styl" }]` | menu jest zdefiniowane na sztywno w tym pliku |
| F4 | `frontend/src/features/courses/components/LessonView.tsx` (l. 8, 24, 94) | import `usePersonalizedBlocks` zamiast `useLessonBlocks` (ten sam kształt `blocks.data.blocks`) + `<PersonalizationNote … />` nad listą bloków (ok. 3–4 linie) | to jedyny widok lekcji ucznia; bez tego uczeń widzi wszystkie bloki i profilowanie nie działa |

Bez zmian zostają: `users`/`User`, `content/service.py` (tylko import `get_blocks`), `/lessons/{id}/blocks`, testy Bartka i `conftest.py`, bo nasze testy używają jego fixture'ów bez modyfikacji.

## 6. Plan testów (pytest, `backend/tests/learning_style/`)

Czyste funkcje (szybkie, bez bazy):
- `test_scoring.py`: liczenie punktów, styl dominujący, remis → `VA`/`VAK`, brak odpowiedzi → błąd, nieznany styl → błąd, walidacja stylu (`AV` i `VV` niepoprawne).
- `test_personalization.py`: tekst zawsze widoczny; załącznik `[V]` widoczny dla `V`, ukryty dla `A`; `[V,A]` widoczny dla `A`; styl `VA` widzi V i A; kolejność bez zmian; `hidden_count`.
- `test_adaptation.py`: wagi startowe i przycinanie 0–30; +1/−1 dla każdej litery stylu; „pierwszy sukces / pierwsza porażka”; propozycja tylko dla samodzielnego lidera; brak propozycji przy stylu ręcznym, przy remisie i po odrzuceniu; teksty „dlaczego”.

API (baza testowa, fixture'y `client`, `login`, `student`, `teacher`, `make_course` z `conftest.py`):
- `test_survey_api.py`: migracja dała 20 aktywnych pytań po 3 odpowiedzi; odpowiedź bez `style`; poprawne wysłanie tworzy profil i wynik; błędy `SURVEY_INCOMPLETE`, `SURVEY_DUPLICATE_ANSWER`, `SURVEY_ANSWER_MISMATCH`; nauczyciel → 403; ponowna ankieta nadpisuje styl, zeruje odrzuconą propozycję i zostawia historię; 401 bez logowania.
- `test_profile_api.py`: profil przed ankietą (`survey_completed: false`); ręczny styl → `manual`; `DELETE` wraca do ankiety; zmiana przed ankietą → `SURVEY_REQUIRED`; accept/reject propozycji, `NO_PROPOSAL`.
- `test_personalized_blocks_api.py`: lekcja z blokami V, A, K i tekstem; uczeń V widzi tekst + V; uczeń bez ankiety → 403; nauczyciel widzi wszystko; nieopublikowany kurs → 404 jak u Bartka; `file_url` zachowany.
- `test_quiz_hook.py`: `record_quiz_result` zapisuje próbę, zmienia wagi raz na lekcję i styl, zwraca propozycję; dla nauczyciela i ucznia bez profilu → `None`.

Kontrola całości: `pytest` (wszystkie testy, w tym 178 Bartka, muszą przechodzić), `ruff check .`, `ruff format --check .`; frontend: `npm run lint`, `npm run build`; ręczny przejazd w przeglądarce (rejestracja ucznia → ankieta → wynik → lekcja z materiałami V/A/K → zmiana stylu → inna treść lekcji).

## 7. Kolejność prac i commity (lokalne, bez push i merge)

1. `feat(learning-style): add survey tables, VAK questions and scoring`: modele, migracja z pytaniami, `scoring.py` + testy.
2. `feat(learning-style): add survey and learning profile API`: endpointy ankiety i profilu + testy (+ B1, B2 po akceptacji).
3. `feat(learning-style): add personalized lesson blocks`: filtr + endpoint + testy.
4. `feat(learning-style): add simplified adaptation and quiz hook`: wagi, propozycja, `record_quiz_result` + testy.
5. `feat(frontend): add VAK survey, result and learning style profile`: strony i komponenty (+ F1–F3).
6. `feat(frontend): show lesson blocks matching the student's learning style`: F4 + notka i baner.

Po każdym kroku dopisuję wpis w `docs/RAPORT-ankieta-vak.md`.

## 8. Do decyzji przy akceptacji

1. Zmiany B1–B3 i F1–F4: akceptujesz wszystkie, czy któreś inaczej?
2. Pytania ankiety w migracji (proponuję) czy osobna komenda seed?
3. Uczeń bez ankiety: 403 na `/personalized-blocks` (proponuję) czy pokazywać tylko bloki tekstowe?
4. Nazwy ścieżek po angielsku (`/survey`, `/profile`) jak reszta v2? Teksty w UI są po polsku.
