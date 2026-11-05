import { api } from "@/shared/api/client";

import type { Course, CourseSummary } from "./types";

export const coursesApi = {
  list: () => api.get<CourseSummary[]>("/courses"),
  get: (id: number) => api.get<Course>(`/courses/${id}`),
  setPublished: (id: number, isPublished: boolean) =>
    api.patch<CourseSummary>(`/courses/${id}`, { is_published: isPublished }),
};
