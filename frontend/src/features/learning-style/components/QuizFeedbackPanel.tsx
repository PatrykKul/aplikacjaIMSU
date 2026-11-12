"use client";

import { AwardIcon } from "lucide-react";

import type { Form } from "@/features/content/types";

import {
  percentagesText,
  praiseText,
  quizChangeParts,
  quizChangeRule,
} from "../explain";
import type { QuizFeedback } from "../types";
import { RetrySuggestionBox } from "./RetrySuggestionBox";
import { StyleProposalBanner } from "./StyleProposalBanner";
import { TrialNote } from "./TrialNote";

type QuizFeedbackPanelProps = {
  feedback: QuizFeedback;
  /** R5 action: change the form of the lesson and draw new questions. */
  onRetryInForm: (form: Form) => void;
  retryPending?: boolean;
};

/** What the system decided after the attempt, with the numbers behind it. */
export function QuizFeedbackPanel({
  feedback,
  onRetryInForm,
  retryPending,
}: QuizFeedbackPanelProps) {
  return (
    <div className="space-y-5">
      <section aria-labelledby="quiz-change" className="space-y-1.5">
        <h3 id="quiz-change" className="font-semibold">
          Co to zmieniło
        </h3>
        <p className="text-lg tabular-nums">
          {quizChangeParts(feedback).join(" · ")}
        </p>
        <p className="text-sm text-muted-foreground">
          {quizChangeRule(feedback.counted, feedback.passed)} Teraz:{" "}
          <span className="tabular-nums">
            {percentagesText(feedback.percentages_after)}
          </span>
          .
        </p>
      </section>

      {feedback.praise && (
        <div className="flex gap-3 border-l-2 border-feedback-correct-foreground py-1 pl-4">
          <AwardIcon
            aria-hidden="true"
            className="mt-0.5 size-5 shrink-0 text-feedback-correct-foreground"
          />
          <p>
            <span className="font-medium">Świetna seria! </span>
            {praiseText(feedback.praise)}.
          </p>
        </div>
      )}

      {!feedback.passed && feedback.suggestion && (
        <RetrySuggestionBox
          suggestion={feedback.suggestion}
          onRetry={onRetryInForm}
          pending={retryPending}
        />
      )}

      {feedback.trial && <TrialNote trial={feedback.trial} />}

      {feedback.proposal && (
        <StyleProposalBanner proposal={feedback.proposal} />
      )}
    </div>
  );
}
