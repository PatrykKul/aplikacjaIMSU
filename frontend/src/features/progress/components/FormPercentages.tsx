import { FORMS } from "@/features/content/types";
import { formLabel, formStatsText } from "@/features/learning-style/explain";
import { FORM_BAR } from "@/features/learning-style/form-tones";
import type { LearningProfile } from "@/features/learning-style/types";
import { cn } from "@/shared/lib/utils";

/**
 * Percent of each form with a bar and where it comes from (R3):
 * "potwierdzona wynikami (2 lekcje, średnio 88%)" or "tylko z ankiety".
 */
export function FormPercentages({ profile }: { profile: LearningProfile }) {
  const { percentages, forms, style } = profile;
  if (!percentages) {
    return (
      <p className="text-muted-foreground">
        Procenty pojawią się po wypełnieniu ankiety.
      </p>
    );
  }
  return (
    <dl className="divide-y border-y">
      {FORMS.map((form) => (
        <div
          key={form}
          className="grid grid-cols-[minmax(0,1fr)_3.5rem] items-center gap-x-4 gap-y-1.5 py-3 sm:grid-cols-[11rem_minmax(0,1fr)_3.5rem]"
        >
          <dt className="font-medium">
            {formLabel(form)}
            {form === style && (
              <span className="ml-2 text-sm font-normal text-muted-foreground">
                aktywny styl
              </span>
            )}
          </dt>
          <dd className="order-last col-span-2 h-2 overflow-hidden rounded-full bg-muted sm:order-none sm:col-span-1">
            <div
              className={cn("h-full rounded-full", FORM_BAR[form])}
              style={{ width: `${percentages[form]}%` }}
            />
          </dd>
          <dd className="text-right text-lg font-semibold tabular-nums">
            {percentages[form]}%
          </dd>
          <dd className="order-last col-span-2 text-sm text-muted-foreground sm:col-span-3 sm:col-start-1">
            {formStatsText(forms?.[form])}
          </dd>
        </div>
      ))}
    </dl>
  );
}
