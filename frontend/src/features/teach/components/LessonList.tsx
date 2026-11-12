"use client";

import {
  ArrowDownIcon,
  ArrowUpIcon,
  PencilIcon,
  Trash2Icon,
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { confirmLeave } from "@/shared/hooks/use-unsaved-changes-warning";
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

import { teachError } from "../errors";
import {
  useArchiveLesson,
  useLessonsReadiness,
  useReorderLessons,
} from "../hooks";
import { issuesSummary } from "../readiness";
import type { Readiness, TeacherCourse, TeacherLessonSummary } from "../types";
import { AddLessonForm } from "./AddLessonForm";
import { RenameLessonDialog } from "./RenameLessonDialog";

/** Ids in a new order: the lesson at `index` swapped with its neighbour. */
function moved(
  lessons: TeacherLessonSummary[],
  index: number,
  step: -1 | 1,
): number[] {
  const ids = lessons.map((lesson) => lesson.id);
  [ids[index], ids[index + step]] = [ids[index + step], ids[index]];
  return ids;
}

/** "Opublikowana" / "Szkic – brakuje: wersja K, 2 pytania" (R11). */
function LessonState({
  lesson,
  readiness,
}: {
  lesson: TeacherLessonSummary;
  readiness: Readiness | undefined;
}) {
  if (lesson.is_published) {
    return <span className="font-medium text-foreground">Opublikowana</span>;
  }
  if (!readiness) {
    return <span>Szkic</span>;
  }
  return (
    <span>
      {readiness.ready
        ? "Szkic – gotowa do publikacji"
        : `Szkic – brakuje: ${issuesSummary(readiness.issues)}`}
    </span>
  );
}

type LessonListProps = {
  course: TeacherCourse;
  /** Unsaved changes in the course form: confirm before opening a lesson. */
  dirty: boolean;
};

export function LessonList({ course, dirty }: LessonListProps) {
  const reorder = useReorderLessons(course.id);
  const archive = useArchiveLesson(course.id);
  const [renaming, setRenaming] = useState<TeacherLessonSummary | null>(null);
  const [removing, setRemoving] = useState<TeacherLessonSummary | null>(null);
  const { lessons } = course;
  const readiness = useLessonsReadiness(lessons.map((lesson) => lesson.id));

  function move(index: number, step: -1 | 1) {
    reorder.mutate(moved(lessons, index, step), {
      onError: (error) => toast.error(teachError(error)),
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
              className="flex items-center gap-3 py-2 pr-1 pl-4"
            >
              <span className="w-6 shrink-0 self-start pt-0.5 text-muted-foreground tabular-nums">
                {index + 1}.
              </span>
              <div className="min-w-0 flex-1">
                <Link
                  href={`/teach/courses/${course.id}/lessons/${lesson.id}`}
                  className="block truncate font-medium underline-offset-4 hover:underline"
                  onClick={(event) => {
                    if (!confirmLeave(dirty)) {
                      event.preventDefault();
                    }
                  }}
                >
                  {lesson.title}
                </Link>
                <p className="truncate text-sm text-muted-foreground">
                  <LessonState
                    lesson={lesson}
                    readiness={readiness[index]?.data}
                  />
                </p>
              </div>
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

      <RenameLessonDialog lesson={renaming} onClose={() => setRenaming(null)} />

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
              Lekcja „{removing?.title}” zniknie z kursu razem z trzema wersjami
              i pulą pytań.
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
                  onError: (error) => toast.error(teachError(error)),
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
