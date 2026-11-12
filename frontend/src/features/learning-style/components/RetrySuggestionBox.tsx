"use client";

import { RefreshCwIcon } from "lucide-react";

import type { Form } from "@/features/content/types";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import {
  suggestionAction,
  suggestionReason,
  suggestionTitle,
} from "../explain";
import { useLearningProfile } from "../hooks";
import type { RetrySuggestion } from "../types";

type RetrySuggestionBoxProps = {
  suggestion: RetrySuggestion;
  /** Changes the form of the lesson and draws new questions. */
  onRetry: (form: Form) => void;
  pending?: boolean;
};

/** R5: after a failed quiz - which form to try and why, with one button. */
export function RetrySuggestionBox({
  suggestion,
  onRetry,
  pending,
}: RetrySuggestionBoxProps) {
  const profile = useLearningProfile();
  const form = suggestion.suggested.form;
  return (
    <section
      aria-label="Sugestia"
      className="space-y-3 rounded-lg border border-feedback-incorrect-foreground/30 bg-feedback-incorrect p-4 text-feedback-incorrect-foreground sm:p-5"
    >
      <div className="space-y-1.5">
        <p className="font-medium">{suggestionTitle(suggestion)}</p>
        <p className="text-pretty tabular-nums">
          {suggestionReason(suggestion, {
            survey: profile.data?.survey?.percentages,
          })}
        </p>
      </div>
      <Button disabled={pending} onClick={() => onRetry(form)}>
        {pending ? (
          <Spinner data-icon="inline-start" />
        ) : (
          <RefreshCwIcon data-icon="inline-start" />
        )}
        {suggestionAction(form)}
      </Button>
    </section>
  );
}
