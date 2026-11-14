"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { FORMS } from "@/features/content/types";
import { attentionNoteText } from "@/features/learning-style/explain";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { formatDate, formatPercent, STYLE_NAMES } from "../format";
import type { CourseStudentRow } from "../types";
import { FormLabel } from "./FormLabel";

function proposalText(row: CourseStudentRow): string {
  if (!row.open_proposal) {
    return "–";
  }
  const { kind, to } = row.open_proposal;
  return kind === "revert"
    ? `powrót do ${to} (${STYLE_NAMES[to]})`
    : `zmiana na ${to} (${STYLE_NAMES[to]})`;
}

type CourseStudentsTableProps = {
  courseId: number;
  students: CourseStudentRow[];
};

/** Accepted students of the course; a row opens the student's details. */
export function CourseStudentsTable({
  courseId,
  students,
}: CourseStudentsTableProps) {
  const router = useRouter();

  if (students.length === 0) {
    return (
      <p className="text-muted-foreground">
        Na kurs nie jest jeszcze zapisany żaden uczeń. Przyjmij prośbę o zapis,
        a uczeń pojawi się tutaj.
      </p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Uczeń</TableHead>
          <TableHead>Styl</TableHead>
          {FORMS.map((form) => (
            <TableHead key={form} className="text-right">
              <abbr title={`Procent formy ${form}`} className="no-underline">
                {form}
              </abbr>
            </TableHead>
          ))}
          <TableHead>Postęp</TableHead>
          <TableHead className="text-right">Średnia</TableHead>
          <TableHead>Ostatnia aktywność</TableHead>
          <TableHead>Otwarta propozycja</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {students.map((row) => {
          const href = `/teach/courses/${courseId}/students/${row.id}`;
          return (
            <TableRow
              key={row.id}
              className="cursor-pointer"
              // The name is the real link (keyboard, screen reader); the row is a shortcut
              onClick={() => router.push(href)}
            >
              <TableCell>
                <Link
                  href={href}
                  className="font-medium underline-offset-4 hover:underline"
                  onClick={(event) => event.stopPropagation()}
                >
                  {row.display_name}
                </Link>
                <span className="block text-sm text-muted-foreground">
                  {row.email}
                </span>
                {row.attention && (
                  <span className="block text-sm font-medium">
                    {attentionNoteText(row.attention)}
                  </span>
                )}
              </TableCell>
              <TableCell>
                {row.style ? (
                  <FormLabel form={row.style} name={STYLE_NAMES[row.style]} />
                ) : (
                  <span className="text-muted-foreground">bez stylu</span>
                )}
              </TableCell>
              {FORMS.map((form) => (
                <TableCell key={form} className="text-right tabular-nums">
                  {formatPercent(row.percentages?.[form])}
                </TableCell>
              ))}
              <TableCell className="tabular-nums">
                {row.passed} z {row.total}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatPercent(row.average)}
              </TableCell>
              <TableCell>
                {row.last_activity ? formatDate(row.last_activity) : "–"}
              </TableCell>
              <TableCell>{proposalText(row)}</TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}
