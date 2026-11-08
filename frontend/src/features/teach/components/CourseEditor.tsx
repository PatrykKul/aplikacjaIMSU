"use client";

import Link from "next/link";
import { useState } from "react";

import { useCourse } from "@/features/courses/hooks";
import { ApiError } from "@/shared/api/client";
import {
  confirmLeave,
  useUnsavedChangesWarning,
} from "@/shared/hooks/use-unsaved-changes-warning";
import { PageMessage } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { ArchiveCourseSection } from "./ArchiveCourseSection";
import { CourseSettingsForm } from "./CourseSettingsForm";
import { LessonList } from "./LessonList";
import { PublishSwitch } from "./PublishSwitch";

const backLinkClass = "text-sm font-medium underline underline-offset-4";

export function CourseEditor({ courseId }: { courseId: number }) {
  const { data: course, error, isPending, refetch } = useCourse(courseId);
  const [dirty, setDirty] = useState(false);
  useUnsavedChangesWarning(dirty);

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
          title="Nie znaleziono kursu"
          description="Kurs nie istnieje albo został usunięty."
          action={
            <Link href="/teach" className={backLinkClass}>
              Wróć do moich kursów
            </Link>
          }
        />
      );
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
    <div className="space-y-10">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link
            href="/teach"
            className="hover:text-foreground"
            onClick={(event) => {
              if (!confirmLeave(dirty)) {
                event.preventDefault();
              }
            }}
          >
            Moje kursy
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{course.title}</span>
        </nav>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold tracking-tight">
            {course.title}
          </h1>
          <PublishSwitch course={course} />
        </div>
      </div>

      <section aria-labelledby="course-settings" className="space-y-4">
        <h2 id="course-settings" className="text-xl font-semibold">
          Opis i wstęp
        </h2>
        <CourseSettingsForm course={course} onDirtyChange={setDirty} />
      </section>

      <section aria-labelledby="course-lessons" className="space-y-4">
        <h2 id="course-lessons" className="text-xl font-semibold">
          Lekcje
        </h2>
        <LessonList course={course} dirty={dirty} />
      </section>

      <ArchiveCourseSection course={course} />
    </div>
  );
}
