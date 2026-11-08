import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { contentApi } from "./api";
import type { Block } from "./types";

export const lessonBlocksKey = (lessonId: number) =>
  ["lessons", lessonId, "blocks"] as const;

export function useLessonBlocks(lessonId: number) {
  return useQuery({
    queryKey: lessonBlocksKey(lessonId),
    queryFn: () => contentApi.getBlocks(lessonId),
  });
}

export function useSaveBlocks(lessonId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (blocks: Block[]) => contentApi.saveBlocks(lessonId, blocks),
    onSuccess: (saved) =>
      queryClient.setQueryData(lessonBlocksKey(lessonId), saved),
  });
}
