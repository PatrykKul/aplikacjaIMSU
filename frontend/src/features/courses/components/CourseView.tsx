"use client";

import { CloudOffIcon, SearchXIcon } from "lucide-react";
import Link from "next/link";

import { useCurrentUser } from "@/features/auth/hooks";
import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { isEmptyDocument } from "@/shared/rich-text/is-empty";
import { RichTextView } from "@/shared/rich-text/RichTextView";
import { Button } from "@/shared/ui/button";
import { Card, CardHeader, CardTitle } from "@/shared/ui/card";
import { Spinner } from "@/shared/ui/spinner";

import { useCourse } from "../hooks";
import { PreviewBanner } from "./PreviewBanner";

const linkClass = "text-sm font-medium underline underline-offset-4";

export function CourseView({ courseId }: { courseId: number }) {
  const { data: user } = useCurrentUser();
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
      return (
        <PageMessage
          icon={SearchXIcon}
          title="Nie znaleziono kursu"
          description="Kurs nie istnieje albo nie jest jeszcze dostępny."
          action={
            <Link href="/dashboard" className={linkClass}>
              Wróć na stronę główną
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

  const isAuthor = user?.id === course.owner_id;

  return (
    <div className="space-y-8">
      {isAuthor ? (
        <PreviewBanner editHref={`/teach/courses/${course.id}`} what="kurs" />
      ) : (
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link href="/courses" className="hover:text-foreground">
            Kursy
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{course.title}</span>
        </nav>
      )}

      <div className="space-y-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          {course.title}
        </h1>
        {course.description && (
          <p className="max-w-[65ch] text-lg text-muted-foreground">
            {course.description}
          </p>
        )}
      </div>

      {!isEmptyDocument(course.introduction) && course.introduction && (
        <section aria-label="Wstęp">
          <RichTextView
            content={course.introduction}
            className="max-w-[65ch] text-[1.0625rem] leading-[1.65]"
          />
        </section>
      )}

      <section aria-labelledby="course-lessons" className="space-y-4">
        <h2 id="course-lessons" className="text-xl font-semibold">
          Lekcje
        </h2>
        {course.lessons.length === 0 ? (
          <p className="text-muted-foreground">
            Ten kurs nie ma jeszcze lekcji.
          </p>
        ) : (
          <ol role="list" className="grid gap-3">
            {course.lessons.map((lesson, index) => (
              <li key={lesson.id}>
                <Card className="relative transition-colors hover:bg-muted/50 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
                  <CardHeader className="flex items-center gap-4">
                    <span
                      aria-hidden="true"
                      className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted text-sm font-medium tabular-nums"
                    >
                      {index + 1}
                    </span>
                    <CardTitle className="text-lg">
                      <Link
                        href={`/courses/${course.id}/lessons/${lesson.id}`}
                        className="outline-none after:absolute after:inset-0"
                      >
                        {lesson.title}
                      </Link>
                    </CardTitle>
                  </CardHeader>
                </Card>
              </li>
            ))}
          </ol>
        )}
      </section>
    </div>
  );
}
