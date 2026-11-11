"use client";

import { PencilIcon } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { toast } from "sonner";

import { useClassroom, useRenameClassroom } from "@/features/classes/hooks";
import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { ClassroomCourses } from "./ClassroomCourses";
import { ClassroomNameDialog } from "./ClassroomNameDialog";
import { ClassroomStudents } from "./ClassroomStudents";
import { DeleteClassroomSection } from "./DeleteClassroomSection";

export function ClassroomEditor({ classroomId }: { classroomId: number }) {
  const {
    data: classroom,
    error,
    isPending,
    refetch,
  } = useClassroom(classroomId);
  const renameClassroom = useRenameClassroom(classroomId);
  const [renaming, setRenaming] = useState(false);

  if (isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (error) {
    if (error instanceof ApiError && error.status === 404) {
      return (
        <PageMessage
          title="Nie znaleziono klasy"
          description="Klasa nie istnieje albo została usunięta."
          action={
            <Link
              href="/teach/classes"
              className="text-sm font-medium underline underline-offset-4"
            >
              Wróć do klas
            </Link>
          }
        />
      );
    }
    return (
      <PageMessage
        title="Nie udało się wczytać klasy"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  return (
    <div className="space-y-10">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link href="/teach/classes" className="hover:text-foreground">
            Klasy
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{classroom.name}</span>
        </nav>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold tracking-tight">
            {classroom.name}
          </h1>
          <Button
            variant="outline"
            onClick={() => {
              renameClassroom.reset();
              setRenaming(true);
            }}
          >
            <PencilIcon data-icon="inline-start" />
            Zmień nazwę
          </Button>
        </div>
      </div>

      <section aria-labelledby="classroom-students" className="space-y-4">
        <h2 id="classroom-students" className="text-xl font-semibold">
          Uczniowie
        </h2>
        <ClassroomStudents classroom={classroom} />
      </section>

      <section aria-labelledby="classroom-courses" className="space-y-4">
        <h2 id="classroom-courses" className="text-xl font-semibold">
          Kursy
        </h2>
        <ClassroomCourses classroom={classroom} />
      </section>

      <DeleteClassroomSection classroom={classroom} />

      <ClassroomNameDialog
        open={renaming}
        title="Zmiana nazwy klasy"
        submitLabel="Zapisz"
        defaultName={classroom.name}
        pending={renameClassroom.isPending}
        error={renameClassroom.error}
        onSubmit={(name) =>
          renameClassroom.mutate(name, {
            onSuccess: () => {
              toast.success("Zapisano nazwę klasy.");
              setRenaming(false);
            },
          })
        }
        onClose={() => setRenaming(false)}
      />
    </div>
  );
}
