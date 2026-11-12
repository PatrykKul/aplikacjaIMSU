import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";

/** `required_lesson` of LESSON_LOCKED. */
export type RequiredLesson = { id: number; title: string; number: number };

export function requiredLesson(error: unknown): RequiredLesson | null {
  if (!(error instanceof ApiError) || error.code !== "LESSON_LOCKED") {
    return null;
  }
  const value = error.params.required_lesson as RequiredLesson | undefined;
  return value && typeof value.id === "number" ? value : null;
}

export function isErrorCode(error: unknown, code: string): boolean {
  return error instanceof ApiError && error.code === code;
}

const messages: Record<string, string> = {
  ENROLLMENT_REQUIRED:
    "Ta lekcja jest dostępna po zapisaniu się na kurs i przyjęciu przez nauczyciela.",
  ALREADY_ENROLLED: "Jesteś już zapisany na ten kurs.",
  TEACHER_NOT_APPROVED:
    "Ten nauczyciel nie ma zatwierdzonego konta. Wybierz zatwierdzonego nauczyciela.",
  COURSE_HAS_NO_PUBLISHED_LESSONS:
    "Kurs nie ma jeszcze opublikowanej lekcji, więc nie można go opublikować.",
};

/** Messages for this feature's error codes, then the app-wide ones. */
export function coursesError(error: unknown): string {
  const required = requiredLesson(error);
  if (required) {
    return `Ta lekcja jest jeszcze zablokowana. Najpierw zalicz lekcję ${required.number}: „${required.title}”.`;
  }
  if (isErrorCode(error, "LESSON_LOCKED")) {
    return "Ta lekcja jest jeszcze zablokowana. Najpierw zalicz poprzednią lekcję.";
  }
  if (error instanceof ApiError && messages[error.code]) {
    return messages[error.code];
  }
  return errorMessage(error);
}
