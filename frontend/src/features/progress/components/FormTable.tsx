import type { ReactNode } from "react";

import { FORMS, type Form } from "@/features/content/types";
import { FormMark } from "@/features/learning-style/components/FormMark";
import {
  activeStyleText,
  formStatusText,
  formTableConclusion,
  formLabel,
  lessonsText,
  tooFewText,
} from "@/features/learning-style/explain";
import { FORM_BAR } from "@/features/learning-style/form-tones";
import type {
  FormTable as FormTableData,
  FormTableRow,
} from "@/features/learning-style/types";
import { cn } from "@/shared/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

type FormTableProps = {
  forms: FormTableData;
  /** Active style: its row says "Twój styl" / "styl ucznia". */
  style: Form | null;
  /** "student" in "Moje postępy", "neutral" in the teacher's view. */
  voice?: "student" | "neutral";
};

// Long headers break into two lines instead of widening the table
const WRAP_HEAD = "h-auto py-2 align-bottom leading-snug whitespace-normal";

/** No results in the form at all: a dash, read out as words. */
function NoData() {
  return (
    <>
      <span aria-hidden="true" className="text-muted-foreground">
        –
      </span>
      <span className="sr-only">brak wyników</span>
    </>
  );
}

function Muted({ children }: { children: ReactNode }) {
  return <span className="text-muted-foreground">{children}</span>;
}

/** "Za pierwszym razem": "75%" with "3 z 4", or "za mało danych (n = 1)". */
function FirstTryCell({ row }: { row: FormTableRow }) {
  if (row.first_try_lessons === 0) {
    return <NoData />;
  }
  if (row.first_try_rate === null) {
    // May break into two lines: the column stays as wide as its header
    return (
      <span className="inline-block max-w-28 whitespace-normal text-muted-foreground">
        {tooFewText(row.first_try_lessons)}
      </span>
    );
  }
  return (
    <>
      <span className="font-medium">{row.first_try_rate}%</span>{" "}
      <Muted>
        ({row.first_try_passed} z {row.first_try_lessons})
      </Muted>
    </>
  );
}

/** "Średnia": "84%", with "(1 lekcja)" when it rests on one lesson. */
function AverageCell({ row }: { row: FormTableRow }) {
  if (row.average === null) {
    return <NoData />;
  }
  return (
    <>
      <span className="font-medium">{row.average}%</span>
      {row.first_try_lessons === 1 && (
        <>
          {" "}
          <Muted>({lessonsText(1)})</Muted>
        </>
      )}
    </>
  );
}

/** Percent of the profile: a thin bar in the colour of the form and the number. */
function PercentCell({ form, value }: { form: Form; value: number | null }) {
  if (value === null) {
    return <NoData />;
  }
  return (
    <span className="flex items-center justify-end gap-2">
      <span
        aria-hidden="true"
        className="h-1.5 w-12 overflow-hidden rounded-full bg-muted"
      >
        <span
          className={cn("block h-full rounded-full", FORM_BAR[form])}
          style={{ width: `${value}%` }}
        />
      </span>
      <span className="w-10 font-medium">{value}%</span>
    </span>
  );
}

/**
 * Stage 10: one row per form (V / A / K) with lessons, attempts, first tries,
 * average, best result, status (R3) and percent of the profile, then one
 * sentence with the conclusion. Used in "Moje postępy" and in the teacher's
 * view of a student.
 */
export function FormTable({ forms, style, voice = "student" }: FormTableProps) {
  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent [&>th]:align-bottom">
            <TableHead>Forma</TableHead>
            <TableHead className="text-right">Lekcje</TableHead>
            <TableHead className="text-right">Podejścia</TableHead>
            <TableHead className="text-right">Zaliczone</TableHead>
            <TableHead className={cn(WRAP_HEAD, "text-right")}>
              Za pierwszym razem
            </TableHead>
            <TableHead className="text-right">Średnia</TableHead>
            <TableHead className={cn(WRAP_HEAD, "text-right")}>
              Najlepszy wynik
            </TableHead>
            <TableHead>Status</TableHead>
            <TableHead className={cn(WRAP_HEAD, "text-right")}>
              Procent profilu
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {FORMS.map((form) => {
            const row = forms[form];
            return (
              <TableRow key={form} className="hover:bg-transparent">
                <TableCell className="py-3">
                  <FormMark
                    form={form}
                    label={formLabel(form)}
                    className="font-medium"
                  />
                  {form === style && (
                    <span className="block pl-4 text-sm text-muted-foreground">
                      {activeStyleText(voice)}
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {row.lessons}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {row.attempts}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {row.passed_lessons}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  <FirstTryCell row={row} />
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  <AverageCell row={row} />
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  {row.best === null ? (
                    <NoData />
                  ) : (
                    <span className="font-medium">{row.best}%</span>
                  )}
                </TableCell>
                <TableCell
                  className={cn(!row.confirmed && "text-muted-foreground")}
                >
                  {formStatusText(row.confirmed)}
                </TableCell>
                <TableCell className="text-right tabular-nums">
                  <PercentCell form={form} value={row.percent} />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
      <p className="max-w-[65ch] text-pretty">
        {formTableConclusion(forms, voice)}
      </p>
    </div>
  );
}
