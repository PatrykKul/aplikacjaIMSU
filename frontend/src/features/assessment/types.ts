import type { Form } from "@/features/content/types";
import type { QuizFeedback } from "@/features/learning-style/types";

export type QuizAnswer = { id: string; text: string };

/** Question as the author edits it (with the answer key). */
export type QuizQuestion = {
  id: string;
  text: string;
  /** Material the question is about; null = common part of the lesson. */
  form: Form | null;
  answers: QuizAnswer[];
  correct_answer_id: string;
};

export type QuizContent = { questions: QuizQuestion[] };

/** Question for a student: no answer key. */
export type StudentQuestion = Omit<QuizQuestion, "correct_answer_id">;

export type StudentQuiz = {
  questions: StudentQuestion[];
  hidden_count: number;
};

export type QuestionResult = {
  question_id: string;
  correct: boolean;
  chosen_answer_id: string;
  correct_answer_id: string;
};

export type AttemptResult = {
  percent: number;
  correct_count: number;
  total: number;
  results: QuestionResult[];
  /** Present for students: what the adaptation changed after this quiz. */
  adaptation: QuizFeedback | null;
};

export const MIN_ANSWERS = 3;
export const MAX_ANSWERS = 4;
export const MAX_QUESTIONS = 20;

/** "1 pytanie", "3 pytania", "5 pytań", "22 pytania". */
export function questionsLabel(count: number): string {
  if (count === 1) return "1 pytanie";
  const teen = count % 100 >= 12 && count % 100 <= 14;
  const few = count % 10 >= 2 && count % 10 <= 4 && !teen;
  return `${count} ${few ? "pytania" : "pytań"}`;
}

export function newQuizId(prefix: "q" | "a"): string {
  return `${prefix}-${crypto.randomUUID().slice(0, 8)}`;
}
