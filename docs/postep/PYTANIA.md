# Pytania i decyzje do potwierdzenia

Format: pytanie · wybrany wariant · gdzie w kodzie (`TODO(decyzja)` / `TODO(prowadzący)`).

## Do prowadzącego (z notatki `../Projekt-zaliczeniowy.md`)
- Termin i forma oddania (prezentacja / repo / dokumentacja)?
- Indywidualnie czy w grupie?
- Czy technologia jest dowolna?
- Jak „inteligentny" ma być dobór materiałów (reguły vs. ML)? — przyjęto: reguły + adaptacja wag.
- Jakie elementy multimedialne są wymagane? — przyjęto: obraz, diagram, wideo, audio, ćwiczenie, quiz.
- Czy pytania ankiety VAK mają pochodzić z konkretnego, uznanego kwestionariusza? — przyjęto: 20 autorskich pytań (`backend/app/seed_ankieta.py`), nauczyciel może je edytować.
- Czy progi adaptacji (70% zaliczenie, 90% rozszerzenia, krok wag ±1) są odpowiednie? — przyjęto wartości z opisu projektu; stałe w `backend/app/services/adaptacja.py`.

## Decyzje podjęte samodzielnie (do potwierdzenia przez autora)
- **Etap 1 – „swoi uczniowie" nauczyciela.** Brak modelu klas/zapisów na kurs, więc nauczyciel widzi wszystkich uczniów. Wariant najprostszy; `TODO(decyzja)` w kodzie panelu nauczyciela.
- **Etap 1 – sesja.** Token JWT w `localStorage` (bez ciasteczek httpOnly). Wystarczające dla projektu zaliczeniowego.
- **Etap 2 – remis w ankiecie.** Styl mieszany zapisujemy jako litery (`VA`, `VAK`); uczeń widzi bloki wszystkich remisujących stylów. Ręcznie wybiera się tylko jeden styl.
- **Etap 2 – każde pytanie ma dokładnie po jednej odpowiedzi na styl V/A/K.**
- **Etap 3 – audio bez nagrań.** Kurs demo nie ma plików audio; omówienie czyta lektor przeglądarki (Web Speech API). Nauczyciel może wgrać nagranie.
- **Etap 3 – brak filmów w kursie demo.** Nie wstawiam niezweryfikowanych linków do cudzych filmów; typ `wideo` jest gotowy do użycia.
- **Etap 4 – źródło stylu `adaptacja`.** Opis przewiduje `ankieta` / `reczny`; dodałem trzecią wartość dla stylu przyjętego z propozycji systemu, żeby ręczny wybór nadal miał pierwszeństwo, a propozycje mogły działać dalej.
- **Etap 4 – wagi a powtarzanie quizu.** Liczy się tylko pierwszy sukces i pierwsza porażka w danym temacie i stylu.
- **Etap 4 – poziom trudności** liczony z dwóch ostatnich quizów ucznia (niezależnie od tematu).
