import { Fragment } from "react";

import { FormMark } from "@/features/learning-style/components/FormMark";
import { cn } from "@/shared/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { formatDateTime } from "../format";
import type { LessonProgress } from "../types";

/**
 * Every quiz attempt grouped by lesson. The first attempt in a form (the one
 * that changed the percentages, R2) is marked in the last column. Course and
 * lesson titles wrap, so the table fits the page on a computer; on a phone it
 * scrolls inside its own container.
 */
export function LessonResultsTable({ lessons }: { lessons: LessonProgress[] }) {
  const withAttempts = lessons.filter((lesson) => lesson.attempts.length > 0);
  if (withAttempts.length === 0) {
    return (
      <p className="text-muted-foreground">Nie ma jeszcze wyników quizów.</p>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Kurs</TableHead>
          <TableHead>Lekcja</TableHead>
          <TableHead>Podejście</TableHead>
          <TableHead>Forma</TableHead>
          <TableHead className="text-right">Wynik</TableHead>
          <TableHead>Procenty form</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {withAttempts.map((lesson) => (
          <Fragment key={lesson.lesson_id}>
            {lesson.attempts.map((attempt, index) => {
              const first = index === 0;
              const span = lesson.attempts.length;
              return (
                <TableRow
                  key={`${lesson.lesson_id}-${attempt.at}`}
                  className={cn(
                    "hover:bg-transparent",
                    index < span - 1 && "border-b-border/40",
                  )}
                >
                  {first && (
                    <>
                      <TableCell
                        rowSpan={span}
                        className="max-w-48 min-w-32 align-top whitespace-normal"
                      >
                        {lesson.course_title}
                      </TableCell>
                      <TableCell
                        rowSpan={span}
                        className="max-w-64 min-w-40 align-top whitespace-normal"
                      >
                        <span className="font-medium">
                          {lesson.number !== null && `${lesson.number}. `}
                          {lesson.lesson_title}
                        </span>
                        <span className="block text-muted-foreground">
                          {lesson.passed ? "zaliczona" : "niezaliczona"}
                        </span>
                      </TableCell>
                    </>
                  )}
                  <TableCell className="tabular-nums">
                    {index + 1}.{" "}
                    <span className="text-muted-foreground">
                      {formatDateTime(attempt.at)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <FormMark form={attempt.form} />
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    <span className="font-medium">{attempt.percent}%</span>{" "}
                    <span className="text-muted-foreground">
                      {attempt.passed ? "zaliczone" : "niezaliczone"}
                    </span>
                  </TableCell>
                  <TableCell
                    className={cn(
                      attempt.counted ? "font-medium" : "text-muted-foreground",
                    )}
                  >
                    {attempt.counted ? "liczy się" : "powtórka, bez zmian"}
                  </TableCell>
                </TableRow>
              );
            })}
          </Fragment>
        ))}
      </TableBody>
    </Table>
  );
}
