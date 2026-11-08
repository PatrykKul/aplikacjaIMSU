import type { JSONContent } from "@tiptap/react";

export type CourseSummary = {
  id: number;
  owner_id: number;
  title: string;
  description: string;
  is_published: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
};

export type LessonSummary = { id: number; title: string };

export type Course = CourseSummary & {
  /** TipTap document; null until the teacher writes an introduction. */
  introduction: JSONContent | null;
  lessons: LessonSummary[];
};

export type Lesson = {
  id: number;
  title: string;
  course: { id: number; title: string; owner_id: number };
  previous_lesson_id: number | null;
  next_lesson_id: number | null;
};

export type CourseCreateInput = { title: string; description: string };

export type CourseUpdateInput = {
  title?: string;
  description?: string;
  introduction?: JSONContent;
  is_published?: boolean;
};

/** Limits shared with the backend (`curriculum/schemas.py`). */
export const TITLE_MAX = 120;
export const DESCRIPTION_MAX = 500;
