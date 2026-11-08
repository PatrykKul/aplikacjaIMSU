"use client";

import { useRouter } from "next/navigation";
import { toast } from "sonner";

import { useArchiveCourse } from "@/features/courses/hooks";
import type { Course } from "@/features/courses/types";
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
  AlertDialogTrigger,
} from "@/shared/ui/alert-dialog";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

export function ArchiveCourseSection({ course }: { course: Course }) {
  const router = useRouter();
  const archive = useArchiveCourse(course.id);

  return (
    <section
      aria-labelledby="course-archive"
      className="space-y-3 border-t pt-6"
    >
      <h2 id="course-archive" className="text-xl font-semibold">
        Usuwanie kursu
      </h2>
      <p className="max-w-[65ch] text-muted-foreground">
        Usunięty kurs znika z Twojej listy, a uczniowie przestają go widzieć.
      </p>
      <AlertDialog>
        <AlertDialogTrigger render={<Button variant="destructive" />}>
          Usuń kurs
        </AlertDialogTrigger>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Usunąć kurs?</AlertDialogTitle>
            <AlertDialogDescription>
              Kurs „{course.title}” zniknie z Twojej listy razem z lekcjami.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Anuluj</AlertDialogCancel>
            <AlertDialogAction
              variant="destructive"
              disabled={archive.isPending}
              onClick={() =>
                archive.mutate(undefined, {
                  onSuccess: () => {
                    toast.success(`Usunięto kurs: ${course.title}.`);
                    router.replace("/teach");
                  },
                  onError: (error) => toast.error(errorMessage(error)),
                })
              }
            >
              {archive.isPending && <Spinner data-icon="inline-start" />}
              Usuń kurs
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </section>
  );
}
