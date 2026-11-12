import type { Block, Form } from "@/features/content/types";

/** Profile of a student: percent of each form, sum 100, each 5-90. */
export type Percentages = Record<Form, number>;

export type StyleSource = "survey" | "tie_choice" | "manual" | "proposal";

export type SurveyAnswer = { id: number; text: string };

export type SurveyQuestion = {
  id: number;
  text: string;
  answers: SurveyAnswer[];
};

export type SurveyChoice = { question_id: number; answer_id: number };

export type SurveyResult = {
  points: Percentages;
  percentages: Percentages;
  created_at: string;
};

/** R3: results of a form over all courses (counted results only). */
export type FormStats = {
  /** At least one passed attempt in this form (also a repeated one). */
  confirmed: boolean;
  lessons: number;
  average: number | null;
};

export type ProposalKind = "switch" | "revert";

export type FormEvidence = {
  form: Form;
  lessons: number;
  average: number | null;
  percent: number;
};

/**
 * R6: `from` / `to` with the numbers of both forms. A revert proposal (R7)
 * may carry the averages of the trial instead.
 */
export type ProposalEvidence = {
  from?: FormEvidence;
  to?: FormEvidence;
  before_average?: number | null;
  after_average?: number | null;
};

export type Proposal = {
  id: number;
  kind: ProposalKind;
  from: Form;
  to: Form;
  evidence: ProposalEvidence;
  created_at: string;
};

export type TrialResult = "helped" | "neutral" | "worse" | "no_baseline";

export type Trial = {
  id: number;
  from: Form;
  to: Form;
  source: "proposal" | "manual";
  before_average: number | null;
  after_average: number | null;
  /** null until the trial ends. */
  result: TrialResult | null;
  /** Counted results in the new style so far. */
  done: number;
  needed: number;
  started_at: string;
  finished_at: string | null;
};

export type LearningProfile = {
  survey_completed: boolean;
  /** null before the survey and while a tie is not resolved. */
  style: Form | null;
  style_source: StyleSource | null;
  /** Non-empty only while a tie of the survey is not resolved. */
  tie_styles: Form[];
  percentages: Percentages | null;
  forms: Record<Form, FormStats> | null;
  survey: SurveyResult | null;
  open_proposal: Proposal | null;
  /** The running trial or the last finished one. */
  trial: Trial | null;
};

export type LessonRef = { id: number; title: string; number: number };

export type LessonScore = {
  lesson_id: number;
  lesson_title: string;
  percent: number;
};

/** R5: the same shape as `data` of the journal event `retry_suggestion`. */
export type RetrySuggestion = {
  failed: { form: Form; percent: number; previous: LessonScore | null };
  suggested: {
    form: Form;
    reason: "confirmed" | "survey";
    percent: number;
    survey_percent: number;
    best: LessonScore | null;
  };
};

export type Praise = { form: Form; streak: number; average: number };

/** What `record_quiz_result` decided after one quiz attempt. */
export type QuizFeedback = {
  form: Form;
  counted: boolean;
  percentages_before: Percentages;
  percentages_after: Percentages;
  passed: boolean;
  unlocked_lesson: LessonRef | null;
  course_completed: boolean;
  praise: Praise | null;
  suggestion: RetrySuggestion | null;
  proposal: Proposal | null;
  trial: Trial | null;
};

export type FormSource = "style" | "choice";

/** A lesson for a student: the version in one form (`GET /lessons/{id}/study`). */
export type Study = {
  lesson_id: number;
  form: Form;
  form_source: FormSource;
  style: Form | null;
  blocks: Block[];
  other_forms: Form[];
  suggestion: RetrySuggestion | null;
  last_result: { percent: number; passed: boolean; form: Form } | null;
};

/** R8: the best form of the course among other students. */
export type CourseHint = {
  form: Form;
  average: number;
  students: number;
  results: number;
};
