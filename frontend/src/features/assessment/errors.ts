import { learningStyleError } from "@/features/learning-style/errors";
import { ApiError } from "@/shared/api/client";

const messages: Record<string, string> = {
  QUIZ_NOT_FOUND: "Ta lekcja nie ma quizu.",
  QUIZ_INCOMPLETE: "Odpowiedz na wszystkie pytania quizu.",
  QUIZ_ANSWER_MISMATCH: "Quiz zmienił się w międzyczasie. Odśwież stronę i spróbuj ponownie.",
  VALIDATION_ERROR:
    "Sprawdź quiz: każde pytanie musi mieć treść, 3–4 odpowiedzi z treścią i zaznaczoną poprawną.",
};

export function assessmentError(error: unknown): string {
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return learningStyleError(error);
}
