import {
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import type { Block, Form } from "@/features/content/types";

import {
  authoringApi,
  enrollmentsApi,
  poolApi,
  statsApi,
  teachCoursesApi,
  teachLessonsApi,
  versionsApi,
} from "./api";
import type {
  CourseUpdateInput,
  LessonUpdateInput,
  LessonVersions,
  PoolQuestion,
  TeacherCourse,
  TeacherLesson,
} from "./types";

// Query keys (docs/08-praca-biezaca.md, "Klucze TanStack Query")
export const coursesKey = ["courses"] as const;
export const courseKey = (id: number) => ["courses", id] as const;
export const enrollmentsKey = (id: number) =>
  ["courses", id, "enrollments"] as const;
export const courseStatsKey = (id: number) => ["courses", id, "stats"] as const;
export const courseStudentKey = (id: number, studentId: number) =>
  ["courses", id, "students", studentId] as const;
export const lessonKey = (id: number) => ["lessons", id] as const;
export const versionsKey = (id: number) => ["lessons", id, "versions"] as const;
export const poolKey = (id: number) => ["lessons", id, "quiz-edit"] as const;
export const readinessKey = (id: number) =>
  ["lessons", id, "readiness"] as const;

// --- courses ---

export function useTeacherCourses() {
  return useQuery({ queryKey: coursesKey, queryFn: teachCoursesApi.list });
}

export function useTeacherCourse(id: number) {
  return useQuery({
    queryKey: courseKey(id),
    queryFn: () => teachCoursesApi.get(id),
  });
}

/** Details of several courses at once (the "Moje kursy" cards count published lessons). */
export function useTeacherCourseDetails(ids: number[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: courseKey(id),
      queryFn: () => teachCoursesApi.get(id),
    })),
  });
}

/** After a change: store the returned course and refetch the list only. */
function useStoreCourse() {
  const queryClient = useQueryClient();
  return (course: TeacherCourse) => {
    queryClient.setQueryData(courseKey(course.id), course);
    return queryClient.invalidateQueries({ queryKey: coursesKey, exact: true });
  };
}

function useRefreshCourse(courseId: number) {
  const queryClient = useQueryClient();
  return () =>
    Promise.all([
      queryClient.invalidateQueries({
        queryKey: courseKey(courseId),
        exact: true,
      }),
      queryClient.invalidateQueries({ queryKey: coursesKey, exact: true }),
    ]);
}

export function useCreateCourse() {
  const store = useStoreCourse();
  return useMutation({ mutationFn: teachCoursesApi.create, onSuccess: store });
}

export function useUpdateCourse(id: number) {
  const store = useStoreCourse();
  return useMutation({
    mutationFn: (data: CourseUpdateInput) => teachCoursesApi.update(id, data),
    onSuccess: store,
  });
}

export function useArchiveCourse(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => teachCoursesApi.archive(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: courseKey(id) });
      return queryClient.invalidateQueries({
        queryKey: coursesKey,
        exact: true,
      });
    },
  });
}

// --- lessons of a course ---

export function useAddLesson(courseId: number) {
  const refresh = useRefreshCourse(courseId);
  return useMutation({
    mutationFn: (title: string) => teachCoursesApi.addLesson(courseId, title),
    onSuccess: refresh,
  });
}

export function useReorderLessons(courseId: number) {
  const store = useStoreCourse();
  return useMutation({
    mutationFn: (lessonIds: number[]) =>
      teachCoursesApi.reorderLessons(courseId, lessonIds),
    onSuccess: store,
  });
}

export function useArchiveLesson(courseId: number) {
  const refresh = useRefreshCourse(courseId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => teachLessonsApi.archive(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: lessonKey(id) });
      return refresh();
    },
  });
}

// --- one lesson ---

export function useTeacherLesson(id: number) {
  return useQuery({
    queryKey: lessonKey(id),
    queryFn: () => teachLessonsApi.get(id),
  });
}

/** Stores the returned lesson; course list, course and readiness are refetched. */
function useStoreLesson() {
  const queryClient = useQueryClient();
  return (lesson: TeacherLesson) => {
    queryClient.setQueryData(lessonKey(lesson.id), lesson);
    return Promise.all([
      queryClient.invalidateQueries({ queryKey: readinessKey(lesson.id) }),
      queryClient.invalidateQueries({
        queryKey: courseKey(lesson.course.id),
        exact: true,
      }),
      queryClient.invalidateQueries({ queryKey: coursesKey, exact: true }),
    ]);
  };
}

export function useUpdateLesson(id: number) {
  const store = useStoreLesson();
  return useMutation({
    mutationFn: (data: LessonUpdateInput) => teachLessonsApi.update(id, data),
    onSuccess: store,
  });
}

/** Rename from the course page: the lesson id comes with the call. */
export function useRenameLesson() {
  const store = useStoreLesson();
  return useMutation({
    mutationFn: ({ id, title }: { id: number; title: string }) =>
      teachLessonsApi.update(id, { title }),
    onSuccess: store,
  });
}

export function useLessonReadiness(id: number) {
  return useQuery({
    queryKey: readinessKey(id),
    queryFn: () => authoringApi.readiness(id),
  });
}

/** Readiness of every lesson of a course (the lesson list shows what is missing). */
export function useLessonsReadiness(ids: number[]) {
  return useQueries({
    queries: ids.map((id) => ({
      queryKey: readinessKey(id),
      queryFn: () => authoringApi.readiness(id),
    })),
  });
}

export function usePublishLesson(id: number) {
  const store = useStoreLesson();
  return useMutation({
    mutationFn: (isPublished: boolean) => authoringApi.publish(id, isPublished),
    onSuccess: store,
  });
}

// --- versions V / A / K ---

export function useLessonVersions(lessonId: number) {
  return useQuery({
    queryKey: versionsKey(lessonId),
    queryFn: () => versionsApi.get(lessonId),
  });
}

export function useSaveVersion(lessonId: number, form: Form) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (blocks: Block[]) => versionsApi.save(lessonId, form, blocks),
    onSuccess: (saved) => {
      queryClient.setQueryData<LessonVersions>(
        versionsKey(lessonId),
        (current) => current && { ...current, [form]: saved },
      );
      return queryClient.invalidateQueries({
        queryKey: readinessKey(lessonId),
      });
    },
  });
}

// --- question pool ---

export function useQuestionPool(lessonId: number) {
  return useQuery({
    queryKey: poolKey(lessonId),
    queryFn: () => poolApi.get(lessonId),
  });
}

/** Saves the pool; an empty pool deletes the quiz (the API needs 1–50 questions). */
export function useSavePool(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (questions: PoolQuestion[]) => {
      if (questions.length === 0) {
        await poolApi.remove(lessonId);
        return { questions: [] };
      }
      return poolApi.save(lessonId, questions);
    },
    onSuccess: (saved) => {
      queryClient.setQueryData(poolKey(lessonId), saved);
      return queryClient.invalidateQueries({
        queryKey: readinessKey(lessonId),
      });
    },
  });
}

// --- course panel ---

export function useEnrollments(courseId: number) {
  return useQuery({
    queryKey: enrollmentsKey(courseId),
    queryFn: () => enrollmentsApi.list(courseId),
  });
}

export function useDecideEnrollment(courseId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      studentId,
      accept,
    }: {
      studentId: number;
      accept: boolean;
    }) => enrollmentsApi.decide(courseId, studentId, accept),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: enrollmentsKey(courseId) }),
        queryClient.invalidateQueries({ queryKey: courseStatsKey(courseId) }),
        queryClient.invalidateQueries({ queryKey: coursesKey, exact: true }),
      ]),
  });
}

export function useCourseStats(courseId: number) {
  return useQuery({
    queryKey: courseStatsKey(courseId),
    queryFn: () => statsApi.course(courseId),
  });
}

export function useCourseStudent(courseId: number, studentId: number) {
  return useQuery({
    queryKey: courseStudentKey(courseId, studentId),
    queryFn: () => statsApi.student(courseId, studentId),
  });
}
