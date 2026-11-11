"use client";

import { BookOpenIcon, CloudOffIcon, PlusIcon } from "lucide-react";
import { useState } from "react";

import { useCourses } from "@/features/courses/hooks";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { NewCourseDialog } from "./NewCourseDialog";
import { TeacherCourseCard } from "./TeacherCourseCard";

export function TeacherCoursesPage() {
  const { data: courses, isPending, error, refetch } = useCourses();
  const [creating, setCreating] = useState(false);

  const newCourseButton = (
    <Button onClick={() => setCreating(true)}>
      <PlusIcon data-icon="inline-start" />
      Nowy kurs
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
        title="Nie udało się wczytać kursów"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  } else if (courses.length === 0) {
    content = (
      <PageMessage
        icon={BookOpenIcon}
        title="Nie masz jeszcze kursów"
        description="Utwórz pierwszy kurs, a potem dodaj do niego lekcje."
        action={newCourseButton}
      />
    );
  } else {
    content = (
      <ul role="list" className="grid gap-4 sm:grid-cols-2">
        {courses.map((course) => (
          <li key={course.id}>
            <TeacherCourseCard course={course} />
          </li>
        ))}
      </ul>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="text-2xl font-semibold tracking-tight">Moje kursy</h1>
        {courses && courses.length > 0 && newCourseButton}
      </div>
      {content}
      <NewCourseDialog open={creating} onClose={() => setCreating(false)} />
    </div>
  );
}
