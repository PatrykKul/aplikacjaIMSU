import { FORMS } from "@/features/content/types";
import { cn } from "@/shared/lib/utils";

import { formLabel } from "../explain";
import { FORM_BAR } from "../form-tones";
import type { Percentages } from "../types";

type StyleBarsProps = {
  values: Percentages;
  /** Value of a full bar (100 for percentages). */
  max?: number;
  label: string;
  unit?: string;
};

/** Three horizontal bars for V, A and K with their numbers. */
export function StyleBars({
  values,
  max = 100,
  label,
  unit = "%",
}: StyleBarsProps) {
  return (
    <dl aria-label={label} className="space-y-3">
      {FORMS.map((form) => {
        const value = values[form];
        const width = max > 0 ? Math.round((value / max) * 100) : 0;
        return (
          <div
            key={form}
            className="grid grid-cols-[9.5rem_minmax(0,1fr)_3rem] items-center gap-3"
          >
            <dt className="text-sm">{formLabel(form)}</dt>
            <dd className="h-2.5 overflow-hidden rounded-full bg-muted">
              <div
                className={cn(
                  "h-full rounded-full transition-[width]",
                  FORM_BAR[form],
                )}
                style={{ width: `${width}%` }}
              />
            </dd>
            <dd className="text-right text-sm font-medium tabular-nums">
              {value}
              {unit}
            </dd>
          </div>
        );
      })}
    </dl>
  );
}
