"use client";

import Link from "next/link";

import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCourse } from "../hooks";
import { SkillList } from "./SkillList";

function CourseNotFound() {
  return (
    <PageMessage
      title="Nie znaleziono kursu"
      description="Kurs nie istnieje albo nie jest jeszcze dostępny."
      action={
        <Link
          href="/courses"
          className="text-sm font-medium underline underline-offset-4"
        >
          Wróć do kursów
        </Link>
      }
    />
  );
}

export function CourseView({ courseId }: { courseId: number }) {
  const { data: course, error, isPending, refetch } = useCourse(courseId);

  if (isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  if (error) {
    if (error instanceof ApiError && error.status === 404) {
      return <CourseNotFound />;
    }
    return (
      <PageMessage
        title="Nie udało się wczytać kursu"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  return (
    <div className="space-y-8">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link href="/courses" className="hover:text-foreground">
            Kursy
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{course.title}</span>
        </nav>
        <h1 className="text-2xl font-semibold tracking-tight">
          {course.title}
        </h1>
        {course.description && (
          <p className="max-w-[65ch] text-muted-foreground">
            {course.description}
          </p>
        )}
      </div>
      <SkillList course={course} />
    </div>
  );
}
