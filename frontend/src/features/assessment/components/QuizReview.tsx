import { CheckIcon, XIcon } from "lucide-react";

import { cn } from "@/shared/lib/utils";

import type { QuestionResult } from "../types";

/** Every question after checking: the chosen and the correct answer, then the explanation. */
export function QuizReview({ results }: { results: QuestionResult[] }) {
  return (
    <ol className="space-y-6">
      {results.map((result, index) => (
        <li key={result.question_id} className="space-y-2.5">
          <p className="font-medium">
            {index + 1}. {result.text}
          </p>
          <p
            className={cn(
              "text-sm font-medium",
              result.correct
                ? "text-feedback-correct-foreground"
                : "text-feedback-incorrect-foreground",
            )}
          >
            {result.correct ? "Dobrze!" : "Jeszcze nie"}
          </p>
          <ul className="grid gap-2">
            {result.answers.map((answer) => {
              const chosen = answer.id === result.chosen_answer_id;
              const correct = answer.id === result.correct_answer_id;
              const wrong = chosen && !correct;
              return (
                <li
                  key={answer.id}
                  className={cn(
                    "flex min-h-control items-center gap-3 rounded-lg border px-3 py-2.5 text-sm",
                    correct &&
                      "border-feedback-correct-foreground/50 bg-feedback-correct",
                    wrong &&
                      "border-feedback-incorrect-foreground/50 bg-feedback-incorrect",
                    !correct && !wrong && "text-muted-foreground",
                  )}
                >
                  {correct ? (
                    <CheckIcon
                      aria-hidden="true"
                      className="size-4 shrink-0 text-feedback-correct-foreground"
                    />
                  ) : wrong ? (
                    <XIcon
                      aria-hidden="true"
                      className="size-4 shrink-0 text-feedback-incorrect-foreground"
                    />
                  ) : (
                    <span aria-hidden="true" className="size-4 shrink-0" />
                  )}
                  <span className="flex-1 text-foreground">{answer.text}</span>
                  {(chosen || correct) && (
                    <span
                      className={cn(
                        "text-xs font-medium",
                        correct
                          ? "text-feedback-correct-foreground"
                          : "text-feedback-incorrect-foreground",
                      )}
                    >
                      {chosen && correct
                        ? "Twoja odpowiedź · poprawna"
                        : chosen
                          ? "Twoja odpowiedź"
                          : "Poprawna odpowiedź"}
                    </span>
                  )}
                </li>
              );
            })}
          </ul>
          <p className="max-w-[65ch] text-sm">
            <span className="font-medium">Wyjaśnienie: </span>
            {result.explanation}
          </p>
        </li>
      ))}
    </ol>
  );
}
