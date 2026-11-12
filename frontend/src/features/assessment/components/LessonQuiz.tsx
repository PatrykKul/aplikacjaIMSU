"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ArrowRightIcon, ListChecksIcon, RotateCcwIcon } from "lucide-react";
import Link from "next/link";
import { type FormEvent, useRef, useState } from "react";

import type { Form } from "@/features/content/types";
import { QuizFeedbackPanel } from "@/features/learning-style/components/QuizFeedbackPanel";
import {
  PASS_THRESHOLD,
  formName,
  inForm,
  quizScoreText,
} from "@/features/learning-style/explain";
import type { Study } from "@/features/learning-style/types";
import { ApiError } from "@/shared/api/client";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group";
import { Spinner } from "@/shared/ui/spinner";

import { assessmentError } from "../errors";
import { lessonQuizKey, useLessonQuiz, useSubmitQuiz } from "../hooks";
import {
  type AttemptResult,
  type QuizDraw,
  QUIZ_SIZE,
  questionsLabel,
} from "../types";
import { QuizReview } from "./QuizReview";

type LessonQuizProps = {
  lessonId: number;
  courseId: number;
  lastResult: Study["last_result"];
  /** R5: change the form of the lesson (the parent draws new questions). */
  onRetryInForm: (form: Form) => void;
  retryPending?: boolean;
  /** Told when the result appears or disappears (the lesson hides its own suggestion). */
  onResultChange?: (shown: boolean) => void;
};

function QuizQuestions({
  draw,
  pending,
  onSubmit,
}: {
  draw: QuizDraw;
  pending: boolean;
  onSubmit: (answers: Record<string, string>) => void;
}) {
  const [chosen, setChosen] = useState<Record<string, string>>({});
  const complete = draw.questions.every((q) => chosen[q.id] !== undefined);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (complete) {
      onSubmit(chosen);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <ol className="space-y-6">
        {draw.questions.map((question, index) => (
          <li key={question.id}>
            <fieldset>
              <legend
                id={`quiz-${question.id}-text`}
                className="mb-2.5 font-medium"
              >
                {index + 1}. {question.text}
              </legend>
              <RadioGroup
                aria-labelledby={`quiz-${question.id}-text`}
                value={chosen[question.id] ?? null}
                onValueChange={(value) =>
                  setChosen((prev) => ({
                    ...prev,
                    [question.id]: value as string,
                  }))
                }
              >
                {question.answers.map((answer) => (
                  <label
                    key={answer.id}
                    className={cn(
                      "flex min-h-control cursor-pointer items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-colors hover:bg-muted/50",
                      chosen[question.id] === answer.id &&
                        "border-primary bg-primary/5",
                    )}
                  >
                    <RadioGroupItem value={answer.id} />
                    <span className="flex-1">{answer.text}</span>
                  </label>
                ))}
              </RadioGroup>
            </fieldset>
          </li>
        ))}
      </ol>
      <Button type="submit" disabled={!complete || pending}>
        {pending && <Spinner data-icon="inline-start" />}
        {complete ? "Sprawdź" : "Odpowiedz na wszystkie pytania"}
      </Button>
    </form>
  );
}

function QuizResultView({
  result,
  courseId,
  onAgain,
  onRetryInForm,
  retryPending,
}: {
  result: AttemptResult;
  courseId: number;
  onAgain: () => void;
  onRetryInForm: (form: Form) => void;
  retryPending?: boolean;
}) {
  const { feedback } = result;
  const unlocked = feedback.unlocked_lesson;
  return (
    <div className="space-y-8">
      <div aria-live="polite" className="space-y-1">
        <p
          className={cn(
            "text-xl font-semibold tabular-nums",
            result.passed
              ? "text-feedback-correct-foreground"
              : "text-feedback-incorrect-foreground",
          )}
        >
          {quizScoreText(
            result.correct_count,
            result.total,
            result.percent,
            result.passed,
          )}
        </p>
        <p className="text-sm text-muted-foreground">
          Lekcja przerobiona {inForm(feedback.form)} ({feedback.form}).
        </p>
      </div>

      <QuizReview results={result.results} />

      <QuizFeedbackPanel
        feedback={feedback}
        onRetryInForm={onRetryInForm}
        retryPending={retryPending}
      />

      <div className="flex flex-wrap gap-3 border-t pt-6">
        <Button variant="outline" onClick={onAgain}>
          <RotateCcwIcon data-icon="inline-start" />
          Rozwiąż jeszcze raz
        </Button>
        {unlocked && (
          <Link
            href={`/courses/${courseId}/lessons/${unlocked.id}`}
            className={cn(buttonVariants())}
          >
            Lekcja {unlocked.number}: {unlocked.title}
            <ArrowRightIcon data-icon="inline-end" />
          </Link>
        )}
        {feedback.course_completed && (
          <Link
            href={`/courses/${courseId}`}
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            Wróć do kursu
          </Link>
        )}
      </div>
    </div>
  );
}

/** "Sprawdź się": 5 questions drawn on the server, then the result and what it changed. */
export function LessonQuiz({
  lessonId,
  courseId,
  lastResult,
  onRetryInForm,
  retryPending,
  onResultChange,
}: LessonQuizProps) {
  const queryClient = useQueryClient();
  const quiz = useLessonQuiz(lessonId);
  const submit = useSubmitQuiz(lessonId, courseId);
  const sectionRef = useRef<HTMLElement>(null);

  function scrollToTop() {
    sectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  /** A new set of questions (the previous one is closed). */
  function newDraw() {
    void queryClient.resetQueries({ queryKey: lessonQuizKey(lessonId) });
    submit.reset();
    onResultChange?.(false);
    scrollToTop();
  }

  let body;
  if (quiz.isPending) {
    body = (
      <div className="flex justify-center py-6">
        <Spinner className="size-5" />
      </div>
    );
  } else if (quiz.isError) {
    body = (
      <div className="space-y-3">
        <p role="alert" className="text-sm text-destructive">
          Nie udało się wczytać pytań. {assessmentError(quiz.error)}
        </p>
        <Button variant="outline" onClick={() => quiz.refetch()}>
          Spróbuj ponownie
        </Button>
      </div>
    );
  } else if (quiz.data === null) {
    body = (
      <p className="text-muted-foreground">Ta lekcja nie ma jeszcze quizu.</p>
    );
  } else if (submit.data) {
    body = (
      <QuizResultView
        result={submit.data}
        courseId={courseId}
        onAgain={newDraw}
        onRetryInForm={onRetryInForm}
        retryPending={retryPending}
      />
    );
  } else {
    const draw = quiz.data;
    const closed =
      submit.error instanceof ApiError &&
      ["DRAW_NOT_OPEN", "QUIZ_ANSWER_MISMATCH"].includes(submit.error.code);
    body = (
      <div className="space-y-4">
        <QuizQuestions
          key={draw.draw_id}
          draw={draw}
          pending={submit.isPending}
          onSubmit={(answers) =>
            submit.mutate(
              { drawId: draw.draw_id, answers },
              {
                onSuccess: () => {
                  onResultChange?.(true);
                  scrollToTop();
                },
              },
            )
          }
        />
        {submit.isError && (
          <div className="space-y-3">
            <p role="alert" className="text-sm text-destructive">
              {assessmentError(submit.error)}
            </p>
            {closed && (
              <Button variant="outline" onClick={newDraw}>
                Wczytaj nowy zestaw pytań
              </Button>
            )}
          </div>
        )}
      </div>
    );
  }

  const poolSize = quiz.data?.pool_size;

  return (
    <section
      ref={sectionRef}
      id="quiz"
      aria-labelledby="quiz-title"
      className="scroll-mt-20 space-y-6 rounded-xl p-5 ring-1 ring-foreground/10 sm:px-9 sm:py-8"
    >
      <div className="space-y-1.5">
        <h2
          id="quiz-title"
          className="flex items-center gap-2 text-xl font-semibold"
        >
          <ListChecksIcon aria-hidden="true" className="size-5" />
          Sprawdź się
        </h2>
        <p className="text-sm text-muted-foreground">
          {questionsLabel(quiz.data?.questions.length ?? QUIZ_SIZE)}{" "}
          jednokrotnego wyboru
          {poolSize ? `, wylosowane z puli ${poolSize}` : ""}. Zaliczenie od{" "}
          {PASS_THRESHOLD}% otwiera następną lekcję. Po sprawdzeniu zobaczysz
          poprawne odpowiedzi z wyjaśnieniem.
        </p>
        {lastResult && !submit.data && (
          <p className="text-sm text-muted-foreground">
            Ostatni wynik w tej lekcji: {lastResult.percent}% (
            {lastResult.passed ? "zaliczone" : "niezaliczone"}, forma{" "}
            {formName(lastResult.form)}).
          </p>
        )}
      </div>
      {body}
    </section>
  );
}
