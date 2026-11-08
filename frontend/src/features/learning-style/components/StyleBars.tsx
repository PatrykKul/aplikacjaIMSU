import { FORMS } from "@/features/content/types";

import { STYLE_NAMES } from "../styles";
import type { StyleWeights } from "../types";

type StyleBarsProps = {
  values: StyleWeights;
  /** Value of a full bar (survey: number of questions; weights: 30). */
  max: number;
  label: string;
};

/** Three horizontal bars for V, A and K with their numbers. */
export function StyleBars({ values, max, label }: StyleBarsProps) {
  return (
    <dl aria-label={label} className="space-y-3">
      {FORMS.map((form) => {
        const value = values[form];
        const width = max > 0 ? Math.round((value / max) * 100) : 0;
        return (
          <div key={form} className="grid grid-cols-[7.5rem_1fr_2rem] items-center gap-3">
            <dt className="text-sm">
              <span className="font-semibold">{form}</span> · {STYLE_NAMES[form]}
            </dt>
            <dd className="h-2.5 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary transition-[width]"
                style={{ width: `${width}%` }}
              />
            </dd>
            <dd className="text-right text-sm tabular-nums">{value}</dd>
          </div>
        );
      })}
    </dl>
  );
}
