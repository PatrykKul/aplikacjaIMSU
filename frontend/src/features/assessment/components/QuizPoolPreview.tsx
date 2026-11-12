"use client";

import { CheckIcon, ListChecksIcon } from "lucide-react";

import { cn } from "@/shared/lib/utils";
import { Spinner } from "@/shared/ui/spinner";

import { assessmentError } from "../errors";
import { useQuizPool } from "../hooks";
import { MIN_PUBLISHED_QUESTIONS, QUIZ_SIZE, questionsLabel } from "../types";

/** The pool of a lesson for the author and the admin: correct answers and explanations. */
export function QuizPoolPreview({ lessonId }: { lessonId: number }) {
  const pool = useQuizPool(lessonId);

  let body;
  if (pool.isPending) {
    body = (
      <div className="flex justify-center py-6">
        <Spinner className="size-5" />
      </div>
    );
  } else if (pool.isError) {
    body = (
      <p role="alert" className="text-sm text-destructive">
        Nie udało się wczytać pytań. {assessmentError(pool.error)}
      </p>
    );
  } else if (pool.data.questions.length === 0) {
    body = (
      <p className="text-muted-foreground">Ta lekcja nie ma jeszcze pytań.</p>
    );
  } else {
    body = (
      <ol className="space-y-6">
        {pool.data.questions.map((question, index) => (
          <li key={question.id} className="space-y-2.5">
            <p className="font-medium">
              {index + 1}. {question.text}
            </p>
            <ul className="grid gap-2">
              {question.answers.map((answer) => {
                const correct = answer.id === question.correct_answer_id;
                return (
                  <li
                    key={answer.id}
                    className={cn(
                      "flex min-h-control items-center gap-3 rounded-lg border px-3 py-2.5 text-sm",
                      correct &&
                        "border-feedback-correct-foreground/50 bg-feedback-correct",
                    )}
                  >
                    {correct ? (
                      <CheckIcon
                        aria-hidden="true"
                        className="size-4 shrink-0 text-feedback-correct-foreground"
                      />
                    ) : (
                      <span aria-hidden="true" className="size-4 shrink-0" />
                    )}
                    <span className="flex-1">{answer.text}</span>
                    {correct && (
                      <span className="text-xs font-medium text-feedback-correct-foreground">
                        Poprawna odpowiedź
                      </span>
                    )}
                  </li>
                );
              })}
            </ul>
            <p className="max-w-[65ch] text-sm">
              <span className="font-medium">Wyjaśnienie: </span>
              {question.explanation}
            </p>
          </li>
        ))}
      </ol>
    );
  }

  const count = pool.data?.questions.length ?? 0;

  return (
    <section
      aria-labelledby="pool-title"
      className="space-y-6 rounded-xl p-5 ring-1 ring-foreground/10 sm:px-9 sm:py-8"
    >
      <div className="space-y-1.5">
        <h2
          id="pool-title"
          className="flex items-center gap-2 text-xl font-semibold"
        >
          <ListChecksIcon aria-hidden="true" className="size-5" />
          Pula pytań
        </h2>
        <p className="text-sm text-muted-foreground">
          {questionsLabel(count)} w puli (do publikacji min.{" "}
          {MIN_PUBLISHED_QUESTIONS}). Uczeń przy każdym podejściu dostaje{" "}
          {QUIZ_SIZE} wylosowanych, przy powtórce najpierw te, których nie miał
          ostatnio.
        </p>
      </div>
      {body}
    </section>
  );
}
