import Link from "next/link";

import { cn } from "@/shared/lib/utils";
import { buttonVariants } from "@/shared/ui/button";
import { MathMarkdown } from "@/shared/ui/math-markdown";

type LessonSummaryProps = {
  firstTry: number;
  questions: number;
  goal: string;
  courseHref: string;
  nextHref: string | null;
};

// A nautral score, then what the student learned
export function LessonSummary({
  firstTry,
  questions,
  goal,
  courseHref,
  nextHref,
}: LessonSummaryProps) {
  return (
    <div className="space-y-6">
      <div className="space-y-1">
        <h2 className="text-2xl font-semibold tracking-tight">
          Lekcja ukończona
        </h2>
        <p>
          {firstTry === questions
            ? "Wszystko za pierwszym razem!"
            : `Za pierwszym razem: ${firstTry} z ${questions} pytań.`}
        </p>
      </div>
      {goal && (
        <div className="space-y-1">
          <h3 className="font-semibold">Czego się nauczyłeś</h3>
          <MathMarkdown>{goal}</MathMarkdown>
        </div>
      )}
      <div className="flex flex-wrap gap-2">
        {nextHref && (
          <Link href={nextHref} className={buttonVariants()}>
            Następna lekcja
          </Link>
        )}
        <Link
          href={courseHref}
          className={cn(
            buttonVariants({ variant: nextHref ? "outline" : "default" }),
          )}
        >
          Wróć do kursu
        </Link>
      </div>
    </div>
  );
}
