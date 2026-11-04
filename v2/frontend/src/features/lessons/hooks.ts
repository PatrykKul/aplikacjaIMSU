import { useMutation, useQuery } from "@tanstack/react-query";

import { lessonsApi } from "./api";
import type { AnswerValue } from "./types";

export function useSkillLessons(skillId: number) {
  return useQuery({
    queryKey: ["skills", skillId, "lessons"],
    queryFn: () => lessonsApi.listForSkill(skillId),
  });
}

export function useLesson(id: number | undefined) {
  return useQuery({
    queryKey: ["lessons", id],
    queryFn: () => lessonsApi.get(id as number),
    enabled: id !== undefined,
  });
}

type CheckInput = { stepKey: string; answer: AnswerValue; reveal?: boolean };

export function useCheckAnswer(lessonId: number) {
  return useMutation({
    mutationFn: ({ stepKey, answer, reveal = false }: CheckInput) =>
      lessonsApi.check(lessonId, stepKey, answer, reveal),
  });
}
