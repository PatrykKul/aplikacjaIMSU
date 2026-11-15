import {
  decimalText,
  hardestLessonText,
  notEnoughDataText,
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

import { formatPercent } from "../format";
import type { CourseStats } from "../types";

type LessonDifficultyProps = Pick<CourseStats, "lessons" | "hardest">;

const numberHead = "h-auto py-2 text-right align-bottom whitespace-normal";

/** "Które lekcje sprawiają trudność": one row per published lesson. */
export function LessonDifficulty({ lessons, hardest }: LessonDifficultyProps) {
  if (lessons.length === 0) {
    return (
      <p className="text-muted-foreground">
        {hardestLessonText(hardest, lessons)}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="align-bottom">Lekcja</TableHead>
            <TableHead className={numberHead}>Rozpoczęło</TableHead>
            <TableHead className={numberHead}>Zaliczyło</TableHead>
            <TableHead className={numberHead}>Zaliczalność</TableHead>
            <TableHead className={cn(numberHead, "min-w-32")}>
              Średnia z pierwszych podejść
            </TableHead>
            <TableHead className={cn(numberHead, "min-w-36")}>
              Średnia liczba podejść do zaliczenia
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {lessons.map((lesson) => (
            <TableRow key={lesson.lesson_id}>
              <TableCell className="min-w-48 whitespace-normal">
                <span className="text-muted-foreground tabular-nums">
                  {lesson.number}.
                </span>{" "}
                {lesson.title}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {lesson.started}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {lesson.passed}
              </TableCell>
              <TableCell className="text-right font-medium tabular-nums">
                {lesson.pass_rate === null ? (
                  <span className="font-normal text-muted-foreground">
                    {notEnoughDataText(lesson.started)}
                  </span>
                ) : (
                  `${lesson.pass_rate}%`
                )}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {formatPercent(lesson.first_average)}
              </TableCell>
              <TableCell className="text-right tabular-nums">
                {lesson.attempts_to_pass === null
                  ? "–"
                  : decimalText(lesson.attempts_to_pass)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      <p className="max-w-[65ch]">{hardestLessonText(hardest, lessons)}</p>
    </div>
  );
}
