import { FORMS } from "@/features/content/types";
import {
  matrixCellText,
  matrixConclusions,
  notEnoughDataText,
  panelFormName,
} from "@/features/learning-style/explain";
import { cn } from "@/shared/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { FORM_BAR } from "../format";
import type { CourseStats, MatrixCell } from "../types";
import { FormLabel } from "./FormLabel";

type LessonFormMatrixProps = Pick<CourseStats, "matrix" | "form_gaps">;

function Cell({ cell, bar }: { cell: MatrixCell; bar: string }) {
  const text = matrixCellText(cell);
  if (text === null) {
    return (
      <>
        <span aria-hidden="true" className="text-muted-foreground">
          —
        </span>
        <span className="sr-only">{notEnoughDataText(cell.n)}</span>
      </>
    );
  }
  return (
    <span className="flex items-center justify-end gap-3">
      <span
        aria-hidden="true"
        className="block h-1.5 w-12 shrink-0 overflow-hidden rounded-full bg-muted"
      >
        <span
          className={cn("block h-full rounded-full", bar)}
          style={{ width: `${Math.max(0, Math.min(100, cell.average ?? 0))}%` }}
        />
      </span>
      <span className="w-16 text-right">{text}</span>
    </span>
  );
}

/** "W jakiej formie działa każda lekcja": lessons × V / A / K. */
export function LessonFormMatrix({ matrix, form_gaps }: LessonFormMatrixProps) {
  const conclusions = matrixConclusions(matrix, form_gaps);

  if (matrix.length === 0) {
    return <p className="text-muted-foreground">{conclusions[0]}</p>;
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Lekcja</TableHead>
            {FORMS.map((form) => (
              <TableHead key={form} className="text-right">
                <FormLabel form={form} name={panelFormName(form)} />
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {matrix.map((row) => (
            <TableRow key={row.lesson_id}>
              <TableCell className="min-w-48 whitespace-normal">
                <span className="text-muted-foreground tabular-nums">
                  {row.number}.
                </span>{" "}
                {row.title}
              </TableCell>
              {FORMS.map((form) => (
                <TableCell key={form} className="text-right tabular-nums">
                  <Cell cell={row.cells[form]} bar={FORM_BAR[form]} />
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <ul role="list" className="max-w-[65ch] space-y-2">
        {conclusions.map((sentence) => (
          <li key={sentence}>{sentence}</li>
        ))}
      </ul>
    </div>
  );
}
