import { ApiError } from "./client";

const messages: Record<string, string> = {
  INVALID_CREDENTIALS: "Nieprawidłowy e-mail lub hasło.",
  EMAIL_TAKEN:
    "Konto z tym adresem e-mail już istnieje. Zaloguj się albo użyj innego adresu.",
  NOT_AUTHENTICATED: "Sesja wygasła. Zaloguj się ponownie.",
  FORBIDDEN: "Nie masz uprawnień do tej operacji.",
  USER_NOT_FOUND: "Nie znaleziono użytkownika.",
  CANNOT_MODIFY_SELF:
    "Nie możesz zmienić własnej roli ani zablokować własnego konta.",
  COURSE_NOT_FOUND: "Nie znaleziono kursu. Mógł zostać wycofany z publikacji.",
  SKILL_NOT_FOUND: "Nie znaleziono umiejętności.",
  LESSON_NOT_FOUND: "Nie znaleziono lekcji. Mogła zostać wycofana.",
  ANSWER_NOT_A_NUMBER: "Wpisz liczbę, np. 12,5.",
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
