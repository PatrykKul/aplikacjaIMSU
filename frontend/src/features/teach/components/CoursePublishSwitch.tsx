"use client";

import { useState } from "react";
import { toast } from "sonner";

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
import { Spinner } from "@/shared/ui/spinner";
import { Switch } from "@/shared/ui/switch";

import { teachError } from "../errors";
import { useUpdateCourse } from "../hooks";
import type { TeacherCourse } from "../types";

// Publishing takes effect at once, so it only shows a toast. Unpublishing
// hides the course from the catalogue, so it asks for confirmation first.
// The server refuses a course without a published lesson (409), so the
// switch is off in that case and the course page explains why.
export function CoursePublishSwitch({ course }: { course: TeacherCourse }) {
  const updateCourse = useUpdateCourse(course.id);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const hasPublishedLesson = course.lessons.some((l) => l.is_published);
  const blocked = !course.is_published && !hasPublishedLesson;

  function save(isPublished: boolean) {
    updateCourse.mutate(
      { is_published: isPublished },
      {
        onSuccess: () => {
          toast.success(
            isPublished
              ? `Opublikowano kurs: ${course.title}. Uczniowie widzą go w katalogu.`
              : `Wycofano publikację kursu: ${course.title}.`,
          );
          setConfirmOpen(false);
        },
        onError: (error) => toast.error(teachError(error)),
      },
    );
  }

  return (
    <>
      <label className="flex min-h-control cursor-pointer items-center gap-3 text-sm font-medium has-disabled:cursor-not-allowed">
        <Switch
          checked={course.is_published}
          disabled={updateCourse.isPending || blocked}
          aria-describedby={blocked ? "course-publish-blocked" : undefined}
          onCheckedChange={(checked) => {
            if (checked) {
              save(true);
            } else {
              setConfirmOpen(true);
            }
          }}
        />
        Opublikowany
      </label>

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Wycofać publikację kursu?</AlertDialogTitle>
            <AlertDialogDescription>
              Kurs „{course.title}” zniknie z katalogu i nikt nowy się na niego
              nie zapisze. Uczniowie już przyjęci zachowają dostęp. Możesz go
              później opublikować ponownie.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={updateCourse.isPending}
              onClick={() => save(false)}
            >
              {updateCourse.isPending && <Spinner data-icon="inline-start" />}
              Wycofaj publikację
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
