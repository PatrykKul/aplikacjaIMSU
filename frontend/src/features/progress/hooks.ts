import { useQuery } from "@tanstack/react-query";

import { progressApi } from "./api";

export const myProgressKey = ["me", "progress"] as const;
export const myJournalKey = ["me", "journal"] as const;

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
