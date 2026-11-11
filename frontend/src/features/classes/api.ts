import { api } from "@/shared/api/client";

import type { Classroom, ClassroomSummary, StudentSummary } from "./types";

export const classroomsApi = {
  list: () => api.get<ClassroomSummary[]>("/classrooms"),
  get: (id: number) => api.get<Classroom>(`/classrooms/${id}`),
  create: (name: string) => api.post<Classroom>("/classrooms", { name }),
  rename: (id: number, name: string) =>
    api.patch<Classroom>(`/classrooms/${id}`, { name }),
  remove: (id: number) => api.delete(`/classrooms/${id}`),
  addStudent: (id: number, studentId: number) =>
    api.put<void>(`/classrooms/${id}/students/${studentId}`),
  removeStudent: (id: number, studentId: number) =>
    api.delete(`/classrooms/${id}/students/${studentId}`),
  assignCourse: (id: number, courseId: number) =>
    api.put<void>(`/classrooms/${id}/courses/${courseId}`),
  unassignCourse: (id: number, courseId: number) =>
    api.delete(`/classrooms/${id}/courses/${courseId}`),
};

export const studentsApi = {
  search: (email: string, signal?: AbortSignal) =>
    api.get<StudentSummary[]>(
      `/students?email=${encodeURIComponent(email)}`,
      signal,
    ),
};
