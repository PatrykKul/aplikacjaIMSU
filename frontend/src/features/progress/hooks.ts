import { useQuery } from "@tanstack/react-query";

import { progressApi } from "./api";

// Under ["me"]: a quiz result and every change of the profile refresh them
export const myProgressKey = ["me", "progress"] as const;
export const myJournalKey = ["me", "journal"] as const;
export const myStatsKey = ["me", "stats"] as const;
export const myReviewQuestionsKey = ["me", "review-questions"] as const;

export function useMyProgress(enabled = true) {
  return useQuery({
    queryKey: myProgressKey,
    queryFn: progressApi.progress,
    enabled,
  });
}

export function useMyJournal() {
  return useQuery({ queryKey: myJournalKey, queryFn: progressApi.journal });
}

/** Summary, table of forms and R12 of "Moje postępy". */
export function useMyStats() {
  return useQuery({ queryKey: myStatsKey, queryFn: progressApi.stats });
}

/** "Do powtórki": at most 5 questions, newest first. */
export function useMyReviewQuestions() {
  return useQuery({
    queryKey: myReviewQuestionsKey,
    queryFn: progressApi.reviewQuestions,
  });
}
