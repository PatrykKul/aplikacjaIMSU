import { api } from "@/shared/api/client";

import type { AnswerValue, CheckResult, Lesson, LessonSummary } from "./types";

export const lessonsApi = {
  listForSkill: (skillId: number) =>
    api.get<LessonSummary[]>(`/skills/${skillId}/lessons`),
  get: (id: number) => api.get<Lesson>(`/lessons/${id}`),
  check: (
    lessonId: number,
    stepKey: string,
    answer: AnswerValue,
    reveal: boolean,
  ) =>
    api.post<CheckResult>(`/lessons/${lessonId}/steps/${stepKey}/check`, {
      answer,
      reveal,
    }),
};
