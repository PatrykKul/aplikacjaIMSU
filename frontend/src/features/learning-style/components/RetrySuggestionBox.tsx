"use client";

import { RefreshCwIcon, RotateCcwIcon } from "lucide-react";

import type { Form } from "@/features/content/types";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import {
  SOFT_RETRY_ACTION,
  SOFT_RETRY_TEXT,
  softSuggestionLink,
  suggestionAction,
  suggestionReason,
  suggestionStrength,
  suggestionTitle,
} from "../explain";
import { useLearningProfile } from "../hooks";
import type { RetrySuggestion } from "../types";

type RetrySuggestionBoxProps = {
  suggestion: RetrySuggestion;
  /** Changes the form of the lesson and draws new questions. */
  onRetry: (form: Form) => void;
  pending?: boolean;
  /**
   * After the quiz: a new set of questions in the same form. Without it (above
   * the lesson) the soft variant points to the quiz below.
   */
  onAgain?: () => void;
};

// Inline action inside a sentence: looks like a link, works as a button
const INLINE_ACTION =
  "font-medium text-primary underline underline-offset-4 hover:text-primary/80 focus-visible:rounded-sm focus-visible:ring-3 focus-visible:ring-ring/50 focus-visible:outline-none disabled:opacity-50";

/**
 * R5 after a failed quiz. `soft` (one slip in a form that worked): "Rozwiąż
 * jeszcze raz" first, the other form only as a calm sentence. `strong`: a
 * neutral frame with the reason and "Przerób tę lekcję w formie X".
 */
export function RetrySuggestionBox({
  suggestion,
  onRetry,
  pending,
  onAgain,
}: RetrySuggestionBoxProps) {
  const profile = useLearningProfile();
  const form = suggestion.suggested.form;

  if (suggestionStrength(suggestion) === "soft") {
    const otherForm = (
      <button
        type="button"
        disabled={pending}
        onClick={() => onRetry(form)}
        className={INLINE_ACTION}
      >
        {softSuggestionLink(form)}
      </button>
    );
    return (
      <section aria-label="Sugestia" className="space-y-3">
        {onAgain && (
          <Button onClick={onAgain}>
            <RotateCcwIcon data-icon="inline-start" />
            {SOFT_RETRY_ACTION}
          </Button>
        )}
        <p className="text-pretty">
          {onAgain ? (
            <>
              {SOFT_RETRY_TEXT.afterQuiz} {otherForm}.
            </>
          ) : (
            <>
              {SOFT_RETRY_TEXT.inLesson}{" "}
              <a href="#quiz" className={INLINE_ACTION}>
                {SOFT_RETRY_TEXT.quizLink}
              </a>{" "}
              {SOFT_RETRY_TEXT.or} {otherForm}.
            </>
          )}
          {pending && <Spinner className="ml-2 inline size-4 align-middle" />}
        </p>
      </section>
    );
  }

  return (
    <section
      aria-label="Sugestia"
      className="space-y-3 rounded-lg border bg-muted/50 p-4 sm:p-5"
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
