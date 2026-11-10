import type { Block, Form } from "@/features/content/types";

/** One or more letters in V-A-K order, e.g. "V", "VA", "VAK". */
export type LearningStyle = string;

export type StyleSource = "survey" | "manual" | "adaptation";

export type StyleWeights = Record<Form, number>;

export type SurveyAnswer = { id: number; text: string };

export type SurveyQuestion = {
  id: number;
  text: string;
  answers: SurveyAnswer[];
};

export type SurveyChoice = { question_id: number; answer_id: number };

export type SurveyResult = {
  points: StyleWeights;
  dominant_style: LearningStyle;
  created_at: string;
};

export type StyleProposal = { style: Form; message: string; why: string };

export type LearningProfile = {
  survey_completed: boolean;
  style: LearningStyle | null;
  style_source: StyleSource | null;
  weights: StyleWeights | null;
  last_result: SurveyResult | null;
  explanation: string | null;
  proposal: StyleProposal | null;
};

export type PersonalizedBlocks = {
  blocks: Block[];
  /** null for teachers and admins (they see every block). */
  style: LearningStyle | null;
  /** Attachments without a form of the student's style, shown collapsed. */
  collapsed_block_ids: string[];
  /** Collapsed attachments the student has already opened in this lesson. */
  opened_block_ids: string[];
  explanation: string;
};

/** Sent by the quiz endpoint after `record_quiz_result` on the server. */
export type QuizFeedback = {
  passed: boolean;
  percent: number;
  weights: StyleWeights;
  weights_changed: boolean;
  why: string;
  proposal: StyleProposal | null;
};
