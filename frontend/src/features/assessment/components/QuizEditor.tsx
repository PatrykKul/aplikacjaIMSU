"use client";

import { ArrowLeftIcon, PlusIcon, Trash2Icon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { useLesson } from "@/features/courses/hooks";
import { FORM_LABELS, FORMS, type Form } from "@/features/content/types";
import { PageMessage } from "@/shared/layout/page-states";
import { useUnsavedChangesWarning } from "@/shared/hooks/use-unsaved-changes-warning";
import { Button, buttonVariants } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";

import { assessmentError } from "../errors";
import { useDeleteQuiz, useQuizForEditing, useSaveQuiz } from "../hooks";
import {
  MAX_ANSWERS,
  MAX_QUESTIONS,
  MIN_ANSWERS,
  type QuizQuestion,
  newQuizId,
  questionsLabel,
} from "../types";

function emptyQuestion(): QuizQuestion {
  const answers = Array.from({ length: MIN_ANSWERS }, () => ({
    id: newQuizId("a"),
    text: "",
  }));
  return {
    id: newQuizId("q"),
    text: "",
    form: null,
    answers,
    correct_answer_id: answers[0].id,
  };
}

/** Problems shown before saving (the server validates the same rules). */
function problems(questions: QuizQuestion[]): string[] {
  const list: string[] = [];
  questions.forEach((q, i) => {
    if (!q.text.trim()) list.push(`Pytanie ${i + 1}: wpisz treść pytania.`);
    if (q.answers.some((a) => !a.text.trim()))
      list.push(`Pytanie ${i + 1}: uzupełnij wszystkie odpowiedzi.`);
  });
  return list;
}

type EditorProps = {
  lessonId: number;
  initial: QuizQuestion[];
  previewHref: string;
};

function Editor({ lessonId, initial, previewHref }: EditorProps) {
  const [questions, setQuestions] = useState<QuizQuestion[]>(
    initial.length > 0 ? initial : [emptyQuestion()],
  );
  const [dirty, setDirty] = useState(initial.length === 0);
  const [showProblems, setShowProblems] = useState(false);
  const save = useSaveQuiz(lessonId);
  const remove = useDeleteQuiz(lessonId);
  useUnsavedChangesWarning(dirty);

  function update(index: number, change: (q: QuizQuestion) => QuizQuestion) {
    setQuestions((prev) => prev.map((q, i) => (i === index ? change(q) : q)));
    setDirty(true);
    save.reset();
  }

  function handleSave() {
    if (problems(questions).length > 0) {
      setShowProblems(true);
      return;
    }
    save.mutate(questions, { onSuccess: () => setDirty(false) });
  }

  const found = problems(questions);

  return (
    <div className="space-y-5">
      <ol className="space-y-5">
        {questions.map((question, index) => (
          <li key={question.id}>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-2">
                <CardTitle className="text-base">Pytanie {index + 1}</CardTitle>
                <Button
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Usuń pytanie ${index + 1}`}
                  disabled={questions.length === 1}
                  onClick={() => {
                    setQuestions((prev) => prev.filter((_, i) => i !== index));
                    setDirty(true);
                  }}
                >
                  <Trash2Icon />
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <label className="block space-y-1.5 text-sm font-medium">
                  Treść pytania
                  <Input
                    value={question.text}
                    maxLength={500}
                    onChange={(e) =>
                      update(index, (q) => ({ ...q, text: e.target.value }))
                    }
                  />
                </label>
                <label className="block space-y-1.5 text-sm font-medium">
                  Dotyczy materiału
                  <select
                    className="block h-control w-full rounded-lg border bg-background px-3 text-sm"
                    value={question.form ?? ""}
                    onChange={(e) =>
                      update(index, (q) => ({
                        ...q,
                        form: (e.target.value || null) as Form | null,
                      }))
                    }
                  >
                    <option value="">
                      Wspólnego – pytanie widzi każdy uczeń
                    </option>
                    {FORMS.map((form) => (
                      <option key={form} value={form}>
                        {FORM_LABELS[form]} – widzą tylko uczniowie tego stylu
                      </option>
                    ))}
                  </select>
                </label>
                <fieldset className="space-y-2">
                  <legend className="text-sm font-medium">
                    Odpowiedzi (zaznacz poprawną)
                  </legend>
                  {question.answers.map((answer, a) => (
                    <div key={answer.id} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name={`correct-${question.id}`}
                        aria-label={`Odpowiedź ${a + 1} jest poprawna`}
                        checked={question.correct_answer_id === answer.id}
                        onChange={() =>
                          update(index, (q) => ({
                            ...q,
                            correct_answer_id: answer.id,
                          }))
                        }
                        className="size-4 accent-primary"
                      />
                      <Input
                        value={answer.text}
                        maxLength={200}
                        aria-label={`Odpowiedź ${a + 1}`}
                        onChange={(e) =>
                          update(index, (q) => ({
                            ...q,
                            answers: q.answers.map((x) =>
                              x.id === answer.id
                                ? { ...x, text: e.target.value }
                                : x,
                            ),
                          }))
                        }
                      />
                      <Button
                        variant="ghost"
                        size="icon-sm"
                        aria-label={`Usuń odpowiedź ${a + 1}`}
                        disabled={question.answers.length <= MIN_ANSWERS}
                        onClick={() =>
                          update(index, (q) => {
                            const answers = q.answers.filter(
                              (x) => x.id !== answer.id,
                            );
                            const correct =
                              q.correct_answer_id === answer.id
                                ? answers[0].id
                                : q.correct_answer_id;
                            return {
                              ...q,
                              answers,
                              correct_answer_id: correct,
                            };
                          })
                        }
                      >
                        <Trash2Icon />
                      </Button>
                    </div>
                  ))}
                  {question.answers.length < MAX_ANSWERS && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() =>
                        update(index, (q) => ({
                          ...q,
                          answers: [
                            ...q.answers,
                            { id: newQuizId("a"), text: "" },
                          ],
                        }))
                      }
                    >
                      <PlusIcon data-icon="inline-start" />
                      Dodaj odpowiedź
                    </Button>
                  )}
                </fieldset>
              </CardContent>
            </Card>
          </li>
        ))}
      </ol>

      {questions.length < MAX_QUESTIONS && (
        <Button
          variant="outline"
          onClick={() => {
            setQuestions((prev) => [...prev, emptyQuestion()]);
            setDirty(true);
          }}
        >
          <PlusIcon data-icon="inline-start" />
          Dodaj pytanie
        </Button>
      )}

      {showProblems && found.length > 0 && (
        <ul
          role="alert"
          className="list-disc space-y-1 pl-5 text-sm text-destructive"
        >
          {found.map((p) => (
            <li key={p}>{p}</li>
          ))}
        </ul>
      )}
      {(save.error ?? remove.error) && (
        <p role="alert" className="text-sm text-destructive">
          {assessmentError(save.error ?? remove.error)}
        </p>
      )}

      <div className="sticky bottom-0 flex flex-wrap items-center gap-3 border-t bg-background py-3">
        <Button onClick={handleSave} disabled={save.isPending}>
          {save.isPending && <Spinner data-icon="inline-start" />}
          Zapisz quiz ({questionsLabel(questions.length)})
        </Button>
        <span className="text-sm text-muted-foreground" aria-live="polite">
          {dirty ? "Niezapisane zmiany" : save.isSuccess ? "Zapisano" : ""}
        </span>
        <Link
          href={previewHref}
          className={buttonVariants({ variant: "ghost" })}
        >
          Podgląd lekcji z quizem
        </Link>
        {initial.length > 0 && (
          <Button
            variant="ghost"
            className="ml-auto text-destructive"
            disabled={remove.isPending}
            onClick={() => {
              if (window.confirm("Usunąć quiz z tej lekcji?")) {
                remove.mutate(undefined, {
                  onSuccess: () => {
                    setQuestions([emptyQuestion()]);
                    setDirty(true);
                  },
                });
              }
            }}
          >
            Usuń quiz
          </Button>
        )}
      </div>
    </div>
  );
}

type QuizEditorProps = { courseId: number; lessonId: number };

export function QuizEditor({ courseId, lessonId }: QuizEditorProps) {
  const lesson = useLesson(lessonId);
  const quiz = useQuizForEditing(lessonId);
  const lessonEditHref = `/teach/courses/${courseId}/lessons/${lessonId}`;
  const previewHref = `/courses/${courseId}/lessons/${lessonId}#quiz`;

  if (lesson.isPending || quiz.isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (lesson.isError || quiz.isError || lesson.data.course.id !== courseId) {
    return (
      <PageMessage
        title="Nie można edytować quizu"
        description={assessmentError(lesson.error ?? quiz.error)}
        action={
          <Link
            href="/teach"
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć do moich kursów
          </Link>
        }
      />
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="space-y-2">
        <Link
          href={lessonEditHref}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeftIcon className="size-4" />
          {lesson.data.title}
        </Link>
        <h1 className="text-2xl font-semibold tracking-tight">
          Quiz do lekcji
        </h1>
        <p className="text-sm text-muted-foreground">
          Pytania jednokrotnego wyboru (3–4 odpowiedzi). Pytanie o materiał
          wzrokowy, słuchowy albo kinestetyczny zobaczą tylko uczniowie, którzy
          ten materiał mają w lekcji. Wynik quizu zmienia wagi stylów ucznia.
        </p>
      </div>
      <Editor
        // Keyed by lesson only: saving updates the cache and must not remount the editor
        // (that would drop the "Zapisano" status and the local edit state)
        key={lessonId}
        lessonId={lessonId}
        initial={quiz.data.questions}
        previewHref={previewHref}
      />
    </div>
  );
}
