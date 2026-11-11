"use client";

import { CheckIcon, ListChecksIcon, PencilIcon, XIcon } from "lucide-react";
import Link from "next/link";
import { type FormEvent, useState } from "react";

import { FORM_LABELS } from "@/features/content/types";
import { AdaptationFeedback } from "@/features/learning-style/components/AdaptationFeedback";
import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";
import { Button, buttonVariants } from "@/shared/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group";
import { Spinner } from "@/shared/ui/spinner";

import { assessmentError } from "../errors";
import { useLessonQuiz, useSubmitQuiz } from "../hooks";
import { type QuestionResult, questionsLabel } from "../types";

type LessonQuizProps = {
  lessonId: number;
  /** Link to the quiz editor, shown to the lesson's author. */
  editHref?: string;
};

/** Quiz under a lesson: answers are scored on the server, then the adaptation reacts. */
export function LessonQuiz({ lessonId, editHref }: LessonQuizProps) {
  const quiz = useLessonQuiz(lessonId);
  const submit = useSubmitQuiz(lessonId);
  const [chosen, setChosen] = useState<Record<string, string>>({});

  if (quiz.isPending) {
    return (
      <div className="flex justify-center py-6">
        <Spinner className="size-5" />
      </div>
    );
  }
  if (quiz.isError) {
    return (
      <p className="text-sm text-destructive">
        Nie udało się wczytać quizu. {assessmentError(quiz.error)}
      </p>
    );
  }
  if (quiz.data === null) {
    return editHref ? (
      <Card>
        <CardHeader>
          <CardTitle>Quiz</CardTitle>
          <CardDescription>Ta lekcja nie ma jeszcze quizu.</CardDescription>
        </CardHeader>
        <CardContent>
          <Link
            href={editHref}
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            <PencilIcon data-icon="inline-start" />
            Dodaj quiz
          </Link>
        </CardContent>
      </Card>
    ) : null;
  }

  const questions = quiz.data.questions;
  const result = submit.data;
  const resultFor = new Map<string, QuestionResult>(
    (result?.results ?? []).map((r) => [r.question_id, r]),
  );
  const complete = questions.every((q) => chosen[q.id] !== undefined);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (complete) {
      submit.mutate(chosen);
    }
  }

  function retry() {
    setChosen({});
    submit.reset();
  }

  return (
    <Card id="quiz">
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2">
          <ListChecksIcon className="size-5" aria-hidden="true" />
          Sprawdź się
        </CardTitle>
        <CardDescription>
          {questionsLabel(questions.length)} jednokrotnego wyboru. Po
          sprawdzeniu zobaczysz poprawne odpowiedzi.
          {quiz.data.hidden_count > 0 &&
            " Pytania dotyczą materiałów, które widzisz w tej lekcji."}
        </CardDescription>
        {editHref && (
          <Link
            href={editHref}
            className="text-sm font-medium underline underline-offset-4"
          >
            Edytuj quiz
          </Link>
        )}
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-5">
          <ol className="space-y-5">
            {questions.map((question, index) => {
              const checked = resultFor.get(question.id);
              return (
                <li key={question.id}>
                  <fieldset className="space-y-2" disabled={!!result}>
                    <legend
                      id={`quiz-${question.id}-text`}
                      className="flex flex-wrap items-center gap-2 font-medium"
                    >
                      {index + 1}. {question.text}
                      {question.form && (
                        <Badge variant="outline">
                          {FORM_LABELS[question.form]}
                        </Badge>
                      )}
                    </legend>
                    <RadioGroup
                      aria-labelledby={`quiz-${question.id}-text`}
                      disabled={!!result}
                      value={chosen[question.id] ?? null}
                      onValueChange={(value) =>
                        setChosen((prev) => ({
                          ...prev,
                          [question.id]: value as string,
                        }))
                      }
                    >
                      {question.answers.map((answer) => {
                        const isChosen = chosen[question.id] === answer.id;
                        const isCorrect =
                          checked?.correct_answer_id === answer.id;
                        const isWrong = checked && isChosen && !checked.correct;
                        return (
                          <label
                            key={answer.id}
                            className={cn(
                              "flex min-h-control items-center gap-3 rounded-lg border px-3 py-2.5 text-sm transition-colors",
                              !result && "cursor-pointer hover:bg-muted/50",
                              isChosen &&
                                !result &&
                                "border-primary bg-primary/5",
                              isCorrect &&
                                "border-feedback-correct-foreground/50 bg-feedback-correct",
                              isWrong &&
                                "border-feedback-incorrect-foreground/50 bg-feedback-incorrect",
                            )}
                          >
                            <RadioGroupItem value={answer.id} />
                            <span className="flex-1">{answer.text}</span>
                            {isCorrect && (
                              <CheckIcon
                                className="size-4 text-feedback-correct-foreground"
                                aria-label="poprawna odpowiedź"
                              />
                            )}
                            {isWrong && (
                              <XIcon
                                className="size-4 text-feedback-incorrect-foreground"
                                aria-label="błędna odpowiedź"
                              />
                            )}
                          </label>
                        );
                      })}
                    </RadioGroup>
                  </fieldset>
                </li>
              );
            })}
          </ol>

          {submit.isError && (
            <p role="alert" className="text-sm text-destructive">
              {assessmentError(submit.error)}
            </p>
          )}

          {result ? (
            <div className="space-y-4" aria-live="polite">
              <p className="text-lg font-semibold">
                Wynik: {result.correct_count} / {result.total} ({result.percent}
                %)
              </p>
              {result.adaptation && (
                <AdaptationFeedback feedback={result.adaptation} />
              )}
              <Button type="button" variant="outline" onClick={retry}>
                Rozwiąż jeszcze raz
              </Button>
            </div>
          ) : (
            <Button type="submit" disabled={!complete || submit.isPending}>
              {submit.isPending && <Spinner data-icon="inline-start" />}
              {complete
                ? "Sprawdź odpowiedzi"
                : "Odpowiedz na wszystkie pytania"}
            </Button>
          )}
        </form>
      </CardContent>
    </Card>
  );
}
