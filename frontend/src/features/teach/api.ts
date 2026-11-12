import type { Block, Form, UploadedFile } from "@/features/content/types";
import { api, uploadFile } from "@/shared/api/client";

import type {
  CourseCreateInput,
  CourseStats,
  CourseUpdateInput,
  Enrollment,
  EnrollmentStatus,
  LessonUpdateInput,
  LessonVersions,
  PoolQuestion,
  QuizPool,
  Readiness,
  TeacherCourse,
  TeacherCourseSummary,
  TeacherLesson,
} from "./types";

// --- curriculum ---

export const teachCoursesApi = {
  list: () => api.get<TeacherCourseSummary[]>("/courses"),
  get: (id: number) => api.get<TeacherCourse>(`/courses/${id}`),
  create: (data: CourseCreateInput) =>
    api.post<TeacherCourse>("/courses", data),
  update: (id: number, data: CourseUpdateInput) =>
    api.patch<TeacherCourse>(`/courses/${id}`, data),
  archive: (id: number) => api.delete(`/courses/${id}`),
  addLesson: (courseId: number, title: string) =>
    api.post<TeacherLesson>(`/courses/${courseId}/lessons`, { title }),
  reorderLessons: (courseId: number, lessonIds: number[]) =>
    api.put<TeacherCourse>(`/courses/${courseId}/lessons/order`, {
      lesson_ids: lessonIds,
    }),
};

export const teachLessonsApi = {
  get: (id: number) => api.get<TeacherLesson>(`/lessons/${id}`),
  update: (id: number, data: LessonUpdateInput) =>
    api.patch<TeacherLesson>(`/lessons/${id}`, data),
  archive: (id: number) => api.delete(`/lessons/${id}`),
};

// --- enrollments ---

export const enrollmentsApi = {
  list: (courseId: number, status?: EnrollmentStatus) =>
    api.get<Enrollment[]>(
      `/courses/${courseId}/enrollments${status ? `?status=${status}` : ""}`,
    ),
  decide: (courseId: number, studentId: number, accept: boolean) =>
    api.post(
      `/courses/${courseId}/enrollments/${studentId}/${accept ? "accept" : "reject"}`,
    ),
};

// --- content: the three versions of a lesson ---

export const versionsApi = {
  get: (lessonId: number) =>
    api.get<LessonVersions>(`/lessons/${lessonId}/versions`),
  save: (lessonId: number, form: Form, blocks: Block[]) =>
    api.put<{ blocks: Block[] }>(`/lessons/${lessonId}/versions/${form}`, {
      blocks,
    }),
  upload: (file: File, onProgress?: (fraction: number) => void) =>
    uploadFile<UploadedFile>("/files", file, onProgress),
};

// --- assessment: the question pool ---

export const poolApi = {
  get: (lessonId: number) =>
    api.get<QuizPool>(`/lessons/${lessonId}/quiz/edit`),
  save: (lessonId: number, questions: PoolQuestion[]) =>
    api.put<QuizPool>(`/lessons/${lessonId}/quiz`, { questions }),
  remove: (lessonId: number) => api.delete(`/lessons/${lessonId}/quiz`),
};

// --- authoring ---

export const authoringApi = {
  readiness: (lessonId: number) =>
    api.get<Readiness>(`/lessons/${lessonId}/readiness`),
  publish: (lessonId: number, isPublished: boolean) =>
    api.put<TeacherLesson>(`/lessons/${lessonId}/publication`, {
      is_published: isPublished,
    }),
};

// --- learning_style: statistics ---

export const statsApi = {
  course: (courseId: number) =>
    api.get<CourseStats>(`/courses/${courseId}/stats`),
};
