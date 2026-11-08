import { api } from "@/shared/api/client";

import type {
  Course,
  CourseCreateInput,
  CourseSummary,
  CourseUpdateInput,
  Lesson,
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
};

export const lessonsApi = {
  get: (id: number) => api.get<Lesson>(`/lessons/${id}`),
  rename: (id: number, title: string) =>
    api.patch<Lesson>(`/lessons/${id}`, { title }),
  archive: (id: number) => api.delete(`/lessons/${id}`),
};
