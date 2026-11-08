"use client";

import { useCurrentUser } from "@/features/auth/hooks";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCourses } from "../hooks";
import { CourseCard } from "./CourseCard";

/** Published courses for a student; every course for the admin (read only until stage 4). */
export function CourseList() {
  const { data: user } = useCurrentUser();
  const { data: courses, isPending, error, refetch } = useCourses();
  const isAdmin = user?.role === "admin";

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
        title="Nie udało się wczytać kursów"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  } else if (courses.length === 0) {
    content = (
      <PageMessage
        title="Nie ma jeszcze kursów"
        description={
          isAdmin
            ? "Nauczyciele nie utworzyli jeszcze żadnego kursu."
            : "Nauczyciele nie opublikowali jeszcze żadnego kursu. Zajrzyj tu później."
        }
      />
    );
  } else {
    content = (
      <ul role="list" className="grid gap-4 sm:grid-cols-2">
        {courses.map((course) => (
          <li key={course.id}>
            <CourseCard course={course} showStatus={isAdmin} />
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Kursy</h1>
      {content}
    </div>
  );
}
