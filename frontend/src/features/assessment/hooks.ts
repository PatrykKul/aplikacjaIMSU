import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { learningProfileKey } from "@/features/learning-style/hooks";
import { ApiError } from "@/shared/api/client";

import { assessmentApi } from "./api";
import type { QuizContent, QuizQuestion } from "./types";

const quizKey = (lessonId: number) => ["quiz", lessonId] as const;
const quizEditKey = (lessonId: number) => ["quiz", lessonId, "edit"] as const;

/** null when the lesson has no quiz (or none for this student's style). */
export function useLessonQuiz(lessonId: number) {
  return useQuery({
    queryKey: quizKey(lessonId),
    queryFn: async () => {
      try {
        return await assessmentApi.quiz(lessonId);
      } catch (error) {
        if (error instanceof ApiError && error.code === "QUIZ_NOT_FOUND") {
          return null;
        }
        throw error;
      }
    },
  });
}

export function useSubmitQuiz(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (answers: Record<string, string>) =>
      assessmentApi.submit(lessonId, answers),
    // Weights and the style proposal may have changed
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: learningProfileKey }),
  });
}

export function useQuizForEditing(lessonId: number) {
  return useQuery({
    queryKey: quizEditKey(lessonId),
    queryFn: () => assessmentApi.quizForEditing(lessonId),
  });
}

export function useSaveQuiz(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (questions: QuizQuestion[]) =>
      assessmentApi.save(lessonId, questions),
    onSuccess: (saved: QuizContent) => {
      queryClient.setQueryData(quizEditKey(lessonId), saved);
      void queryClient.invalidateQueries({ queryKey: quizKey(lessonId), exact: true });
    },
  });
}

export function useDeleteQuiz(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => assessmentApi.remove(lessonId),
    onSuccess: () => {
      queryClient.setQueryData(quizEditKey(lessonId), { questions: [] });
      void queryClient.invalidateQueries({ queryKey: quizKey(lessonId), exact: true });
    },
  });
}
