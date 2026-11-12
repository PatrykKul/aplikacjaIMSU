import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { courseKey, coursesKey, lessonKey } from "@/features/courses/hooks";
import {
  learningProfileKey,
  lessonQuizKey,
  studyKey,
} from "@/features/learning-style/hooks";
import { ApiError } from "@/shared/api/client";

import { assessmentApi } from "./api";
import type { QuizPool, QuizQuestion } from "./types";

export { lessonQuizKey };
export const quizPoolKey = (lessonId: number) =>
  ["lessons", lessonId, "quiz-edit"] as const;
const readinessKey = (lessonId: number) =>
  ["lessons", lessonId, "readiness"] as const;

function isQuizMissing(error: unknown): boolean {
  return error instanceof ApiError && error.code === "QUIZ_NOT_FOUND";
}

/** The set of questions of a student; null when the lesson has no quiz. */
export function useLessonQuiz(lessonId: number, enabled = true) {
  return useQuery({
    queryKey: lessonQuizKey(lessonId),
    enabled,
    queryFn: async () => {
      try {
        return await assessmentApi.quiz(lessonId);
      } catch (error) {
        if (isQuizMissing(error)) {
          return null;
        }
        throw error;
      }
    },
  });
}

/**
 * After an attempt the profile, the lesson (form, suggestion, next lesson),
 * the course (lesson states), progress and journal may have changed.
 */
export function useSubmitQuiz(lessonId: number, courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      drawId,
      answers,
    }: {
      drawId: number;
      answers: Record<string, string>;
    }) => assessmentApi.submit(lessonId, drawId, answers),
    onSuccess: () =>
      Promise.all([
        // The set is closed now: the next visit draws a new one
        queryClient.invalidateQueries({
          queryKey: lessonQuizKey(lessonId),
          refetchType: "none",
        }),
        queryClient.invalidateQueries({ queryKey: learningProfileKey }),
        queryClient.invalidateQueries({ queryKey: studyKey(lessonId) }),
        queryClient.invalidateQueries({
          queryKey: lessonKey(lessonId),
          exact: true,
        }),
        queryClient.invalidateQueries({ queryKey: courseKey(courseId) }),
        queryClient.invalidateQueries({ queryKey: coursesKey, exact: true }),
        queryClient.invalidateQueries({ queryKey: ["me"] }),
      ]),
  });
}

/** The whole pool with the key (author, admin); empty when there is no quiz. */
export function useQuizPool(lessonId: number, enabled = true) {
  return useQuery({
    queryKey: quizPoolKey(lessonId),
    enabled,
    queryFn: async (): Promise<QuizPool> => {
      try {
        return await assessmentApi.pool(lessonId);
      } catch (error) {
        if (isQuizMissing(error)) {
          return { questions: [] };
        }
        throw error;
      }
    },
  });
}

/** Kept name for the teacher's editor. */
export const useQuizForEditing = useQuizPool;

export function useSaveQuiz(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (questions: QuizQuestion[]) =>
      assessmentApi.save(lessonId, questions),
    onSuccess: (saved: QuizPool) => {
      queryClient.setQueryData(quizPoolKey(lessonId), saved);
      return queryClient.invalidateQueries({
        queryKey: readinessKey(lessonId),
      });
    },
  });
}

export function useDeleteQuiz(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => assessmentApi.remove(lessonId),
    onSuccess: () => {
      queryClient.setQueryData<QuizPool>(quizPoolKey(lessonId), {
        questions: [],
      });
      return queryClient.invalidateQueries({
        queryKey: readinessKey(lessonId),
      });
    },
  });
}
