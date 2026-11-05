import type { LessonMethod } from "./types";

// Names shown to teachers and admins; student never see variants
export const methodLabels: Record<LessonMethod, string> = {
  common: "Wspólny",
  alpha: "Alfa",
  beta: "Beta",
  gamma: "Gamma",
  delta: "Delta",
};

export function isLessonMethod(
  value: string | undefined,
): value is LessonMethod {
  return value !== undefined && value in methodLabels;
}
