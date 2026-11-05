import { useMutation, useQuery } from "@tanstack/react-query";

import { lessonsApi } from "./api";
import type { AnswerValue } from "./types";

export function useSkillLesson(skillId: number) {
  return useQuery({
    queryKey: ["skills", skillId, "lesson"],
    queryFn: () => lessonsApi.getForSkill(skillId),
  });
}

type CheckInput = { stepKey: string; answer: AnswerValue; reveal?: boolean };

export function useCheckAnswer(lessonId: number) {
  return useMutation({
    mutationFn: ({ stepKey, answer, reveal = false }: CheckInput) =>
      lessonsApi.check(lessonId, stepKey, answer, reveal),
  });
}
