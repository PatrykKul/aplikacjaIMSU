"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useMemo, useState } from "react";

import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { learningStyleError } from "../errors";
import { useSubmitSurvey, useSurveyQuestions } from "../hooks";
import type { SurveyAnswer, SurveyQuestion } from "../types";

/**
 * Answers in a stable mixed order, so the visual answer is not always first.
 * Deterministic (no Math.random) - the same order on every render.
 */
function mixAnswers(question: SurveyQuestion): SurveyAnswer[] {
  const rank = (answer: SurveyAnswer) =>
    (question.id * 31 + answer.id * 17) % 7;
  return [...question.answers].sort((a, b) => rank(a) - rank(b) || a.id - b.id);
}

export function SurveyForm() {
  const router = useRouter();
  const questions = useSurveyQuestions();
  const submit = useSubmitSurvey();
  const [chosen, setChosen] = useState<Record<number, number>>({});
  const [showMissing, setShowMissing] = useState(false);

  const mixed = useMemo(
    () => (questions.data ?? []).map((q) => ({ ...q, answers: mixAnswers(q) })),
    [questions.data],
  );

  if (questions.isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (questions.isError) {
    return (
      <PageMessage
        title="Nie udało się wczytać ankiety"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button onClick={() => questions.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }

  const answered = mixed.filter((q) => chosen[q.id] !== undefined).length;
  const total = mixed.length;
  const complete = total > 0 && answered === total;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!complete) {
      setShowMissing(true);
      const first = mixed.find((q) => chosen[q.id] === undefined);
      if (first) {
        document.getElementById(`question-${first.id}`)?.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }
      return;
    }
    submit.mutate(
      mixed.map((q) => ({ question_id: q.id, answer_id: chosen[q.id] })),
      { onSuccess: () => router.push("/survey/result") },
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6" noValidate>
      <div className="sticky top-0 z-10 -mx-4 border-b bg-background/95 px-4 py-3 backdrop-blur sm:mx-0 sm:rounded-lg sm:border">
        <div className="flex items-center justify-between text-sm">
          <span>
            Odpowiedziano na{" "}
            <strong className="tabular-nums">{answered}</strong> z {total} pytań
          </span>
        </div>
        <div
          className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"
          role="progressbar"
          aria-label="Postęp ankiety"
          aria-valuemin={0}
          aria-valuemax={total}
          aria-valuenow={answered}
        >
          <div
            className="h-full rounded-full bg-primary transition-[width]"
            style={{ width: `${total ? (answered / total) * 100 : 0}%` }}
          />
        </div>
      </div>

      <ol className="space-y-4">
        {mixed.map((question, index) => {
          const missing = showMissing && chosen[question.id] === undefined;
          return (
            <li key={question.id} id={`question-${question.id}`}>
              <fieldset
                className={cn(
                  "space-y-3 rounded-xl border p-4",
                  missing && "border-destructive",
                )}
                aria-invalid={missing || undefined}
              >
                <legend className="px-1 font-medium">
                  {index + 1}. {question.text}
                </legend>
                {question.answers.map((answer) => (
                  <label
                    key={answer.id}
                    className={cn(
                      "flex cursor-pointer items-start gap-3 rounded-lg border p-3 text-sm transition-colors hover:bg-muted/50",
                      chosen[question.id] === answer.id &&
                        "border-primary bg-primary/5",
                    )}
                  >
                    <input
                      type="radio"
                      name={`question-${question.id}`}
                      value={answer.id}
                      checked={chosen[question.id] === answer.id}
                      onChange={() =>
                        setChosen((prev) => ({
                          ...prev,
                          [question.id]: answer.id,
                        }))
                      }
                      className="mt-0.5 size-4 accent-primary"
                    />
                    <span>{answer.text}</span>
                  </label>
                ))}
                {missing && (
                  <p className="text-sm text-destructive">
                    Wybierz jedną odpowiedź.
                  </p>
                )}
              </fieldset>
            </li>
          );
        })}
      </ol>

      {submit.isError && (
        <p role="alert" className="text-sm text-destructive">
          {learningStyleError(submit.error)}
        </p>
      )}
      {showMissing && !complete && (
        <p role="alert" className="text-sm text-destructive">
          Brakuje odpowiedzi na {total - answered} z {total} pytań.
        </p>
      )}
      <Button type="submit" size="lg" disabled={submit.isPending}>
        {submit.isPending && <Spinner data-icon="inline-start" />}
        Zobacz mój styl uczenia się
      </Button>
    </form>
  );
}
