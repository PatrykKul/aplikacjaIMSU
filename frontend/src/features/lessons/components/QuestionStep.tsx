"use client";

import { type FormEvent, type ReactNode, useId, useState } from "react";

import { errorMessage } from "@/shared/api/error-messages";
import { Button } from "@/shared/ui/button";
import { MathMarkdown } from "@/shared/ui/math-markdown";
import { Spinner } from "@/shared/ui/spinner";

import { useCheckAnswer } from "../hooks";
import type {
  AnswerValue,
  CheckResult,
  QuestionStep as QuestionData,
} from "../types";
import { ChoiceAnswer } from "./ChoiceAnswer";
import { NumberAnswer } from "./NumberAnswer";
import { StepFeedback } from "./StepFeedback";

type Status = "open" | "correct" | "revealed";

type QuestionStepProps = {
  lessonId: number;
  step: QuestionData;
  onComplete: (firstTry: boolean) => void;
  next?: ReactNode;
};

export function QuestionStep({
  lessonId,
  step,
  onComplete,
  next,
}: QuestionStepProps) {
  const id = useId();
  const check = useCheckAnswer(lessonId);
  const [text, setText] = useState("");
  const [choice, setChoice] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("open");
  const [result, setResult] = useState<CheckResult | null>(null);
  const [attempts, setAttempts] = useState(0);
  const [lastAnswer, setLastAnswer] = useState<AnswerValue | null>(null);
  const [hintShown, setHintShown] = useState(false);

  const isChoice = step.answer.type === "choice";
  const locked = status !== "open";
  const errorId = error ? `${id}-error` : undefined;

  function submit(event: FormEvent) {
    event.preventDefault();
    const answer: AnswerValue | null = isChoice ? choice : text.trim();
    if (answer === null || answer === "") {
      setError(isChoice ? "Wybierz odpowiedź." : "Wpisz odpowiedź.");
      return;
    }
    check.mutate(
      { stepKey: step.key, answer },
      {
        onSuccess: (checked) => {
          setResult(checked);
          setLastAnswer(answer);
          setAttempts(attempts + 1);
          if (checked.correct) {
            setStatus("correct");
            onComplete(attempts === 0);
          }
        },
        onError: (failure) => setError(errorMessage(failure)),
      },
    );
  }

  function reveal() {
    if (lastAnswer === null) {
      return;
    }
    check.mutate(
      { stepKey: step.key, answer: lastAnswer, reveal: true },
      {
        onSuccess: (checked) => {
          setResult(checked);
          setStatus("revealed");
          onComplete(false);
        },
        onError: (failure) => setError(errorMessage(failure)),
      },
    );
  }

  function changeAnswer() {
    setError(null);
  }

  return (
    <form onSubmit={submit} className="space-y-4" noValidate>
      <MathMarkdown>{step.prompt}</MathMarkdown>

      {step.answer.type === "number" ? (
        <NumberAnswer
          id={`${id}-answer`}
          unit={step.answer.unit}
          value={text}
          onChange={(value) => {
            setText(value);
            changeAnswer();
          }}
          disabled={locked}
          errorId={errorId}
        />
      ) : (
        <ChoiceAnswer
          name={`${id}-answer`}
          options={step.answer.options}
          value={choice}
          onChange={(value) => {
            setChoice(value);
            changeAnswer();
          }}
          disabled={locked}
          errorId={errorId}
        />
      )}

      {error && (
        <p id={errorId} role="alert" className="text-sm font-medium">
          {error}
        </p>
      )}

      {hintShown && step.hint && (
        <div className="rounded-lg bg-muted px-4 py-3">
          <p className="text-sm font-semibold">Podpowiedź</p>
          <MathMarkdown>{step.hint}</MathMarkdown>
        </div>
      )}

      {/* Feedback is announced by screen readers when it changes */}
      <div aria-live="polite">
        {result && status === "correct" && (
          <StepFeedback kind="correct" result={result} />
        )}
        {result && status === "open" && !result.correct && (
          <StepFeedback kind="incorrect" result={result} />
        )}
        {result && status === "revealed" && (
          <StepFeedback kind="solution" result={result} />
        )}
      </div>

      {locked ? (
        next
      ) : (
        <div className="flex flex-wrap gap-2">
          <Button type="submit" disabled={check.isPending}>
            {check.isPending && <Spinner data-icon="inline-start" />}
            Sprawdź
          </Button>
          {step.hint && !hintShown && (
            <Button
              type="button"
              variant="outline"
              onClick={() => setHintShown(true)}
            >
              Podpowiedź
            </Button>
          )}
          {attempts > 0 && (
            <Button
              type="button"
              variant="outline"
              onClick={reveal}
              disabled={check.isPending}
            >
              Pokaż rozwiązanie
            </Button>
          )}
        </div>
      )}
    </form>
  );
}
