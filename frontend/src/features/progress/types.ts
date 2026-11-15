import type { Form } from "@/features/content/types";
import type {
  Attention,
  FormTable,
  LearningProfile,
  LessonRef,
  Percentages,
  Praise,
  ProposalEvidence,
  ProposalKind,
  RetrySuggestion,
  TrialResult,
} from "@/features/learning-style/types";

export type { Percentages } from "@/features/learning-style/types";

/** State of the profile after one change (`style_history`). */
export type HistoryPoint = {
  at: string;
  percentages: Percentages;
  style: Form | null;
  /**
   * The journal event that added the point: survey_completed, tie_resolved,
   * quiz_attempt (counted), manual_style_change, proposal_accepted,
   * style_change_reverted; null for older points.
   */
  event: JournalEntry | null;
};

export type CourseProgress = {
  id: number;
  title: string;
  passed: number;
  total: number;
  next_lesson: LessonRef | null;
};

export type Attempt = {
  at: string;
  form: Form;
  percent: number;
  passed: boolean;
  /** The first attempt in this form in this lesson: it changed the percentages. */
  counted: boolean;
};

export type LessonProgress = {
  course_id: number;
  course_title: string;
  lesson_id: number;
  lesson_title: string;
  // null for a lesson unpublished or archived after the attempt
  number: number | null;
  passed: boolean;
  attempts: Attempt[];
};

export type Progress = {
  history: HistoryPoint[];
  courses: CourseProgress[];
  lessons: LessonProgress[];
};

// --- Decision journal: `data` of each event type (specification, "Dziennik decyzji") ---

export type ClearedLesson = {
  lesson_id: number;
  lesson_title: string;
  form: Form;
};

export type JournalEvent =
  | {
      type: "survey_completed";
      data: {
        points: Percentages;
        percentages: Percentages;
        style: Form | null;
        tie_styles: Form[];
      };
    }
  | { type: "tie_resolved"; data: { style: Form; tie_styles: Form[] } }
  | {
      type: "quiz_attempt";
      data: {
        draw_id: number;
        form: Form;
        percent: number;
        passed: boolean;
        counted: boolean;
        percentages_before: Percentages;
        percentages_after: Percentages;
        unlocked_lesson: LessonRef | null;
      };
    }
  | { type: "retry_suggestion"; data: RetrySuggestion }
  | {
      type: "lesson_form_changed";
      data: { from: Form; to: Form; source: "manual" | "suggestion" };
    }
  | {
      type: "proposal_created";
      data: {
        proposal_id: number;
        kind: ProposalKind;
        from: Form;
        to: Form;
        evidence: ProposalEvidence;
      };
    }
  | {
      type: "proposal_accepted";
      data: {
        proposal_id: number;
        kind: ProposalKind;
        from: Form;
        to: Form;
        cleared_lessons: ClearedLesson[];
      };
    }
  | {
      type: "proposal_rejected" | "proposal_expired";
      data: { proposal_id: number; kind: ProposalKind; from: Form; to: Form };
    }
  | {
      type: "manual_style_change";
      data: {
        from: Form;
        to: Form;
        cleared_lessons: ClearedLesson[];
        superseded_proposal_id?: number | null;
      };
    }
  | {
      /**
       * R7a (D60): back to `to` (the starting style of the trial) before any
       * lesson in `from`; the trial `trial_id` is cancelled.
       */
      type: "style_change_reverted";
      data: {
        from: Form;
        to: Form;
        trial_id: number;
        source: "manual" | "proposal";
        cleared_lessons: ClearedLesson[];
      };
    }
  | {
      type: "trial_started";
      data: {
        trial_id: number;
        from: Form;
        to: Form;
        source: "proposal" | "manual";
        before_average: number | null;
        /** D60: a third style replaced a trial without lessons; the baseline stays. */
        replaced_trial_id?: number | null;
      };
    }
  | { type: "praise"; data: Praise }
  /** R12: written once per series, when it reaches 3 failed counted results. */
  | { type: "attention_needed"; data: Attention }
  | {
      type: "trial_finished";
      data: {
        trial_id: number;
        from: Form;
        to: Form;
        before_average: number | null;
        after_average: number | null;
        result: TrialResult;
      };
    };

export type JournalEventType = JournalEvent["type"];

export type JournalEntry = JournalEvent & {
  id: number;
  at: string;
  course: { id: number; title: string } | null;
  /** `number` only if the server sends it; the chart falls back to a lookup. */
  lesson: { id: number; title: string; number?: number | null } | null;
};

/** `GET /courses/{id}/students/{student_id}` - the teacher's view of one student. */
export type StudentDetail = {
  student: { id: number; display_name: string; email: string };
  profile: LearningProfile;
  history: HistoryPoint[];
  lessons: LessonProgress[];
  journal: JournalEntry[];
  /** Table of forms over all courses of the student (as in `/me/stats`). */
  forms: FormTable;
  attention: Attention | null;
};

// --- Stage 10: statistics of the student ---

export type StatsSummary = {
  /** Passed lessons in all courses. */
  passed_lessons: number;
  /** Submitted attempts (rows of `quiz_results`). */
  attempts: number;
  /** Average of the counted results; null without them. */
  average: number | null;
  counted: number;
  /** Passed counted results in a row, from the newest back. */
  streak: number;
};

/** `GET /me/stats` */
export type StudentStats = {
  summary: StatsSummary;
  forms: FormTable;
  attention: Attention | null;
};

export type ReviewAnswer = { id: string; text: string };

/** `GET /me/review-questions`: answered wrong in the last submitted set of a lesson. */
export type ReviewQuestion = {
  course_id: number;
  course_title: string;
  lesson_id: number;
  lesson_title: string;
  // null for a lesson unpublished after the attempt
  number: number | null;
  question_id: string;
  text: string;
  chosen_answer: ReviewAnswer;
  correct_answer: ReviewAnswer;
  explanation: string;
  answered_at: string;
};
