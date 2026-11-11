import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import { classroomsApi, studentsApi } from "./api";
import { type Classroom, STUDENT_SEARCH_MIN } from "./types";

export const classroomsKey = ["classrooms"] as const;
export const classroomKey = (id: number) => [...classroomsKey, id] as const;

export function useClassrooms() {
  return useQuery({ queryKey: classroomsKey, queryFn: classroomsApi.list });
}

export function useClassroom(id: number) {
  return useQuery({
    queryKey: classroomKey(id),
    queryFn: () => classroomsApi.get(id),
  });
}

/** After a change: store the returned classroom and refetch the list only. */
function useStoreClassroom() {
  const queryClient = useQueryClient();
  return (classroom: Classroom) => {
    queryClient.setQueryData(classroomKey(classroom.id), classroom);
    return queryClient.invalidateQueries({
      queryKey: classroomsKey,
      exact: true,
    });
  };
}

export function useCreateClassroom() {
  const store = useStoreClassroom();
  return useMutation({ mutationFn: classroomsApi.create, onSuccess: store });
}

export function useRenameClassroom(id: number) {
  const store = useStoreClassroom();
  return useMutation({
    mutationFn: (name: string) => classroomsApi.rename(id, name),
    onSuccess: store,
  });
}

export function useDeleteClassroom(id: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => classroomsApi.remove(id),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: classroomKey(id) });
      return queryClient.invalidateQueries({
        queryKey: classroomsKey,
        exact: true,
      });
    },
  });
}

// --- Students and courses of a classroom (the list shows their counts) ---

function useRefreshClassrooms() {
  const queryClient = useQueryClient();
  // The prefix covers the classroom and the list with its counts
  return () => queryClient.invalidateQueries({ queryKey: classroomsKey });
}

export function useAddStudent(id: number) {
  const refresh = useRefreshClassrooms();
  return useMutation({
    mutationFn: (studentId: number) => classroomsApi.addStudent(id, studentId),
    onSuccess: refresh,
  });
}

export function useRemoveStudent(id: number) {
  const refresh = useRefreshClassrooms();
  return useMutation({
    mutationFn: (studentId: number) =>
      classroomsApi.removeStudent(id, studentId),
    onSuccess: refresh,
  });
}

export function useAssignCourse(id: number) {
  const refresh = useRefreshClassrooms();
  return useMutation({
    mutationFn: (courseId: number) => classroomsApi.assignCourse(id, courseId),
    onSuccess: refresh,
  });
}

export function useUnassignCourse(id: number) {
  const refresh = useRefreshClassrooms();
  return useMutation({
    mutationFn: (courseId: number) =>
      classroomsApi.unassignCourse(id, courseId),
    onSuccess: refresh,
  });
}

/**
 * Students whose e-mail contains `email` (already debounced by the caller).
 * Each text is cached; the previous results stay on screen while new ones load,
 * and a request for text the user has already changed is cancelled.
 */
export function useStudentSearch(email: string) {
  return useQuery({
    queryKey: ["students", "search", email],
    queryFn: ({ signal }) => studentsApi.search(email, signal),
    enabled: email.length >= STUDENT_SEARCH_MIN,
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}
