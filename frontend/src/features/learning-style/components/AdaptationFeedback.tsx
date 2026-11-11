"use client";

import { CircleCheckIcon, RotateCcwIcon } from "lucide-react";

import { cn } from "@/shared/lib/utils";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";

import type { QuizFeedback } from "../types";
import { StyleProposalBanner } from "./StyleProposalBanner";

/**
 * Shown by the quiz block after the server scored the answers.
 * `feedback` is the value of `record_quiz_result` sent in the quiz response.
 */
export function AdaptationFeedback({ feedback }: { feedback: QuizFeedback }) {
  const { V, A, K } = feedback.weights;
  // A failed quiz is information, not an error: soft brick, not `destructive`
  const tone = feedback.passed
    ? "border-feedback-correct-foreground/25 bg-feedback-correct text-feedback-correct-foreground"
    : "border-feedback-incorrect-foreground/25 bg-feedback-incorrect text-feedback-incorrect-foreground";

  return (
    <div className="space-y-3">
      <Alert className={tone}>
        {feedback.passed ? <CircleCheckIcon /> : <RotateCcwIcon />}
        <AlertTitle>
          {feedback.passed
            ? `Zaliczone: ${feedback.percent}%`
            : `${feedback.percent}% – spróbuj jeszcze raz`}
        </AlertTitle>
        <AlertDescription className={cn("text-current")}>
          <p>{feedback.why}</p>
          <p>
            {feedback.weights_changed
              ? `System zaktualizował wagi Twoich stylów: V ${V} / A ${A} / K ${K}.`
              : `Wagi stylów bez zmian (liczy się pierwszy sukces i pierwsza porażka w lekcji): V ${V} / A ${A} / K ${K}.`}
          </p>
        </AlertDescription>
      </Alert>
      {feedback.proposal && (
        <StyleProposalBanner proposal={feedback.proposal} />
      )}
    </div>
  );
}
