"use client";

import { type ReactNode, useEffect, useRef, useState } from "react";

import { Button } from "@/shared/ui/button";

import type { Lesson } from "../types";
import { LessonHeader } from "./LessonHeader";
import { LessonSummary } from "./LessonSummary";
import { QuestionStep } from "./QuestionStep";
import { StepCard } from "./StepCard";
import { TextStep } from "./TextStep";

type LessonPlayerProps = {
  lesson: Lesson;
  courseHref: string;
  context: string;
  goal: string;
  nextHref: string | null;
  methodSelect?: ReactNode;
};

// Steps appear one by one and stay on the page, so the finished lesson reads
// as whole. State lives only here: reload starts lesson again.
export function LessonPlayer({
  lesson,
  courseHref,
  context,
  goal,
  nextHref,
  methodSelect,
}: LessonPlayerProps) {
  const steps = lesson.steps;
  const questionKeys = steps.flatMap((step) =>
    step.type === "question" ? [step.key] : [],
  );

  // Number of revealed step
  const [shown, setShown] = useState(1);
  // Questions answered (correctly or revealed)
  const [answered, setAnswered] = useState<Record<string, boolean>>({});
  const [finished, setFinished] = useState(false);

  const stepRefs = useRef<(HTMLDivElement | null)[]>([]);
  const summaryRef = useRef<HTMLDivElement>(null);

  // Move to the step that just appeared
  useEffect(() => {
    if (shown === 1 && !finished) {
      return;
    }
    const target = finished ? summaryRef.current : stepRefs.current[shown - 1];
    const reduceMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    target?.focus({ preventScroll: true });
    target?.scrollIntoView({
      behavior: reduceMotion ? "auto" : "smooth",
      block: "start",
    });
  }, [shown, finished]);

  function goNext() {
    if (shown < steps.length) {
      setShown(shown + 1);
    } else {
      setFinished(true);
    }
  }

  const isLast = shown === steps.length;
  const nextButton = (
    <Button onClick={goNext}>{isLast ? "Zakończ lekcję" : "Dalej"}</Button>
  );
  const completed = finished ? steps.length : shown - 1;
  const firstTry = Object.values(answered).filter(Boolean).length;

  return (
    <>
      <LessonHeader
        courseHref={courseHref}
        context={context}
        title={lesson.title}
        step={finished ? steps.length : shown}
        total={steps.length}
        progress={completed / steps.length}
        methodSelect={methodSelect}
      />
      {/* Bottom padding lets newest step scroll up to the top */}
      <main className="mx-auto w-full max-w-3xl space-y-5 px-3 pt-6 pb-[50svh] sm:px-4 sm:pt-8">
        {steps.slice(0, shown).map((step, index) => {
          const current = index === shown - 1 && !finished;
          return (
            <StepCard
              key={step.key}
              ref={(element) => {
                stepRefs.current[index] = element;
              }}
              active={current}
              label={
                step.type === "question"
                  ? `Pytanie ${questionKeys.indexOf(step.key) + 1} z ${questionKeys.length}`
                  : undefined
              }
            >
              {step.type === "text" ? (
                <>
                  <TextStep step={step} />
                  {current && nextButton}
                </>
              ) : (
                <QuestionStep
                  lessonId={lesson.id}
                  step={step}
                  onComplete={(first) =>
                    setAnswered((previous) => ({
                      ...previous,
                      [step.key]: first,
                    }))
                  }
                  next={current ? nextButton : undefined}
                />
              )}
            </StepCard>
          );
        })}
        {finished && (
          <StepCard ref={summaryRef} active>
            <LessonSummary
              firstTry={firstTry}
              questions={questionKeys.length}
              goal={goal}
              courseHref={courseHref}
              nextHref={nextHref}
            />
          </StepCard>
        )}
      </main>
    </>
  );
}
