"use client";

import { useCurrentUser } from "@/features/auth/hooks";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCourses } from "../hooks";
import { CourseCard } from "./CourseCard";

function EmptyCourses({ isAdmin }: { isAdmin: boolean }) {
  return (
    <div className="space-y-2 rounded-xl border border-dashed p-8 text-center">
      <p className="font-medium">
        {isAdmin ? "Nie ma jeszcze kursów" : "Kursy pojawią się tu wkrótce"}
      </p>
      <p className="text-sm text-muted-foreground">
        {isAdmin ? (
          <>
            Dodaj kurs w backendzie poleceniem{" "}
            <code className="font-mono">import-course</code>.
          </>
        ) : (
          "Gdy kurs zostanie opublikowany, zobaczysz go na tej stronie."
        )}
      </p>
    </div>
  );
}

export function CourseList() {
  const { data: user } = useCurrentUser();
  const { data: courses, isPending, isError, refetch } = useCourses();
  const isAdmin = user?.role === "admin";

  if (isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (isError) {
    return (
      <PageMessage
        title="Nie udało się wczytać kursów"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Kursy</h1>
      {courses.length === 0 ? (
        <EmptyCourses isAdmin={isAdmin} />
      ) : (
        <ul role="list" className="grid gap-4 sm:grid-cols-2">
          {courses.map((course) => (
            <li key={course.id}>
              <CourseCard course={course} isAdmin={isAdmin} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
