import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { coursesApi } from "./api";
import type { Course, CourseSummary } from "./types";

export const coursesKey = ["courses"] as const;
export const courseKey = (id: number) => [...coursesKey, id] as const;

export function useCourses() {
  return useQuery({ queryKey: coursesKey, queryFn: coursesApi.list });
}

export function useCourse(id: number) {
  return useQuery({
    queryKey: courseKey(id),
    queryFn: () => coursesApi.get(id),
  });
}

export function useSetPublished() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, isPublished }: { id: number; isPublished: boolean }) =>
      coursesApi.setPublished(id, isPublished),
    onSuccess: (updated) => {
      queryClient.setQueryData<CourseSummary[]>(coursesKey, (courses) =>
        courses?.map((course) => (course.id === updated.id ? updated : course)),
      );
      queryClient.setQueryData<Course>(courseKey(updated.id), (course) =>
        course ? { ...course, ...updated } : course,
      );
    },
  });
}
