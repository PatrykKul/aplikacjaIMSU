import { journalLabel, journalText } from "@/features/learning-style/explain";

import { formatDateTime } from "../format";
import { cancelledTrials } from "../journal-data";
import type { JournalEntry } from "../types";

type DecisionJournalProps = {
  entries: JournalEntry[];
  /** false in the view of one course: only the lesson is named. */
  showCourse?: boolean;
};

function contextText(entry: JournalEntry, showCourse: boolean): string {
  const parts: string[] = [];
  if (showCourse && entry.course) {
    parts.push(entry.course.title);
  }
  if (entry.lesson) {
    parts.push(entry.lesson.title);
  }
  return parts.join(" · ");
}

/** Every decision of the system with its numbers, newest first (as the API sends them). */
export function DecisionJournal({
  entries,
  showCourse = true,
}: DecisionJournalProps) {
  if (entries.length === 0) {
    return (
      <p className="text-muted-foreground">Dziennik jest jeszcze pusty.</p>
    );
  }
  // R7a: a trial cancelled later says so in its own entry
  const context = { cancelledTrials: cancelledTrials(entries) };
  return (
    <ol role="list" className="divide-y border-y">
      {entries.map((entry) => {
        const where = contextText(entry, showCourse);
        return (
          <li
            key={entry.id}
            className="grid gap-1 py-3 sm:grid-cols-[11rem_minmax(0,1fr)] sm:gap-6"
          >
            <div className="text-sm text-muted-foreground">
              <time dateTime={entry.at} className="tabular-nums">
                {formatDateTime(entry.at)}
              </time>
              <span className="block text-xs font-medium tracking-wide uppercase">
                {journalLabel(entry)}
              </span>
            </div>
            <div className="space-y-0.5">
              <p className="text-pretty">{journalText(entry, context)}</p>
              {where && (
                <p className="text-sm text-muted-foreground">{where}</p>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
