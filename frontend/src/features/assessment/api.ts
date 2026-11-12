import { api } from "@/shared/api/client";

import type { AttemptResult, QuizDraw, QuizPool, QuizQuestion } from "./types";

const quizPath = (lessonId: number) => `/lessons/${lessonId}/quiz`;

export const assessmentApi = {
  /** The open set of questions or a new draw. */
  quiz: (lessonId: number) => api.get<QuizDraw>(quizPath(lessonId)),
  submit: (lessonId: number, drawId: number, answers: Record<string, string>) =>
    api.post<AttemptResult>(`${quizPath(lessonId)}/attempts`, {
      draw_id: drawId,
      answers,
    }),

  pool: (lessonId: number) => api.get<QuizPool>(`${quizPath(lessonId)}/edit`),
  save: (lessonId: number, questions: QuizQuestion[]) =>
    api.put<QuizPool>(quizPath(lessonId), { questions }),
  remove: (lessonId: number) => api.delete(quizPath(lessonId)),
};
