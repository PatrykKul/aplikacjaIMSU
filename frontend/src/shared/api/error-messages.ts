import { ApiError } from "./client";

const messages: Record<string, string> = {
  INVALID_CREDENTIALS: "Nieprawidłowy e-mail lub hasło.",
  EMAIL_TAKEN:
    "Konto z tym adresem e-mail już istnieje. Zaloguj się albo użyj innego adresu.",
  NOT_AUTHENTICATED: "Sesja wygasła. Zaloguj się ponownie.",
  FORBIDDEN: "Nie masz uprawnień do tej operacji.",
  USER_NOT_FOUND: "Nie znaleziono użytkownika.",
  COURSE_NOT_FOUND: "Nie znaleziono kursu. Mógł zostać usunięty.",
  LESSON_NOT_FOUND: "Nie znaleziono lekcji. Mogła zostać usunięta.",
  LESSON_ORDER_MISMATCH:
    "Lista lekcji zmieniła się w międzyczasie. Odśwież stronę i spróbuj ponownie.",
  FILE_TYPE_NOT_ALLOWED:
    "Tego rodzaju pliku nie można dodać. Wybierz obraz (PNG, JPG, WEBP, GIF), nagranie (MP3, OGG, WAV, M4A), film (MP4, WEBM) albo PDF.",
  FILE_TOO_LARGE: "Plik jest za duży. Największy dozwolony rozmiar to 50 MB.",
  FILE_EMPTY: "Plik jest pusty. Wybierz inny plik.",
  FILE_NOT_FOUND:
    "Jeden z plików w lekcji nie istnieje. Usuń ten załącznik i dodaj plik ponownie.",
  FILE_KIND_MISMATCH:
    "Plik w jednym z załączników nie pasuje do jego typu. Dodaj właściwy plik.",
  VALIDATION_ERROR: "Sprawdź dane w formularzu.",
  NETWORK_ERROR:
    "Brak połączenia z serwerem. Sprawdź internet i spróbuj ponownie.",
};

const FALLBACK = "Ups! Coś poszło nie tak. Spróbuj ponownie za chwilę.";

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return messages[error.code] ?? FALLBACK;
  }
  return FALLBACK;
}
