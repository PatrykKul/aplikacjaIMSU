"use client";

import { PlusIcon, UnlinkIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { classroomsError } from "@/features/classes/errors";
import { useUnassignCourse } from "@/features/classes/hooks";
import type { Classroom } from "@/features/classes/types";
import { Badge } from "@/shared/ui/badge";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { AssignCourseDialog } from "./AssignCourseDialog";
import { PublicationBadge } from "./PublicationBadge";

export function ClassroomCourses({ classroom }: { classroom: Classroom }) {
  const unassignCourse = useUnassignCourse(classroom.id);
  const [assigning, setAssigning] = useState(false);
  const { courses } = classroom;

  return (
    <div className="space-y-4">
      {courses.length === 0 ? (
        <p className="text-muted-foreground">
          Klasa nie ma jeszcze kursów. Przypisz swój kurs — uczniowie klasy
          zobaczą go nawet wtedy, gdy jest prywatny.
        </p>
      ) : (
        <ul
          role="list"
          className="divide-y overflow-hidden rounded-xl ring-1 ring-foreground/10"
        >
          {courses.map((course) => {
            const isUnassigning =
              unassignCourse.isPending &&
              unassignCourse.variables === course.id;
            return (
              <li
                key={course.id}
                className="flex items-center gap-3 py-1 pr-1 pl-4"
              >
                <div className="flex min-w-0 flex-1 flex-wrap items-center gap-x-3 gap-y-1 py-1">
                  {course.is_archived ? (
                    <span className="truncate font-medium text-muted-foreground">
                      {course.title}
                    </span>
                  ) : (
                    <Link
                      href={`/teach/courses/${course.id}`}
                      className="truncate font-medium underline-offset-4 hover:underline"
                    >
                      {course.title}
                    </Link>
                  )}
                  {course.is_archived ? (
                    // Students no longer see it; the teacher can only unassign it
                    <Badge variant="destructive">Usunięty</Badge>
                  ) : (
                    <PublicationBadge isPublished={course.is_published} />
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Odepnij kurs: ${course.title}`}
                  title="Odepnij od klasy"
                  disabled={isUnassigning}
                  onClick={() =>
                    unassignCourse.mutate(course.id, {
                      onSuccess: () =>
                        toast.success(`Odpięto kurs: ${course.title}.`),
                      onError: (error) => toast.error(classroomsError(error)),
                    })
                  }
                >
                  {isUnassigning ? <Spinner /> : <UnlinkIcon />}
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      <Button variant="outline" onClick={() => setAssigning(true)}>
        <PlusIcon data-icon="inline-start" />
        Przypisz kurs
      </Button>

      <AssignCourseDialog
        classroom={classroom}
        open={assigning}
        onClose={() => setAssigning(false)}
      />
    </div>
  );
}
