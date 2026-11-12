import type { Form } from "@/features/content/types";
import type { QuizFeedback } from "@/features/learning-style/types";

export type QuizAnswer = { id: string; text: string };

/** Question of the pool as the author edits it (with the key and the explanation). */
export type QuizQuestion = {
  id: string;
  text: string;
  answers: QuizAnswer[];
  correct_answer_id: string;
  explanation: string;
};

/** The whole pool (`GET /lessons/{id}/quiz/edit`). */
export type QuizPool = { questions: QuizQuestion[] };

/** Kept for the teacher's screens (name from v2). */
export type QuizContent = QuizPool;

/** Question for a student: no key, no explanation. */
export type StudentQuestion = {
  id: string;
  text: string;
  answers: QuizAnswer[];
};

/** One drawn set of questions (R9); the key stays on the server. */
export type QuizDraw = {
  draw_id: number;
  questions: StudentQuestion[];
  pool_size: number;
  form: Form;
};

export type QuestionResult = {
  question_id: string;
  text: string;
  answers: QuizAnswer[];
  chosen_answer_id: string;
  correct_answer_id: string;
  correct: boolean;
  explanation: string;
};

export type AttemptResult = {
  draw_id: number;
  percent: number;
  correct_count: number;
  total: number;
  passed: boolean;
  results: QuestionResult[];
  feedback: QuizFeedback;
};

/** Limits shared with the backend (`assessment/schemas.py`). */
export const MIN_ANSWERS = 3;
export const MAX_ANSWERS = 4;
export const MAX_QUESTIONS = 50;
export const MIN_PUBLISHED_QUESTIONS = 5;
export const QUIZ_SIZE = 5;
export const EXPLANATION_MAX = 1000;

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
