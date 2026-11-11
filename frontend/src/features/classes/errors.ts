import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";

const messages: Record<string, string> = {
  CLASSROOM_NOT_FOUND: "Nie znaleziono klasy. Mogła zostać usunięta.",
  STUDENT_NOT_FOUND:
    "Nie znaleziono ucznia. Jego konto mogło zostać zablokowane — wyszukaj go ponownie.",
};

/** Messages for this feature's error codes, then the app-wide ones. */
export function classroomsError(error: unknown): string {
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return errorMessage(error);
}
