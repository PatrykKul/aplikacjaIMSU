import { FORMS } from "@/features/content/types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { FORM_BAR, FORM_NAMES, formatPercent } from "../format";
import type { CourseStats } from "../types";
import { Bar, FormLabel } from "./FormLabel";

/** Which form works in this course: averages of counted results per form. */
export function FormEffectiveness({ forms }: { forms: CourseStats["forms"] }) {
  const hasData = FORMS.some((form) => forms[form].counted_results > 0);

  return (
    <div className="space-y-3">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Forma</TableHead>
            <TableHead className="w-1/3">Średnia wyników</TableHead>
            <TableHead className="text-right">Wyniki</TableHead>
            <TableHead className="text-right">Podejścia</TableHead>
            <TableHead className="text-right">Uczniowie</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {FORMS.map((form) => {
            const stats = forms[form];
            return (
              <TableRow key={form}>
                <TableCell>
                  <FormLabel form={form} name={FORM_NAMES[form]} />
                </TableCell>
                <TableCell>
                  <span className="flex items-center gap-3">
                    <Bar
                      value={stats.average ?? 0}
                      className={FORM_BAR[form]}
                    />
                    <span className="w-10 shrink-0 text-right font-medium tabular-nums">
                      {formatPercent(stats.average)}
                    </span>
                  </span>
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {stats.counted_results}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {stats.attempts}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {stats.students}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <p className="max-w-[65ch] text-sm text-muted-foreground">
        {hasData
          ? "Średnia liczy tylko wyniki policzone – pierwsze podejście ucznia w danej formie w danej lekcji. Podejścia to wszystkie rozwiązane quizy, także powtórki."
          : "Brak wyników: uczniowie nie rozwiązali jeszcze żadnego quizu w tym kursie."}
      </p>
    </div>
  );
}
