import type { JSONContent } from "@tiptap/react";

export type EnrollmentStatus = "pending" | "accepted" | "rejected";

/** R10: state of a lesson for an accepted student. */
export type LessonState = "passed" | "available" | "locked";

export type CourseSummary = {
  id: number;
  title: string;
  description: string;
  owner: { id: number; display_name: string };
  is_published: boolean;
  is_archived: boolean;
  /** Published lessons; for the author all lessons. */
  lesson_count: number;
  /** Student only; null = no request yet. */
  enrollment_status: EnrollmentStatus | null;
  /** Accepted student only. */
  progress: { passed: number; total: number } | null;
  /** Author only: number of enrollment requests. */
  pending_requests: number | null;
  updated_at: string;
};

export type CourseLesson = {
  id: number;
  title: string;
  /** 1, 2, … in the order of the course. */
  number: number;
  /** TipTap document; null until the teacher writes it. */
  outline: JSONContent | null;
  /** Author only. */
  is_published?: boolean | null;
  /** Accepted student only, otherwise null. */
  state: LessonState | null;
  /** When `state` is "locked". */
  required_lesson_number: number | null;
};

/** Kept for the teacher's screens (name from v2). */
export type LessonSummary = CourseLesson;

export type Course = CourseSummary & {
  introduction: JSONContent | null;
  /** "Podsumowanie i wnioski" of the course. */
  summary: JSONContent | null;
  lessons: CourseLesson[];
};

export type Lesson = {
  id: number;
  title: string;
  number: number;
  outline: JSONContent | null;
  conclusions: JSONContent | null;
  is_published: boolean;
  course: { id: number; title: string; owner_id: number };
  /** Neighbouring published lessons for a student. */
  previous_lesson_id: number | null;
  next_lesson_id: number | null;
  /** Student only. */
  next_lesson_unlocked?: boolean | null;
};

export type Enrollment = {
  course_id: number;
  status: EnrollmentStatus;
  requested_at: string;
  decided_at: string | null;
};

export type CourseCreateInput = { title: string; description: string };

export type CourseUpdateInput = {
  title?: string;
  description?: string;
  introduction?: JSONContent;
  summary?: JSONContent;
  is_published?: boolean;
};

export type LessonUpdateInput = {
  title?: string;
  outline?: JSONContent;
  conclusions?: JSONContent;
};

/** Limits shared with the backend (`curriculum/schemas.py`). */
export const TITLE_MAX = 120;
export const DESCRIPTION_MAX = 500;
