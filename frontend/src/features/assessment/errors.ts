import { learningStyleError } from "@/features/learning-style/errors";
import { ApiError } from "@/shared/api/client";

const messages: Record<string, string> = {
  QUIZ_NOT_FOUND: "Ta lekcja nie ma jeszcze quizu.",
  QUIZ_INCOMPLETE: "Odpowiedz na wszystkie pytania quizu.",
  QUIZ_ANSWER_MISMATCH:
    "Pytania zmieniły się w międzyczasie. Wczytaj nowy zestaw i spróbuj ponownie.",
  DRAW_NOT_OPEN:
    "Ten zestaw pytań został już sprawdzony. Wczytaj nowy zestaw i spróbuj ponownie.",
  VALIDATION_ERROR:
    "Sprawdź quiz: każde pytanie musi mieć treść, 3–4 odpowiedzi z treścią, zaznaczoną poprawną i wyjaśnienie.",
};

export function assessmentError(error: unknown): string {
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return learningStyleError(error);
}
