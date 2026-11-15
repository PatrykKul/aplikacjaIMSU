import { api } from "@/shared/api/client";

import type {
  JournalEntry,
  Progress,
  ReviewQuestion,
  StudentStats,
} from "./types";

export const progressApi = {
  progress: () => api.get<Progress>("/me/progress"),
  journal: () => api.get<JournalEntry[]>("/me/journal"),
  stats: () => api.get<StudentStats>("/me/stats"),
  reviewQuestions: () => api.get<ReviewQuestion[]>("/me/review-questions"),
};
