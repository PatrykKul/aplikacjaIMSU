import { ArrowRightIcon, CheckIcon } from "lucide-react";
import Link from "next/link";

import type { ReviewQuestion } from "../types";

/** "Do powtórki": the question, the correct answer, the explanation and the lesson. */
export function ReviewQuestions({
  questions,
}: {
  questions: ReviewQuestion[];
}) {
  if (questions.length === 0) {
    return <p className="text-muted-foreground">Nie masz pytań do powtórki.</p>;
  }
  return (
    <ol role="list" className="divide-y border-y">
      {questions.map((question) => (
        <li
          key={`${question.lesson_id}-${question.question_id}`}
          className="space-y-2 py-4"
        >
          <p className="font-medium text-pretty">{question.text}</p>
          <p className="flex gap-2">
            <CheckIcon
              aria-hidden="true"
              className="mt-1 size-4 shrink-0 text-feedback-correct-foreground"
            />
            <span>
              <span className="text-muted-foreground">
                Poprawna odpowiedź:{" "}
              </span>
              <span className="font-medium">
                {question.correct_answer.text}
              </span>
            </span>
          </p>
          <p className="max-w-[65ch] text-sm text-pretty">
            <span className="font-medium">Wyjaśnienie: </span>
            {question.explanation}
          </p>
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 pt-1 text-sm">
            <span className="text-muted-foreground">
              {question.course_title} · Lekcja
              {question.number !== null && ` ${question.number}`}:{" "}
              {question.lesson_title}
            </span>
            <Link
              href={`/courses/${question.course_id}/lessons/${question.lesson_id}`}
              className="inline-flex items-center gap-1 font-medium text-primary underline-offset-4 hover:underline"
            >
              Wróć do lekcji
              <ArrowRightIcon aria-hidden="true" className="size-3.5" />
            </Link>
          </div>
        </li>
      ))}
    </ol>
  );
}
