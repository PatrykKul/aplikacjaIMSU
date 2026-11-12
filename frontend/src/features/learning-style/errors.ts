import { coursesError } from "@/features/courses/errors";
import { ApiError } from "@/shared/api/client";

const messages: Record<string, string> = {
  SURVEY_INCOMPLETE: "Odpowiedz na wszystkie pytania ankiety.",
  SURVEY_DUPLICATE_ANSWER:
    "Na każde pytanie można wybrać tylko jedną odpowiedź. Odśwież stronę i spróbuj ponownie.",
  SURVEY_ANSWER_MISMATCH:
    "Ankieta zmieniła się w międzyczasie. Odśwież stronę i wypełnij ją ponownie.",
  SURVEY_EMPTY: "Ankieta nie ma jeszcze pytań. Skontaktuj się z nauczycielem.",
  SURVEY_REQUIRED:
    "Najpierw wypełnij ankietę stylu uczenia się i wybierz swój styl.",
  SURVEY_ALREADY_DONE:
    "Ankieta jest już wypełniona – wypełnia się ją tylko raz. Styl możesz zmienić w zakładce „Mój styl”.",
  NO_TIE: "Twój styl jest już wybrany.",
  STYLE_NOT_TIED: "Wybierz jeden ze stylów, które miały remis w ankiecie.",
  SAME_STYLE: "To już jest Twój styl.",
  PROPOSAL_NOT_FOUND: "Ta propozycja jest już nieaktualna.",
  PROPOSAL_NOT_OPEN:
    "Ta propozycja jest już nieaktualna – została przyjęta, odrzucona albo wygasła.",
};

/** Messages for this feature's error codes, then courses (enrollment, lock), then app-wide. */
export function learningStyleError(error: unknown): string {
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return coursesError(error);
}
