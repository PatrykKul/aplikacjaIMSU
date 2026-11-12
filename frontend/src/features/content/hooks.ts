import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { contentApi } from "./api";
import type { Block, Form, LessonVersions } from "./types";

export const lessonVersionsKey = (lessonId: number) =>
  ["lessons", lessonId, "versions"] as const;

/** All three versions of a lesson (author and admin). */
export function useLessonVersions(lessonId: number, enabled = true) {
  return useQuery({
    queryKey: lessonVersionsKey(lessonId),
    queryFn: () => contentApi.versions(lessonId),
    enabled,
  });
}

/** Saves one version; the cached versions get the saved blocks. */
export function useSaveVersion(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ form, blocks }: { form: Form; blocks: Block[] }) =>
      contentApi.saveVersion(lessonId, form, blocks),
    onSuccess: (saved, { form }) => {
      queryClient.setQueryData<LessonVersions>(
        lessonVersionsKey(lessonId),
        (versions) => (versions ? { ...versions, [form]: saved } : versions),
      );
      return queryClient.invalidateQueries({
        queryKey: ["lessons", lessonId, "readiness"],
      });
    },
  });
}
