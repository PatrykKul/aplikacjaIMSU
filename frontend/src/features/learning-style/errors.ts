import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";

const messages: Record<string, string> = {
  SURVEY_INCOMPLETE: "Odpowiedz na wszystkie pytania ankiety.",
  SURVEY_DUPLICATE_ANSWER:
    "Na każde pytanie można wybrać tylko jedną odpowiedź. Odśwież stronę i spróbuj ponownie.",
  SURVEY_ANSWER_MISMATCH:
    "Ankieta zmieniła się w międzyczasie. Odśwież stronę i wypełnij ją ponownie.",
  SURVEY_EMPTY: "Ankieta nie ma jeszcze pytań. Skontaktuj się z nauczycielem.",
  SURVEY_REQUIRED: "Najpierw wypełnij ankietę stylu uczenia się.",
  BLOCK_NOT_FOUND:
    "Tego materiału nie ma już w lekcji. Odśwież stronę i spróbuj ponownie.",
  NO_PROPOSAL: "Ta propozycja jest już nieaktualna.",
};

/** Messages for this feature's error codes, then the app-wide ones. */
export function learningStyleError(error: unknown): string {
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return errorMessage(error);
}
