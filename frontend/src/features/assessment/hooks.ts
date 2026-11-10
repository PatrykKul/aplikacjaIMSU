import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useCurrentUser } from "@/features/auth/hooks";
import {
  learningProfileKey,
  useLearningProfile,
} from "@/features/learning-style/hooks";
import { ApiError } from "@/shared/api/client";

import { assessmentApi } from "./api";
import type { QuizContent, QuizQuestion } from "./types";

/** All student views of a lesson's quiz (one per learning style). */
export const lessonQuizKey = (lessonId: number) => ["quiz", lessonId] as const;
const quizEditKey = (lessonId: number) => ["quiz-edit", lessonId] as const;

/**
 * null when the lesson has no quiz (or none for this student's style).
 * The questions depend on the student's style, so the style is part of the key:
 * after a style change the quiz is fetched again.
 */
export function useLessonQuiz(lessonId: number) {
  const { data: user } = useCurrentUser();
  const isStudent = user?.role === "student";
  const profile = useLearningProfile(isStudent);
  const style = isStudent ? (profile.data?.style ?? null) : "all";
  return useQuery({
    queryKey: [...lessonQuizKey(lessonId), style],
    enabled: !!user && (!isStudent || profile.isSuccess),
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
      void queryClient.invalidateQueries({ queryKey: lessonQuizKey(lessonId) });
    },
  });
}

export function useDeleteQuiz(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => assessmentApi.remove(lessonId),
    onSuccess: () => {
      queryClient.setQueryData(quizEditKey(lessonId), { questions: [] });
      void queryClient.invalidateQueries({ queryKey: lessonQuizKey(lessonId) });
    },
  });
}
