import { CheckIcon, LightbulbIcon, XIcon } from "lucide-react";

import { cn } from "@/shared/lib/utils";
import { MathMarkdown } from "@/shared/ui/math-markdown";

import type { CheckResult } from "../types";

type StepFeedbackProps = {
  kind: "correct" | "incorrect" | "solution";
  result: CheckResult;
};

const styles = {
  correct: "bg-feedback-correct text-feedback-correct-foreground",
  incorrect: "bg-feedback-incorrect text-feedback-incorrect-foreground",
  solution: "bg-muted text-foreground",
};

// Decimal answers are stored as "12.5"; Polish uses a comma
function polishNumber(text: string): string {
  return text.replace(/(\d)\.(\d)/g, "$1,$2");
}

// The state is always given by a word and an icon, never by colour alone
export function StepFeedback({ kind, result }: StepFeedbackProps) {
  return (
    <div className={cn("space-y-2 rounded-lg px-4 py-3", styles[kind])}>
      <p className="flex items-center gap-2 font-semibold">
        {kind === "correct" && (
          <CheckIcon aria-hidden="true" className="size-5" />
        )}
        {kind === "incorrect" && (
          <XIcon aria-hidden="true" className="size-5" />
        )}
        {kind === "solution" && (
          <LightbulbIcon aria-hidden="true" className="size-5" />
        )}
        {kind === "correct" && "Dobrze!"}
        {kind === "incorrect" && "Jeszcze nie"}
        {kind === "solution" && "Rozwiązanie"}
      </p>
      {kind === "incorrect" && (
        <MathMarkdown>{result.feedback ?? "Spróbuj jeszcze raz."}</MathMarkdown>
      )}
      {kind === "solution" && result.correct_answer && (
        <p>
          Poprawna odpowiedź:{" "}
          <MathMarkdown inline className="font-semibold">
            {polishNumber(result.correct_answer)}
          </MathMarkdown>
        </p>
      )}
      {kind !== "incorrect" && result.explanation && (
        <MathMarkdown>{result.explanation}</MathMarkdown>
      )}
    </div>
  );
}
