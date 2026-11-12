import { FlaskConicalIcon } from "lucide-react";

import { inForm, styleName, trialRuleText, trialStatusText } from "../explain";
import type { Trial } from "../types";

/** R7: the running trial ("1 z 2 lekcji w nowej formie") or its result. */
export function TrialNote({
  trial,
  showRule = false,
}: {
  trial: Trial;
  showRule?: boolean;
}) {
  const finished = trial.result !== null;
  return (
    <div className="flex gap-3 border-l-2 border-primary py-1 pl-4">
      <FlaskConicalIcon
        aria-hidden="true"
        className="mt-0.5 size-5 shrink-0 text-primary"
      />
      <div className="space-y-1">
        <p className="font-medium">
          {finished
            ? `Wynik okresu próbnego: styl ${styleName(trial.to)}`
            : `Okres próbny: nauka ${inForm(trial.to)}`}
        </p>
        <p className="tabular-nums">{trialStatusText(trial)}</p>
        {showRule && !finished && (
          <p className="text-sm text-muted-foreground">{trialRuleText()}</p>
        )}
      </div>
    </div>
  );
}
