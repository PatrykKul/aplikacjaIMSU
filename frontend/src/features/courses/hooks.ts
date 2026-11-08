import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { coursesApi, lessonsApi } from "./api";
import type { Course, CourseUpdateInput } from "./types";

export const coursesKey = ["courses"] as const;
export const courseKey = (id: number) => [...coursesKey, id] as const;
export const lessonKey = (id: number) => ["lessons", id] as const;

export function useCourses() {
  return useQuery({ queryKey: coursesKey, queryFn: coursesApi.list });
}

export function useCourse(id: number) {
  return useQuery({
    queryKey: courseKey(id),
    queryFn: () => coursesApi.get(id),
  });
}

/** After a change: store the returned course and refetch the list only. */
function useStoreCourse() {
  const queryClient = useQueryClient();
  return (course: Course) => {
    queryClient.setQueryData(courseKey(course.id), course);
    return queryClient.invalidateQueries({ queryKey: coursesKey, exact: true });
  };
}

export function useCreateCourse() {
  const store = useStoreCourse();
  return useMutation({ mutationFn: coursesApi.create, onSuccess: store });
}

export function useUpdateCourse(id: number) {
  const store = useStoreCourse();
  return useMutation({
    mutationFn: (data: CourseUpdateInput) => coursesApi.update(id, data),
    onSuccess: store,
  });
}

export function useArchiveCourse(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => coursesApi.archive(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: courseKey(id) });
      return queryClient.invalidateQueries({
        queryKey: coursesKey,
        exact: true,
      });
    },
  });
}

// --- Lessons of a course (the course page shows their titles and order) ---

function useRefreshCourse(courseId: number) {
  const queryClient = useQueryClient();
  return () => queryClient.invalidateQueries({ queryKey: courseKey(courseId) });
}

export function useAddLesson(courseId: number) {
  const refresh = useRefreshCourse(courseId);
  return useMutation({
    mutationFn: (title: string) => coursesApi.addLesson(courseId, title),
    onSuccess: refresh,
  });
}

export function useReorderLessons(courseId: number) {
  const store = useStoreCourse();
  return useMutation({
    mutationFn: (lessonIds: number[]) =>
      coursesApi.reorderLessons(courseId, lessonIds),
    onSuccess: store,
  });
}

export function useRenameLesson(courseId: number) {
  const refresh = useRefreshCourse(courseId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) =>
      lessonsApi.rename(id, title),
    onSuccess: (lesson) => {
      queryClient.setQueryData(lessonKey(lesson.id), lesson);
      return refresh();
    },
  });
}

export function useArchiveLesson(courseId: number) {
  const refresh = useRefreshCourse(courseId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => lessonsApi.archive(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: lessonKey(id) });
      return refresh();
    },
  });
}
