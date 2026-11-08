"use client";

import {
  ArrowDownIcon,
  ArrowUpIcon,
  PencilIcon,
  Trash2Icon,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useArchiveLesson, useReorderLessons } from "@/features/courses/hooks";
import type { Course, LessonSummary } from "@/features/courses/types";
import { errorMessage } from "@/shared/api/error-messages";
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

import { AddLessonForm } from "./AddLessonForm";
import { RenameLessonDialog } from "./RenameLessonDialog";

/** Ids in a new order: the lesson at `index` swapped with its neighbour. */
function moved(
  lessons: LessonSummary[],
  index: number,
  step: -1 | 1,
): number[] {
  const ids = lessons.map((lesson) => lesson.id);
  [ids[index], ids[index + step]] = [ids[index + step], ids[index]];
  return ids;
}

export function LessonList({ course }: { course: Course }) {
  const reorder = useReorderLessons(course.id);
  const archive = useArchiveLesson(course.id);
  const [renaming, setRenaming] = useState<LessonSummary | null>(null);
  const [removing, setRemoving] = useState<LessonSummary | null>(null);
  const { lessons } = course;

  function move(index: number, step: -1 | 1) {
    reorder.mutate(moved(lessons, index, step), {
      onError: (error) => toast.error(errorMessage(error)),
    });
  }

  return (
    <div className="space-y-4">
      {lessons.length === 0 ? (
        <p className="text-muted-foreground">
          Kurs nie ma jeszcze lekcji. Dodaj pierwszą poniżej.
        </p>
      ) : (
        <ol
          role="list"
          className="divide-y overflow-hidden rounded-xl ring-1 ring-foreground/10"
        >
          {lessons.map((lesson, index) => (
            <li
              key={lesson.id}
              className="flex items-center gap-3 py-1 pr-1 pl-4"
            >
              <span className="w-6 shrink-0 text-muted-foreground tabular-nums">
                {index + 1}.
              </span>
              <span className="min-w-0 flex-1 truncate font-medium">
                {lesson.title}
              </span>
              <div className="flex shrink-0">
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Przesuń wyżej: ${lesson.title}`}
                  title="Przesuń wyżej"
                  disabled={index === 0 || reorder.isPending}
                  onClick={() => move(index, -1)}
                >
                  <ArrowUpIcon />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Przesuń niżej: ${lesson.title}`}
                  title="Przesuń niżej"
                  disabled={index === lessons.length - 1 || reorder.isPending}
                  onClick={() => move(index, 1)}
                >
                  <ArrowDownIcon />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Zmień nazwę: ${lesson.title}`}
                  title="Zmień nazwę"
                  onClick={() => setRenaming(lesson)}
                >
                  <PencilIcon />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Usuń lekcję: ${lesson.title}`}
                  title="Usuń lekcję"
                  onClick={() => setRemoving(lesson)}
                >
                  <Trash2Icon />
                </Button>
              </div>
            </li>
          ))}
        </ol>
      )}

      <AddLessonForm courseId={course.id} />

      <RenameLessonDialog
        courseId={course.id}
        lesson={renaming}
        onClose={() => setRenaming(null)}
      />

      <AlertDialog
        open={removing !== null}
        onOpenChange={(open) => {
          if (!open) {
            setRemoving(null);
          }
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Usunąć lekcję?</AlertDialogTitle>
            <AlertDialogDescription>
              Lekcja „{removing?.title}” zniknie z kursu razem z treścią.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={archive.isPending}
              onClick={() =>
                removing &&
                archive.mutate(removing.id, {
                  onSuccess: () => {
                    toast.success(`Usunięto lekcję: ${removing.title}.`);
                    setRemoving(null);
                  },
                  onError: (error) => toast.error(errorMessage(error)),
                })
              }
            >
              {archive.isPending && <Spinner data-icon="inline-start" />}
              Usuń lekcję
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
