import { api } from "@/shared/api/client";

import type { AnswerValue, CheckResult, Lesson } from "./types";

export const lessonsApi = {
  getForSkill: (skillId: number) =>
    api.get<Lesson>(`/skills/${skillId}/lesson`),
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
