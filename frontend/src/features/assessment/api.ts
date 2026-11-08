import { api } from "@/shared/api/client";

import type { AttemptResult, QuizContent, QuizQuestion, StudentQuiz } from "./types";

const quizPath = (lessonId: number) => `/lessons/${lessonId}/quiz`;

export const assessmentApi = {
  quiz: (lessonId: number) => api.get<StudentQuiz>(quizPath(lessonId)),
  submit: (lessonId: number, answers: Record<string, string>) =>
    api.post<AttemptResult>(`${quizPath(lessonId)}/attempts`, { answers }),

  quizForEditing: (lessonId: number) =>
    api.get<QuizContent>(`${quizPath(lessonId)}/edit`),
  save: (lessonId: number, questions: QuizQuestion[]) =>
    api.put<QuizContent>(quizPath(lessonId), { questions }),
  remove: (lessonId: number) => api.delete(quizPath(lessonId)),
};
