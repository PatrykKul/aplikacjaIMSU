"use client";

import { useState } from "react";
import { toast } from "sonner";

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
import { Spinner } from "@/shared/ui/spinner";
import { Switch } from "@/shared/ui/switch";

import { useSetPublished } from "../hooks";
import type { CourseSummary } from "../types";

// Publishing takes effect at once, so it only shows a toast. Unpublishing
// hides the course from every student, so it asks for confirmation first.
export function PublishSwitch({ course }: { course: CourseSummary }) {
  const setPublished = useSetPublished();
  const [confirmOpen, setConfirmOpen] = useState(false);

  function save(isPublished: boolean) {
    setPublished.mutate(
      { id: course.id, isPublished },
      {
        onSuccess: () => {
          toast.success(
            isPublished
              ? `Opublikowano kurs "${course.title}". Uczniowie już go widzą.`
              : `Wycofano publikację kursu "${course.title}".`,
          );
          setConfirmOpen(false);
        },
        onError: (error) => toast.error(errorMessage(error)),
      },
    );
  }

  return (
    <>
      <label className="flex min-h-control cursor-pointer items-center gap-3 text-sm font-medium">
        <Switch
          checked={course.is_published}
          disabled={setPublished.isPending}
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
            <AlertDialogTitle>Wycofać publikację?</AlertDialogTitle>
            <AlertDialogDescription>
              Uczniowie od razu przestaną widzieć kurs: {course.title}. Możesz
              go później opublikować ponownie.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={setPublished.isPending}
              onClick={() => save(false)}
            >
              {setPublished.isPending && <Spinner data-icon="inline-start" />}
              Wycofaj publikację
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
