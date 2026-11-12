import { api, uploadFile } from "@/shared/api/client";

import type {
  Block,
  Form,
  LessonBlocks,
  LessonVersions,
  UploadedFile,
} from "./types";

export const contentApi = {
  versions: (lessonId: number) =>
    api.get<LessonVersions>(`/lessons/${lessonId}/versions`),
  saveVersion: (lessonId: number, form: Form, blocks: Block[]) =>
    api.put<LessonBlocks>(`/lessons/${lessonId}/versions/${form}`, { blocks }),
  upload: (file: File, onProgress?: (fraction: number) => void) =>
    uploadFile<UploadedFile>("/files", file, onProgress),
};
