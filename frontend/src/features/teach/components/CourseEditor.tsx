"use client";

import { CloudOffIcon, EyeIcon, SearchXIcon, UsersIcon } from "lucide-react";
import Link from "next/link";
import type { MouseEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/shared/api/client";
import {
  confirmLeave,
  useUnsavedChangesWarning,
} from "@/shared/hooks/use-unsaved-changes-warning";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { plural } from "@/shared/lib/plural";
import { Button, buttonVariants } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useTeacherCourse } from "../hooks";
import { ArchiveCourseSection } from "./ArchiveCourseSection";
import { CoursePublishSwitch } from "./CoursePublishSwitch";
import { CourseSettingsForm } from "./CourseSettingsForm";
import { LessonList } from "./LessonList";

const backLinkClass = "text-sm font-medium underline underline-offset-4";

export function CourseEditor({ courseId }: { courseId: number }) {
  const {
    data: course,
    error,
    isPending,
    refetch,
  } = useTeacherCourse(courseId);
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
          icon={SearchXIcon}
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
        icon={CloudOffIcon}
        title="Nie udało się wczytać kursu"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }

  function leaveUnlessDirty(event: MouseEvent) {
    if (!confirmLeave(dirty)) {
      event.preventDefault();
    }
  }

  const requests = course.pending_requests ?? 0;
  const publishedCount = course.lessons.filter((l) => l.is_published).length;

  return (
    <div className="space-y-10">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link
            href="/teach"
            className="hover:text-foreground"
            onClick={leaveUnlessDirty}
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
          <div className="flex flex-wrap items-center gap-3">
            <CoursePublishSwitch course={course} />
            <Link
              href={`/teach/courses/${course.id}/panel`}
              className={cn(buttonVariants({ variant: "outline" }))}
              onClick={leaveUnlessDirty}
            >
              <UsersIcon data-icon="inline-start" />
              Panel kursu
              {requests > 0 && (
                <span className="text-muted-foreground">
                  · {requests} {plural(requests, "prośba", "prośby", "próśb")}
                </span>
              )}
            </Link>
            <Link
              href={`/courses/${course.id}`}
              className={cn(buttonVariants({ variant: "outline" }))}
              onClick={leaveUnlessDirty}
            >
              <EyeIcon data-icon="inline-start" />
              Podgląd
            </Link>
          </div>
        </div>
        <p
          id="course-publish-blocked"
          className="max-w-[65ch] text-sm text-muted-foreground"
        >
          {course.is_published
            ? `Kurs jest w katalogu. Uczniowie widzą ${publishedCount} ${plural(publishedCount, "opublikowaną lekcję", "opublikowane lekcje", "opublikowanych lekcji")}.`
            : publishedCount === 0
              ? "Kurs jest prywatny. Opublikujesz go, gdy co najmniej jedna lekcja będzie opublikowana – inaczej uczeń zobaczyłby pusty kurs."
              : "Kurs jest prywatny – widzisz go tylko Ty. Włącz „Opublikowany”, żeby trafił do katalogu."}
        </p>
      </div>

      <section aria-labelledby="course-lessons" className="space-y-4">
        <h2 id="course-lessons" className="text-xl font-semibold">
          Lekcje
        </h2>
        <p className="max-w-[65ch] text-muted-foreground">
          Uczeń przechodzi lekcje po kolei: następna otwiera się po zaliczeniu
          quizu poprzedniej. Widzi tylko lekcje opublikowane.
        </p>
        <LessonList course={course} dirty={dirty} />
      </section>

      <section aria-labelledby="course-settings" className="space-y-4">
        <h2 id="course-settings" className="text-xl font-semibold">
          Opis, wstęp i podsumowanie
        </h2>
        <CourseSettingsForm course={course} onDirtyChange={setDirty} />
      </section>

      <ArchiveCourseSection course={course} />
    </div>
  );
}
