"use client";

import { useRef, useState } from "react";

import { LessonQuiz } from "@/features/assessment/components/LessonQuiz";
import type { Form } from "@/features/content/types";
import { LessonFormBar } from "@/features/learning-style/components/LessonFormBar";
import { RetrySuggestionBox } from "@/features/learning-style/components/RetrySuggestionBox";
import { learningStyleError } from "@/features/learning-style/errors";
import { formName } from "@/features/learning-style/explain";
import { useChangeLessonForm, useStudy } from "@/features/learning-style/hooks";
import { ApiError } from "@/shared/api/client";
import { Spinner } from "@/shared/ui/spinner";

import { useLesson } from "../hooks";
import { BlockList, LessonNav, LessonSection } from "./LessonParts";
import { LessonHeader } from "./LessonHeader";
import { LessonMessage } from "./LessonMessage";

type LessonStudyProps = { courseId: number; lessonId: number };

/** A lesson as the student studies it: one version in one form, then the quiz. */
export function LessonStudy({ courseId, lessonId }: LessonStudyProps) {
  const lesson = useLesson(lessonId);
  const study = useStudy(lessonId);
  const changeForm = useChangeLessonForm(lessonId);
  // A new round of the quiz (new questions) after every change of the form
  const [round, setRound] = useState(0);
  const [resultShown, setResultShown] = useState(false);
  const versionRef = useRef<HTMLDivElement>(null);

  function switchForm(form: Form, source: "manual" | "suggestion") {
    changeForm.mutate(
      { form, source },
      {
        onSuccess: () => {
          setRound((value) => value + 1);
          setResultShown(false);
          versionRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          });
        },
      },
    );
  }

  if (lesson.isPending || study.isPending) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner className="size-8" />
      </div>
    );
  }
  if (lesson.isError || study.isError) {
    return (
      <LessonMessage
        error={lesson.error ?? study.error}
        courseId={courseId}
        onRetry={() => {
          void lesson.refetch();
          void study.refetch();
        }}
      />
    );
  }
  if (lesson.data.course.id !== courseId) {
    return (
      <LessonMessage
        error={new ApiError(404, "LESSON_NOT_FOUND")}
        courseId={courseId}
        onRetry={() => lesson.refetch()}
      />
    );
  }

  const data = lesson.data;
  const courseHref = `/courses/${courseId}`;
  const suggestion = study.data.suggestion;
  const showSuggestion =
    suggestion !== null &&
    suggestion.suggested.form !== study.data.form &&
    !resultShown;

  return (
    <>
      <LessonHeader
        courseHref={courseHref}
        courseTitle={data.course.title}
        title={`${data.number}. ${data.title}`}
      />
      <main className="mx-auto w-full max-w-3xl flex-1 space-y-10 px-4 py-8 sm:px-6">
        <LessonSection id="lesson-outline" title="Zarys" doc={data.outline} />

        <div ref={versionRef} className="scroll-mt-20 space-y-5">
          <LessonFormBar
            study={study.data}
            pending={changeForm.isPending}
            onChange={(form) => switchForm(form, "manual")}
          />
          {changeForm.isError && (
            <p role="alert" className="text-sm text-destructive">
              {learningStyleError(changeForm.error)}
            </p>
          )}
          {showSuggestion && (
            <RetrySuggestionBox
              suggestion={suggestion}
              pending={changeForm.isPending}
              onRetry={(form) => switchForm(form, "suggestion")}
            />
          )}
          <BlockList
            blocks={study.data.blocks}
            label={`Treść lekcji – forma ${formName(study.data.form)}`}
          />
        </div>

        <LessonSection
          id="lesson-conclusions"
          title="Wnioski"
          doc={data.conclusions}
        />

        <LessonQuiz
          key={round}
          lessonId={lessonId}
          courseId={courseId}
          lastResult={study.data.last_result}
          onResultChange={setResultShown}
          retryPending={changeForm.isPending}
          onRetryInForm={(form) => switchForm(form, "suggestion")}
        />

        <LessonNav lesson={data} courseHref={courseHref} />
      </main>
    </>
  );
}
