import { api } from "@/shared/api/client";

import type { JournalEntry, Progress } from "./types";

export const progressApi = {
  progress: () => api.get<Progress>("/me/progress"),
  journal: () => api.get<JournalEntry[]>("/me/journal"),
};
