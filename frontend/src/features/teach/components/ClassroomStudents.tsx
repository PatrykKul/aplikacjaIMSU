"use client";

import { PlusIcon, UserMinusIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { classroomsError } from "@/features/classes/errors";
import { useRemoveStudent } from "@/features/classes/hooks";
import type { Classroom } from "@/features/classes/types";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { AddStudentDialog } from "./AddStudentDialog";

export function ClassroomStudents({ classroom }: { classroom: Classroom }) {
  const removeStudent = useRemoveStudent(classroom.id);
  const [adding, setAdding] = useState(false);
  const students = classroom.students ?? [];

  return (
    <div className="space-y-4">
      {students.length === 0 ? (
        <p className="text-muted-foreground">
          W klasie nie ma jeszcze uczniów. Dodaj ich po adresie e-mail.
        </p>
      ) : (
        <ul
          role="list"
          className="divide-y overflow-hidden rounded-xl ring-1 ring-foreground/10"
        >
          {students.map((student) => {
            const isRemoving =
              removeStudent.isPending && removeStudent.variables === student.id;
            return (
              <li
                key={student.id}
                className="flex items-center gap-3 py-1 pr-1 pl-4"
              >
                <div className="min-w-0 flex-1 py-1">
                  <p className="truncate font-medium">{student.display_name}</p>
                  <p className="truncate text-sm text-muted-foreground">
                    {student.email}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`Usuń z klasy: ${student.display_name}`}
                  title="Usuń z klasy"
                  disabled={isRemoving}
                  onClick={() =>
                    removeStudent.mutate(student.id, {
                      onSuccess: () =>
                        toast.success(
                          `Usunięto z klasy: ${student.display_name}.`,
                        ),
                      onError: (error) => toast.error(classroomsError(error)),
                    })
                  }
                >
                  {isRemoving ? <Spinner /> : <UserMinusIcon />}
                </Button>
              </li>
            );
          })}
        </ul>
      )}

      <Button variant="outline" onClick={() => setAdding(true)}>
        <PlusIcon data-icon="inline-start" />
        Dodaj ucznia
      </Button>

      <AddStudentDialog
        classroom={classroom}
        open={adding}
        onClose={() => setAdding(false)}
      />
    </div>
  );
}
