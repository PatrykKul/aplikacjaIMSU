"use client";

import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useClassrooms } from "../hooks";
import { StudentClassroomCard } from "./StudentClassroomCard";

export function StudentClassroomsPage() {
  const { data: classrooms, isPending, error, refetch } = useClassrooms();

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
        title="Nie udało się wczytać klas"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  } else if (classrooms.length === 0) {
    content = (
      <PageMessage
        title="Nie należysz jeszcze do żadnej klasy"
        description="Nauczyciel doda Cię do klasy. Do tego czasu możesz uczyć się z kursów w zakładce „Kursy”."
      />
    );
  } else {
    content = (
      <ul role="list" className="grid gap-4 sm:grid-cols-2">
        {classrooms.map((classroom) => (
          <li key={classroom.id}>
            <StudentClassroomCard classroom={classroom} />
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Moje klasy</h1>
      {content}
    </div>
  );
}
