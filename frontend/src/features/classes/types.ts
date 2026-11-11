import type { CourseSummary } from "@/features/courses/types";

export type ClassroomTeacher = {
  id: number;
  display_name: string;
  /** For students of the classroom, to contact the teacher. */
  email: string;
};

/** A student as a teacher sees them (search results, classroom members). */
export type StudentSummary = {
  id: number;
  display_name: string;
  email: string;
};

export type ClassroomSummary = {
  id: number;
  name: string;
  teacher: ClassroomTeacher;
  course_count: number;
  /** Only for the classroom teacher. */
  student_count: number | null;
};

export type Classroom = {
  id: number;
  name: string;
  teacher: ClassroomTeacher;
  /** The teacher sees archived courses too; students only active ones. */
  courses: CourseSummary[];
  /** Only for the classroom teacher: students do not see their classmates. */
  students: StudentSummary[] | null;
};

/** Limits shared with the backend (`curriculum/models.py`, `identity/schemas.py`). */
export const CLASSROOM_NAME_MAX = 80;
export const STUDENT_SEARCH_MIN = 3;
