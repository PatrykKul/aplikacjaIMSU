/**
 * Pure helpers over the decision journal (type-only imports, tested by
 * `journal-data.test.mjs`); the Polish words come from `learning-style/explain.ts`.
 */
import type { JournalEntry } from "./types";

/**
 * R7a (D60): why a trial ended before its first lesson. `reverted` - the
 * change of the style was undone; `replaced` - a third style started a new trial.
 */
export type TrialCancel = "reverted" | "replaced";

/**
 * Trials cancelled later in the journal, by `trial_id`: named in
 * `style_change_reverted.data.trial_id` or in a later
 * `trial_started.data.replaced_trial_id`. The order of entries does not matter.
 */
export function cancelledTrials(
  entries: JournalEntry[],
): Map<number, TrialCancel> {
  const cancelled = new Map<number, TrialCancel>();
  for (const entry of entries) {
    if (entry.type === "style_change_reverted") {
      cancelled.set(entry.data.trial_id, "reverted");
    } else if (
      entry.type === "trial_started" &&
      typeof entry.data.replaced_trial_id === "number" &&
      !cancelled.has(entry.data.replaced_trial_id)
    ) {
      cancelled.set(entry.data.replaced_trial_id, "replaced");
    }
  }
  return cancelled;
}
