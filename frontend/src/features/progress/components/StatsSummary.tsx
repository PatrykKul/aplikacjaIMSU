import { statsSummaryItems } from "@/features/learning-style/explain";
import { cn } from "@/shared/lib/utils";

import type { StatsSummary as StatsSummaryData } from "../types";

/** One row of 4 numbers with captions (two by two on a phone), no cards. */
export function StatsSummary({ summary }: { summary: StatsSummaryData }) {
  return (
    <dl className="grid grid-cols-2 gap-y-5 border-y py-5 sm:grid-cols-4">
      {statsSummaryItems(summary).map((item, index) => (
        <div
          key={item.label}
          className={cn(
            // Caption after the number on screen, before it for screen readers
            "flex flex-col-reverse justify-end gap-1",
            index % 2 === 1 && "border-l pl-4 sm:pl-6",
            index === 2 && "sm:border-l sm:pl-6",
          )}
        >
          <dt className="text-sm text-pretty text-muted-foreground">
            {item.label}
          </dt>
          <dd className="text-3xl font-semibold tabular-nums">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}
