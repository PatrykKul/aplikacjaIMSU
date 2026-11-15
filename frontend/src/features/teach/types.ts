import type { JSONContent } from "@tiptap/react";

import type { Block, Form } from "@/features/content/types";

// Types of the teacher's endpoints (docs/08-praca-biezaca.md, section API).

export type Percentages = Record<Form, number>;

// --- curriculum ---

/** `GET /courses` for the author: own courses. */
export type TeacherCourseSummary = {
  id: number;
  title: string;
  description: string;
  owner: { id: number; display_name: string };
  is_published: boolean;
  is_archived: boolean;
  /** For the author: all lessons, published or not. */
  lesson_count: number;
  /** Requests to join waiting for the author's decision. */
  pending_requests: number | null;
  updated_at: string;
};

export type TeacherLessonSummary = {
  id: number;
  title: string;
  number: number;
  outline: JSONContent | null;
  is_published: boolean;
};

/** `GET /courses/{id}` as the author sees it. */
export type TeacherCourse = TeacherCourseSummary & {
  introduction: JSONContent | null;
  summary: JSONContent | null;
  lessons: TeacherLessonSummary[];
};

export type CourseCreateInput = { title: string; description: string };

export type CourseUpdateInput = {
  title?: string;
  description?: string;
  introduction?: JSONContent;
  summary?: JSONContent;
  is_published?: boolean;
};

/** `GET /lessons/{id}` (fields the editor uses). */
export type TeacherLesson = {
  id: number;
  title: string;
  number: number;
  outline: JSONContent | null;
  conclusions: JSONContent | null;
  is_published: boolean;
  course: { id: number; title: string; owner_id: number };
};

export type LessonUpdateInput = {
  title?: string;
  outline?: JSONContent;
  conclusions?: JSONContent;
};

// --- enrollments ---

export type EnrollmentStatus = "pending" | "accepted" | "rejected";

export type StudentRef = { id: number; display_name: string; email: string };

export type Enrollment = {
  student: StudentRef;
  status: EnrollmentStatus;
  requested_at: string;
  decided_at: string | null;
};

// --- content ---

export type LessonVersions = Record<Form, { blocks: Block[] }>;

// --- assessment: the question pool ---

export type PoolAnswer = { id: string; text: string };

export type PoolQuestion = {
  id: string;
  text: string;
  answers: PoolAnswer[];
  correct_answer_id: string;
  explanation: string;
};

export type QuizPool = { questions: PoolQuestion[] };

// --- authoring: readiness and publication (R11) ---

export type IssueArea = "lesson" | Form | "quiz";

export type ReadinessIssue = {
  area: IssueArea;
  code: string;
  count?: number;
  min?: number;
};

export type Readiness = { ready: boolean; issues: ReadinessIssue[] };

// --- learning_style: course statistics ---

export type FormEffectiveness = {
  /** Average of counted results in percent; null without data. */
  average: number | null;
  counted_results: number;
  attempts: number;
  students: number;
};

export type CourseStudentRow = {
  id: number;
  display_name: string;
  email: string;
  /** Active style; null while a survey tie is unresolved (or no survey). */
  style: Form | null;
  percentages: Percentages | null;
  passed: number;
  total: number;
  average: number | null;
  last_activity: string | null;
  open_proposal: { to: Form; kind: "switch" | "revert" } | null;
  /** R12: three or more failed counted results in a row (all courses). */
  attention: Attention | null;
};

/** One of the last three counted results of a streak (chronological order). */
export type AttentionResult = {
  lesson_id: number;
  lesson_title: string;
  form: Form;
  percent: number;
};

/** R12 `Attention`: the current streak of failed counted results. */
export type Attention = {
  streak: number;
  results: AttentionResult[];
};

/** A published lesson in `GET /courses/{id}/stats` → `lessons`. */
export type LessonStatsRow = {
  lesson_id: number;
  title: string;
  number: number;
  /** Students with at least one attempt. */
  started: number;
  /** Students with a passed attempt. */
  passed: number;
  /** Percent of `passed / started`; null when `started < 3`. */
  pass_rate: number | null;
  /** Average of the counted results; null when `started < 3`. */
  first_average: number | null;
  first_results: number;
  /** Average attempts up to the first pass (1 decimal); null when `passed = 0`. */
  attempts_to_pass: number | null;
};

export type MatrixCell = {
  /** Average of the counted results in the form; null when `n < 2`. */
  average: number | null;
  n: number;
};

export type LessonFormMatrixRow = {
  lesson_id: number;
  title: string;
  number: number;
  cells: Record<Form, MatrixCell>;
};

export type FormGapSide = { form: Form; average: number; n: number };

/** A lesson whose best and worst form differ by at least 20 points. */
export type FormGap = {
  lesson_id: number;
  title: string;
  number: number;
  best: FormGapSide;
  worst: FormGapSide;
};

export type CourseStats = {
  forms: Record<Form, FormEffectiveness>;
  styles: Record<Form | "none", number>;
  students: CourseStudentRow[];
  pending_requests: number;
  /** Published lessons in the order of the course. */
  lessons: LessonStatsRow[];
  /** Lowest pass rate among lessons with 3+ students; null without one. */
  hardest: LessonStatsRow | null;
  matrix: LessonFormMatrixRow[];
  form_gaps: FormGap[];
};

// --- assessment: question statistics ---

export type QuestionRating = "hard" | "easy" | "normal";

export type TopWrongAnswer = {
  answer_id: string;
  text: string;
  count: number;
  /** `count / drawn` in percent; null when `drawn < 5`. */
  percent: number | null;
};

export type QuestionStatsRow = {
  question_id: string;
  text: string;
  /** In how many submitted draws the question was. */
  drawn: number;
  correct: number;
  /** null when `drawn < 5`. */
  correct_percent: number | null;
  /** The most chosen wrong answer; null when nobody answered wrong. */
  top_wrong: TopWrongAnswer | null;
  /** null when `drawn < 5`. */
  rating: QuestionRating | null;
};

/** `GET /courses/{id}/question-stats`: one item per published lesson. */
export type LessonQuestionStats = {
  lesson_id: number;
  title: string;
  number: number;
  /** Sorted by the backend: lowest `correct_percent` first, null last. */
  questions: QuestionStatsRow[];
};

/** Limits shared with the backend (`curriculum/schemas.py`, `assessment/schemas.py`). */
export const TITLE_MAX = 120;
export const DESCRIPTION_MAX = 500;
export const QUIZ_SIZE = 5;
export const POOL_MAX = 50;
export const MIN_ANSWERS = 3;
export const MAX_ANSWERS = 4;
export const QUESTION_MAX = 500;
export const ANSWER_MAX = 200;
export const EXPLANATION_MAX = 1000;
