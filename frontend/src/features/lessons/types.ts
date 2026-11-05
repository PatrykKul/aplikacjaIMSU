export type LessonMethod = "common" | "alpha" | "beta" | "gamma" | "delta";

export type LessonSummary = {
  id: number;
  method: LessonMethod;
  title: string;
  step_count: number;
};

export type TextStep = { type: "text"; key: string; body: string };

export type NumberAnswer = { type: "number"; unit: string | null };
export type ChoiceAnswer = { type: "choice"; options: string[] };

export type QuestionStep = {
  type: "question";
  key: string;
  prompt: string;
  hint: string | null;
  answer: NumberAnswer | ChoiceAnswer;
};

export type LessonStep = TextStep | QuestionStep;

export type Lesson = {
  id: number;
  skill_id: number;
  method: LessonMethod;
  title: string;
  steps: LessonStep[];
};

// Text for number questions, option index for choice questions
export type AnswerValue = string | number;

export type CheckResult = {
  correct: boolean;
  feedback: string | null;
  explanation: string | null;
  correct_answer: string | null;
};
