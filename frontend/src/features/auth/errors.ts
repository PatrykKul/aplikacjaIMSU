import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";

const messages: Record<string, string> = {
  TEACHER_NOT_APPROVED:
    "Twoje konto nauczyciela nie jest jeszcze zatwierdzone przez administratora.",
};

/** Messages for this feature's error codes, then the app-wide ones. */
export function authError(error: unknown): string {
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return errorMessage(error);
}

/** True when the server refused a teacher action because of the approval. */
export function isNotApproved(error: unknown): boolean {
  return error instanceof ApiError && error.code === "TEACHER_NOT_APPROVED";
}
