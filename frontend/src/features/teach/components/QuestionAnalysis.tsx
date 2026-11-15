"use client";

import { ChevronDownIcon } from "lucide-react";

import {
  questionRatingText,
  questionSummaryText,
} from "@/features/learning-style/explain";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/shared/ui/collapsible";
import { Spinner } from "@/shared/ui/spinner";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { formatPercent } from "../format";
import { useCourseQuestionStats } from "../hooks";
import type { LessonQuestionStats, QuestionStatsRow } from "../types";

const numberHead = "h-auto py-2 text-right align-bottom whitespace-normal";

function TopWrongCell({ question }: { question: QuestionStatsRow }) {
  if (question.top_wrong) {
    return question.top_wrong.text;
  }
  return (
    <span className="text-muted-foreground">
      {question.drawn === 0 ? "–" : "nikt nie odpowiedział źle"}
    </span>
  );
}

function QuestionTable({ questions }: { questions: QuestionStatsRow[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="align-bottom">Pytanie</TableHead>
          <TableHead className={numberHead}>Wylosowane</TableHead>
          <TableHead className={numberHead}>Poprawne</TableHead>
          <TableHead className="h-auto py-2 align-bottom whitespace-normal">
            Najczęstsza zła odpowiedź
          </TableHead>
          <TableHead className={numberHead}>Wybierana</TableHead>
          <TableHead className="align-bottom">Ocena</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {questions.map((question) => (
          <TableRow key={question.question_id}>
            <TableCell className="min-w-64 whitespace-normal">
              {question.text}
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {question.drawn}
            </TableCell>
            <TableCell className="text-right font-medium tabular-nums">
              {formatPercent(question.correct_percent)}
            </TableCell>
            <TableCell className="min-w-40 whitespace-normal">
              <TopWrongCell question={question} />
            </TableCell>
            <TableCell className="text-right tabular-nums">
              {formatPercent(question.top_wrong?.percent)}
            </TableCell>
            <TableCell
              className={cn(
                question.rating === null && "text-muted-foreground",
                question.rating === "hard" && "font-medium",
              )}
            >
              {questionRatingText(question.rating, question.drawn)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function LessonQuestions({ lesson }: { lesson: LessonQuestionStats }) {
  return (
    <Collapsible>
      <CollapsibleTrigger className="group flex min-h-control w-full items-center gap-3 px-2 py-3 text-left outline-none hover:bg-muted/50 focus-visible:ring-3 focus-visible:ring-ring/50">
        <span className="min-w-0 flex-1">
          <span className="text-muted-foreground tabular-nums">
            {lesson.number}.
          </span>{" "}
          <span className="font-medium">{lesson.title}</span>
        </span>
        <span className="shrink-0 text-sm text-muted-foreground">
          {questionSummaryText(lesson.questions)}
        </span>
        <ChevronDownIcon
          aria-hidden="true"
          className="size-4 shrink-0 text-muted-foreground transition-transform group-data-[panel-open]:rotate-180"
        />
      </CollapsibleTrigger>
      <CollapsibleContent className="pb-4">
        {lesson.questions.length === 0 ? (
          <p className="px-2 text-muted-foreground">Lekcja nie ma quizu.</p>
        ) : (
          <QuestionTable questions={lesson.questions} />
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}

/** "Które pytania są za trudne albo źle ułożone": one disclosure per lesson. */
export function QuestionAnalysis({ courseId }: { courseId: number }) {
  const query = useCourseQuestionStats(courseId);

  if (query.isPending) {
    return (
      <div className="flex justify-center py-8">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (query.error || !query.data) {
    return (
      <div className="flex flex-wrap items-center gap-4">
        <p className="text-muted-foreground">
          Nie udało się wczytać analizy pytań.
        </p>
        <Button variant="outline" onClick={() => void query.refetch()}>
          Spróbuj ponownie
        </Button>
      </div>
    );
  }

  const lessons = query.data;
  if (lessons.length === 0) {
    return (
      <p className="text-muted-foreground">
        Kurs nie ma jeszcze opublikowanych lekcji.
      </p>
    );
  }
  const anyDrawn = lessons.some((lesson) =>
    lesson.questions.some((question) => question.drawn > 0),
  );

  return (
    <div className="space-y-4">
      <p className="max-w-[65ch]">
        {anyDrawn
          ? "Jeśli większość uczniów wybiera tę samą złą odpowiedź, pytanie jest zwykle niejasne albo ma błąd w kluczu odpowiedzi."
          : "Uczniowie nie rozwiązali jeszcze żadnego quizu w tym kursie."}
      </p>
      <ul role="list" className="divide-y border-y">
        {lessons.map((lesson) => (
          <li key={lesson.lesson_id}>
            <LessonQuestions lesson={lesson} />
          </li>
        ))}
      </ul>
    </div>
  );
}
