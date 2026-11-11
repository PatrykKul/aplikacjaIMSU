"use client";

import { CloudOffIcon, PlusIcon, UsersIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";

import { useClassrooms, useCreateClassroom } from "@/features/classes/hooks";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { ClassroomNameDialog } from "./ClassroomNameDialog";
import { TeacherClassroomCard } from "./TeacherClassroomCard";

export function TeacherClassroomsPage() {
  const router = useRouter();
  const { data: classrooms, isPending, error, refetch } = useClassrooms();
  const createClassroom = useCreateClassroom();
  const [creating, setCreating] = useState(false);

  const newClassroomButton = (
    <Button
      onClick={() => {
        createClassroom.reset();
        setCreating(true);
      }}
    >
      <PlusIcon data-icon="inline-start" />
      Nowa klasa
    </Button>
  );

  let content;
  if (isPending) {
    content = (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  } else if (error) {
    content = (
      <PageMessage
        icon={CloudOffIcon}
        title="Nie udało się wczytać klas"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  } else if (classrooms.length === 0) {
    content = (
      <PageMessage
        icon={UsersIcon}
        title="Nie masz jeszcze klas"
        description="Utwórz klasę, dodaj do niej uczniów i przypisz jej kursy — także prywatne."
        action={newClassroomButton}
      />
    );
  } else {
    content = (
      <ul role="list" className="grid gap-4 sm:grid-cols-2">
        {classrooms.map((classroom) => (
          <li key={classroom.id}>
            <TeacherClassroomCard classroom={classroom} />
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Klasy</h1>
        {classrooms && classrooms.length > 0 && newClassroomButton}
      </div>
      {content}
      <ClassroomNameDialog
        open={creating}
        title="Nowa klasa"
        description="Uczniów i kursy dodasz na następnej stronie."
        submitLabel="Utwórz klasę"
        pending={createClassroom.isPending}
        error={createClassroom.error}
        onSubmit={(name) =>
          createClassroom.mutate(name, {
            onSuccess: (classroom) => {
              toast.success(`Utworzono klasę: ${classroom.name}.`);
              router.push(`/teach/classes/${classroom.id}`);
            },
          })
        }
        onClose={() => setCreating(false)}
      />
    </div>
  );
}
