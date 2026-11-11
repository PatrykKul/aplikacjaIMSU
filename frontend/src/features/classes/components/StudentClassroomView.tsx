"use client";

import { CloudOffIcon, MailIcon, SearchXIcon } from "lucide-react";
import Link from "next/link";

import { CourseCard } from "@/features/courses/components/CourseCard";
import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useClassroom } from "../hooks";

export function StudentClassroomView({ classroomId }: { classroomId: number }) {
  const {
    data: classroom,
    error,
    isPending,
    refetch,
  } = useClassroom(classroomId);

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
          icon={SearchXIcon}
          title="Nie znaleziono klasy"
          description="Klasa nie istnieje albo nie należysz już do niej."
          action={
            <Link
              href="/classes"
              className="text-sm font-medium underline underline-offset-4"
            >
              Wróć do moich klas
            </Link>
          }
        />
      );
    }
    return (
      <PageMessage
        icon={CloudOffIcon}
        title="Nie udało się wczytać klasy"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  const { teacher } = classroom;

  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link href="/classes" className="hover:text-foreground">
            Moje klasy
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{classroom.name}</span>
        </nav>
        <h1 className="text-2xl font-semibold tracking-tight">
          {classroom.name}
        </h1>
        <div className="space-y-1">
          <p className="text-lg text-muted-foreground">
            Nauczyciel: {teacher.display_name}
          </p>
          <a
            href={`mailto:${teacher.email}`}
            className="inline-flex items-center gap-2 text-sm font-medium underline-offset-4 hover:underline"
          >
            <MailIcon className="size-4" aria-hidden="true" />
            {teacher.email}
          </a>
        </div>
      </div>

      <section aria-labelledby="classroom-courses" className="space-y-4">
        <h2 id="classroom-courses" className="text-xl font-semibold">
          Kursy
        </h2>
        {classroom.courses.length === 0 ? (
          <p className="text-muted-foreground">
            Nauczyciel nie przypisał jeszcze kursów tej klasie.
          </p>
        ) : (
          <ul role="list" className="grid gap-4 sm:grid-cols-2">
            {classroom.courses.map((course) => (
              <li key={course.id}>
                <CourseCard course={course} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
