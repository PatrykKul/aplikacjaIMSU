import { FORMS } from "@/features/content/types";
import { plural } from "@/shared/lib/plural";

import { FORM_BAR, STYLE_NAMES } from "../format";
import type { CourseStats } from "../types";
import { Bar, FormLabel } from "./FormLabel";

function studentsLabel(count: number): string {
  return `${count} ${plural(count, "uczeń", "uczniów", "uczniów")}`;
}

/** Active styles of the accepted students (V / A / K / without a style). */
export function StyleDistribution({
  styles,
}: {
  styles: CourseStats["styles"];
}) {
  const total = FORMS.reduce((sum, form) => sum + styles[form], styles.none);
  const share = (count: number) =>
    total === 0 ? 0 : Math.round((count / total) * 100);

  if (total === 0) {
    return (
      <p className="text-muted-foreground">
        Rozkład pojawi się, gdy na kurs zapiszą się uczniowie.
      </p>
    );
  }

  const rows = [
    ...FORMS.map((form) => ({
      key: form,
      label: <FormLabel form={form} name={STYLE_NAMES[form]} />,
      count: styles[form],
      bar: FORM_BAR[form],
    })),
    {
      key: "none",
      label: <span className="text-muted-foreground">bez stylu</span>,
      count: styles.none,
      bar: "bg-muted-foreground/40",
    },
  ];

  return (
    <dl className="grid max-w-2xl grid-cols-[max-content_1fr_max-content] items-center gap-x-4 gap-y-3">
      {rows.map((row) => (
        <div key={row.key} className="contents">
          <dt>{row.label}</dt>
          <dd>
            <Bar value={share(row.count)} className={row.bar} />
          </dd>
          <dd className="text-right tabular-nums">
            {studentsLabel(row.count)} ({share(row.count)}%)
          </dd>
        </div>
      ))}
    </dl>
  );
}
