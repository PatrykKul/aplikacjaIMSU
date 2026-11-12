"use client";

import { AlertCircleIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/shared/ui/alert-dialog";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { errorIssues, teachError } from "../errors";
import { useLessonReadiness, usePublishLesson } from "../hooks";
import type { IssueArea, TeacherLesson } from "../types";
import { IssueList } from "./IssueList";

type ReadinessPanelProps = {
  lesson: TeacherLesson;
  /** Unsaved changes in any tab: readiness describes the saved lesson only. */
  dirty: boolean;
  onShowArea: (area: IssueArea) => void;
};

/** Is the lesson complete (R11), and publishing / unpublishing it. */
export function ReadinessPanel({
  lesson,
  dirty,
  onShowArea,
}: ReadinessPanelProps) {
  const readiness = useLessonReadiness(lesson.id);
  const publish = usePublishLesson(lesson.id);
  const [confirmUnpublish, setConfirmUnpublish] = useState(false);

  function setPublished(isPublished: boolean) {
    publish.mutate(isPublished, {
      onSuccess: () => {
        toast.success(
          isPublished
            ? `Opublikowano lekcję: ${lesson.title}.`
            : `Wycofano publikację lekcji: ${lesson.title}.`,
        );
        setConfirmUnpublish(false);
      },
      onError: () => setConfirmUnpublish(false),
    });
  }

  const issues = readiness.data?.issues ?? [];
  const ready = readiness.data?.ready ?? false;

  let summary: string;
  if (lesson.is_published) {
    summary = "Opublikowana – uczniowie zapisani na kurs ją widzą.";
  } else if (readiness.isPending) {
    summary = "Szkic – sprawdzam, czego brakuje…";
  } else if (readiness.isError) {
    summary = "Szkic – nie udało się sprawdzić gotowości.";
  } else if (ready) {
    summary = "Szkic – wszystko gotowe do publikacji.";
  } else {
    summary = "Szkic – do publikacji brakuje:";
  }

  return (
    <section
      aria-labelledby="lesson-readiness"
      className="space-y-4 border-y py-5"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-1">
          <h2 id="lesson-readiness" className="text-lg font-semibold">
            Publikacja
          </h2>
          <p className="text-base" aria-live="polite">
            {summary}
          </p>
        </div>
        {lesson.is_published ? (
          <Button
            variant="outline"
            disabled={publish.isPending}
            onClick={() => setConfirmUnpublish(true)}
          >
            Wycofaj publikację
          </Button>
        ) : (
          <Button
            disabled={!ready || dirty || publish.isPending}
            onClick={() => setPublished(true)}
            aria-describedby={dirty ? "lesson-readiness-dirty" : undefined}
          >
            {publish.isPending && <Spinner data-icon="inline-start" />}
            Opublikuj lekcję
          </Button>
        )}
      </div>

      {!lesson.is_published && issues.length > 0 && (
        <IssueList issues={issues} onShowArea={onShowArea} />
      )}

      {dirty && (
        <p
          id="lesson-readiness-dirty"
          className="text-sm text-muted-foreground"
        >
          Masz niezapisane zmiany – gotowość dotyczy zapisanej lekcji. Zapisz
          zmiany, zanim opublikujesz lekcję.
        </p>
      )}

      {readiness.isError && (
        <Button variant="outline" size="sm" onClick={() => readiness.refetch()}>
          Sprawdź ponownie
        </Button>
      )}

      {publish.isError && (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>
            {lesson.is_published
              ? "Nie wycofano publikacji"
              : "Nie opublikowano lekcji"}
          </AlertTitle>
          <AlertDescription className="space-y-3">
            <p>{teachError(publish.error)}</p>
            {errorIssues(publish.error).length > 0 && (
              <IssueList
                issues={errorIssues(publish.error)}
                onShowArea={onShowArea}
              />
            )}
          </AlertDescription>
        </Alert>
      )}

      <AlertDialog open={confirmUnpublish} onOpenChange={setConfirmUnpublish}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Wycofać publikację lekcji?</AlertDialogTitle>
            <AlertDialogDescription>
              Uczniowie przestaną widzieć lekcję „{lesson.title}”, a w
              kolejności lekcji kursu zostanie ona pominięta. Wyniki uczniów
              zostaną zachowane.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={publish.isPending}
              onClick={() => setPublished(false)}
            >
              {publish.isPending && <Spinner data-icon="inline-start" />}
              Wycofaj publikację
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
