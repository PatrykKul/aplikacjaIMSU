import { authError } from "@/features/auth/errors";
import { ApiError } from "@/shared/api/client";

import { type ReadinessIssue } from "./types";

const messages: Record<string, string> = {
  COURSE_HAS_NO_PUBLISHED_LESSONS:
    "Kurs bez opublikowanej lekcji byłby pusty dla ucznia. Najpierw opublikuj co najmniej jedną lekcję.",
  LESSON_NOT_READY:
    "Lekcja nie jest gotowa do publikacji. Uzupełnij braki z listy i spróbuj ponownie.",
  LAST_PUBLISHED_LESSON:
    "To ostatnia opublikowana lekcja opublikowanego kursu. Najpierw wycofaj publikację kursu albo opublikuj inną lekcję.",
  PUBLISHED_LESSON_INCOMPLETE:
    "Opublikowana lekcja musi zostać kompletna, a ta zmiana usunęłaby wymagany element. Najpierw wycofaj publikację lekcji.",
  ENROLLMENT_NOT_FOUND:
    "Nie znaleziono tej prośby o zapis. Odśwież stronę – mogła zostać już rozpatrzona.",
  STUDENT_NOT_FOUND: "Ten uczeń nie jest zapisany na kurs.",
  QUIZ_NOT_FOUND: "Lekcja nie ma jeszcze pytań.",
};

/** Messages for this feature's error codes, then the app-wide ones. */
export function teachError(error: unknown): string {
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return authError(error);
}

/** Issues sent with 409 LESSON_NOT_READY / PUBLISHED_LESSON_INCOMPLETE. */
export function errorIssues(error: unknown): ReadinessIssue[] {
  if (!(error instanceof ApiError)) {
    return [];
  }
  const issues = error.params.issues;
  return Array.isArray(issues) ? (issues as ReadinessIssue[]) : [];
}
