"use client";

import Link from "next/link";
import { toast } from "sonner";

import { classroomsError } from "@/features/classes/errors";
import { useAssignCourse } from "@/features/classes/hooks";
import type { Classroom } from "@/features/classes/types";
import { useCourses } from "@/features/courses/hooks";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { Spinner } from "@/shared/ui/spinner";

import { PublicationBadge } from "./PublicationBadge";

type AssignCourseDialogProps = {
  classroom: Classroom;
  open: boolean;
  onClose: () => void;
};

export function AssignCourseDialog({
  classroom,
  open,
  onClose,
}: AssignCourseDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onClose();
        }
      }}
    >
      <DialogContent>
        {open && <CourseChoice classroom={classroom} />}
      </DialogContent>
    </Dialog>
  );
}

function CourseChoice({ classroom }: { classroom: Classroom }) {
  // For a teacher: their own courses that are not archived
  const { data: courses, isPending, isError, refetch } = useCourses();
  const assignCourse = useAssignCourse(classroom.id);
  const assignedIds = new Set(classroom.courses.map((course) => course.id));

  let content;
  if (isPending) {
    content = (
      <div className="flex justify-center py-4">
        <Spinner className="size-5" />
      </div>
    );
  } else if (isError) {
    content = (
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">
          Nie udało się wczytać kursów.
        </p>
        <Button variant="outline" onClick={() => refetch()}>
          Spróbuj ponownie
        </Button>
      </div>
    );
  } else if (courses.length === 0) {
    content = (
      <p className="text-sm text-muted-foreground">
        Nie masz jeszcze kursów.{" "}
        <Link
          href="/teach"
          className="font-medium underline underline-offset-4"
        >
          Utwórz kurs
        </Link>{" "}
        i wróć tutaj.
      </p>
    );
  } else {
    const available = courses.filter((course) => !assignedIds.has(course.id));
    content =
      available.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Wszystkie Twoje kursy są już przypisane do tej klasy.
        </p>
      ) : (
        <ul
          role="list"
          className="max-h-72 divide-y overflow-y-auto rounded-xl ring-1 ring-foreground/10"
        >
          {available.map((course) => {
            const isAssigning =
              assignCourse.isPending && assignCourse.variables === course.id;
            return (
              <li
                key={course.id}
                className="flex items-center gap-3 py-2 pr-2 pl-4"
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <p className="truncate font-medium">{course.title}</p>
                  <PublicationBadge isPublished={course.is_published} />
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={isAssigning}
                  aria-label={`Przypisz kurs: ${course.title}`}
                  onClick={() =>
                    assignCourse.mutate(course.id, {
                      onSuccess: () =>
                        toast.success(`Przypisano kurs: ${course.title}.`),
                      onError: (error) => toast.error(classroomsError(error)),
                    })
                  }
                >
                  {isAssigning && <Spinner data-icon="inline-start" />}
                  Przypisz
                </Button>
              </li>
            );
          })}
        </ul>
      );
  }

  return (
    <div className="grid gap-4">
      <DialogHeader>
        <DialogTitle>Przypisz kurs</DialogTitle>
        <DialogDescription>
          Uczniowie klasy zobaczą przypisany kurs, także prywatny.
        </DialogDescription>
      </DialogHeader>
      {content}
      <DialogFooter>
        <DialogClose render={<Button type="button" />}>Gotowe</DialogClose>
      </DialogFooter>
    </div>
  );
}
