"use client";

import { PlusIcon, Trash2Icon } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/ui/card";
import { Input } from "@/shared/ui/input";
import { Label } from "@/shared/ui/label";
import { RadioGroup, RadioGroupItem } from "@/shared/ui/radio-group";
import { Textarea } from "@/shared/ui/textarea";

import { useSavePool } from "../hooks";
import { questionsCount } from "../readiness";
import {
  ANSWER_MAX,
  EXPLANATION_MAX,
  MAX_ANSWERS,
  MIN_ANSWERS,
  POOL_MAX,
  type PoolQuestion,
  QUESTION_MAX,
  QUIZ_SIZE,
} from "../types";
import { SaveBar } from "./SaveBar";
import { SaveErrorAlert } from "./SaveErrorAlert";

function newId(prefix: "q" | "a"): string {
  return `${prefix}-${crypto.randomUUID().slice(0, 8)}`;
}

function emptyQuestion(): PoolQuestion {
  const answers = Array.from({ length: MIN_ANSWERS }, () => ({
    id: newId("a"),
    text: "",
  }));
  return {
    id: newId("q"),
    text: "",
    answers,
    correct_answer_id: answers[0].id,
    explanation: "",
  };
}

type QuestionProblems = {
  text?: string;
  answers?: string;
  explanation?: string;
};

/** The same rules as the server (`assessment/schemas.py`), shown before saving. */
function problemsOf(question: PoolQuestion): QuestionProblems {
  const problems: QuestionProblems = {};
  if (!question.text.trim()) {
    problems.text = "Wpisz treść pytania.";
  }
  if (question.answers.some((answer) => !answer.text.trim())) {
    problems.answers = "Uzupełnij wszystkie odpowiedzi albo usuń pustą.";
  }
  if (!question.explanation.trim()) {
    problems.explanation =
      "Wpisz wyjaśnienie – uczeń zobaczy je po sprawdzeniu odpowiedzi.";
  }
  return problems;
}

function hasProblems(problems: QuestionProblems): boolean {
  return Object.keys(problems).length > 0;
}

type QuestionCardProps = {
  question: PoolQuestion;
  number: number;
  problems: QuestionProblems | null;
  onChange: (change: (q: PoolQuestion) => PoolQuestion) => void;
  onRemove: () => void;
};

function QuestionCard({
  question,
  number,
  problems,
  onChange,
  onRemove,
}: QuestionCardProps) {
  const base = `pool-${question.id}`;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <CardTitle className="text-base">Pytanie {number}</CardTitle>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Usuń pytanie ${number}`}
          title="Usuń pytanie"
          onClick={onRemove}
        >
          <Trash2Icon />
        </Button>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="space-y-2">
          <Label htmlFor={`${base}-text`}>Treść pytania</Label>
          <Textarea
            id={`${base}-text`}
            rows={2}
            value={question.text}
            maxLength={QUESTION_MAX}
            aria-invalid={problems?.text ? true : undefined}
            aria-describedby={problems?.text ? `${base}-text-error` : undefined}
            onChange={(event) =>
              onChange((q) => ({ ...q, text: event.target.value }))
            }
          />
          {problems?.text && (
            <p id={`${base}-text-error`} className="text-sm text-destructive">
              {problems.text}
            </p>
          )}
        </div>

        <fieldset className="space-y-2">
          <legend id={`${base}-answers`} className="mb-2 text-sm font-medium">
            Odpowiedzi – zaznacz poprawną
          </legend>
          <RadioGroup
            aria-labelledby={`${base}-answers`}
            value={question.correct_answer_id}
            onValueChange={(value) =>
              onChange((q) => ({ ...q, correct_answer_id: value as string }))
            }
          >
            {question.answers.map((answer, index) => (
              <div key={answer.id} className="flex items-center gap-3">
                <RadioGroupItem
                  value={answer.id}
                  aria-label={`Odpowiedź ${index + 1} jest poprawna`}
                />
                <Input
                  value={answer.text}
                  maxLength={ANSWER_MAX}
                  aria-label={`Odpowiedź ${index + 1}`}
                  aria-invalid={
                    problems?.answers && !answer.text.trim() ? true : undefined
                  }
                  className={cn(
                    answer.id === question.correct_answer_id && "font-medium",
                  )}
                  onChange={(event) =>
                    onChange((q) => ({
                      ...q,
                      answers: q.answers.map((item) =>
                        item.id === answer.id
                          ? { ...item, text: event.target.value }
                          : item,
                      ),
                    }))
                  }
                />
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Usuń odpowiedź ${index + 1}`}
                  title="Usuń odpowiedź"
                  disabled={question.answers.length <= MIN_ANSWERS}
                  onClick={() =>
                    onChange((q) => {
                      const answers = q.answers.filter(
                        (item) => item.id !== answer.id,
                      );
                      const correct =
                        q.correct_answer_id === answer.id
                          ? answers[0].id
                          : q.correct_answer_id;
                      return { ...q, answers, correct_answer_id: correct };
                    })
                  }
                >
                  <Trash2Icon />
                </Button>
              </div>
            ))}
          </RadioGroup>
          {problems?.answers && (
            <p className="text-sm text-destructive">{problems.answers}</p>
          )}
          {question.answers.length < MAX_ANSWERS && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() =>
                onChange((q) => ({
                  ...q,
                  answers: [...q.answers, { id: newId("a"), text: "" }],
                }))
              }
            >
              <PlusIcon data-icon="inline-start" />
              Dodaj odpowiedź
            </Button>
          )}
        </fieldset>

        <div className="space-y-2">
          <Label htmlFor={`${base}-explanation`}>Wyjaśnienie</Label>
          <Textarea
            id={`${base}-explanation`}
            rows={3}
            value={question.explanation}
            maxLength={EXPLANATION_MAX}
            aria-invalid={problems?.explanation ? true : undefined}
            aria-describedby={`${base}-explanation-hint`}
            onChange={(event) =>
              onChange((q) => ({ ...q, explanation: event.target.value }))
            }
          />
          <p
            id={`${base}-explanation-hint`}
            className={cn(
              "text-sm",
              problems?.explanation
                ? "text-destructive"
                : "text-muted-foreground",
            )}
          >
            {problems?.explanation ??
              "Dlaczego poprawna odpowiedź jest poprawna. Uczeń zobaczy to po sprawdzeniu quizu."}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

type PoolEditorProps = {
  lessonId: number;
  initial: PoolQuestion[];
  onDirtyChange: (dirty: boolean) => void;
};

/** The question pool of a lesson: each attempt draws 5 questions from it (R9). */
export function PoolEditor({
  lessonId,
  initial,
  onDirtyChange,
}: PoolEditorProps) {
  const save = useSavePool(lessonId);
  const [questions, setQuestions] = useState<PoolQuestion[]>(initial);
  const [dirty, setDirty] = useState(false);
  const [showProblems, setShowProblems] = useState(false);

  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);

  function edit(next: PoolQuestion[]) {
    setQuestions(next);
    setDirty(true);
    save.reset();
  }

  function update(index: number, change: (q: PoolQuestion) => PoolQuestion) {
    edit(questions.map((q, i) => (i === index ? change(q) : q)));
  }

  function onSave() {
    if (questions.some((q) => hasProblems(problemsOf(q)))) {
      setShowProblems(true);
      toast.error("Uzupełnij zaznaczone pola pytań przed zapisaniem.");
      return;
    }
    const trimmed = questions.map((q) => ({
      ...q,
      text: q.text.trim(),
      explanation: q.explanation.trim(),
      answers: q.answers.map((a) => ({ ...a, text: a.text.trim() })),
    }));
    save.mutate(trimmed, {
      onSuccess: (saved) => {
        setQuestions(saved.questions);
        setDirty(false);
        setShowProblems(false);
        toast.success("Zapisano pulę pytań.");
      },
    });
  }

  const count = questions.length;
  const enough = count >= QUIZ_SIZE;

  return (
    <div className="space-y-6">
      <SaveBar
        label="Zapisz pulę"
        dirty={dirty}
        pending={save.isPending}
        onSave={onSave}
      >
        <span className="font-medium">
          {questionsCount(count)} w puli (min. {QUIZ_SIZE})
        </span>
        {!enough && (
          <span className="text-muted-foreground">
            {" "}
            · brakuje {QUIZ_SIZE - count}
          </span>
        )}
      </SaveBar>

      {save.isError && <SaveErrorAlert error={save.error} />}

      <p className="max-w-[65ch] text-base text-muted-foreground">
        Każde podejście losuje {QUIZ_SIZE} pytań z puli, przy powtórce najpierw
        te, których uczeń jeszcze nie widział. Pytania są wspólne dla wszystkich
        wersji lekcji. Pytanie ma 3–4 odpowiedzi, jedną poprawną i wyjaśnienie.
      </p>

      {count === 0 ? (
        <p className="text-muted-foreground">
          Pula jest pusta. Dodaj co najmniej {QUIZ_SIZE} pytań, żeby lekcję
          można było opublikować.
        </p>
      ) : (
        <ol role="list" className="space-y-5">
          {questions.map((question, index) => {
            const problems = showProblems ? problemsOf(question) : null;
            return (
              <li key={question.id}>
                <QuestionCard
                  question={question}
                  number={index + 1}
                  problems={problems && hasProblems(problems) ? problems : null}
                  onChange={(change) => update(index, change)}
                  onRemove={() => edit(questions.filter((_, i) => i !== index))}
                />
              </li>
            );
          })}
        </ol>
      )}

      {count < POOL_MAX ? (
        <Button
          variant="outline"
          onClick={() => edit([...questions, emptyQuestion()])}
        >
          <PlusIcon data-icon="inline-start" />
          Dodaj pytanie
        </Button>
      ) : (
        <p className="text-sm text-muted-foreground">
          Pula może mieć najwyżej {POOL_MAX} pytań.
        </p>
      )}
    </div>
  );
}
