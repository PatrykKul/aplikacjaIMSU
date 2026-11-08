import { api, uploadFile } from "@/shared/api/client";

import type { Block, LessonBlocks, UploadedFile } from "./types";

export const contentApi = {
  getBlocks: (lessonId: number) =>
    api.get<LessonBlocks>(`/lessons/${lessonId}/blocks`),
  saveBlocks: (lessonId: number, blocks: Block[]) =>
    api.put<LessonBlocks>(`/lessons/${lessonId}/blocks`, { blocks }),
  upload: (file: File, onProgress?: (fraction: number) => void) =>
    uploadFile<UploadedFile>("/files", file, onProgress),
};
