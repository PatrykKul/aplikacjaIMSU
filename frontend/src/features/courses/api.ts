import { api } from "@/shared/api/client";

import type {
  Course,
  CourseCreateInput,
  CourseSummary,
  CourseUpdateInput,
  Enrollment,
  Lesson,
  LessonUpdateInput,
} from "./types";

export const coursesApi = {
  list: () => api.get<CourseSummary[]>("/courses"),
  get: (id: number) => api.get<Course>(`/courses/${id}`),
  create: (data: CourseCreateInput) => api.post<Course>("/courses", data),
  update: (id: number, data: CourseUpdateInput) =>
    api.patch<Course>(`/courses/${id}`, data),
  archive: (id: number) => api.delete(`/courses/${id}`),
  addLesson: (courseId: number, title: string) =>
    api.post<Lesson>(`/courses/${courseId}/lessons`, { title }),
  reorderLessons: (courseId: number, lessonIds: number[]) =>
    api.put<Course>(`/courses/${courseId}/lessons/order`, {
      lesson_ids: lessonIds,
    }),
  requestEnrollment: (courseId: number) =>
    api.post<Enrollment>(`/courses/${courseId}/enrollment`),
  /** Admin only: hand the course to another approved teacher. */
  changeOwner: (courseId: number, ownerId: number) =>
    api.put<Course>(`/courses/${courseId}/owner`, { owner_id: ownerId }),
};

export const lessonsApi = {
  get: (id: number) => api.get<Lesson>(`/lessons/${id}`),
  update: (id: number, data: LessonUpdateInput) =>
    api.patch<Lesson>(`/lessons/${id}`, data),
  archive: (id: number) => api.delete(`/lessons/${id}`),
};
