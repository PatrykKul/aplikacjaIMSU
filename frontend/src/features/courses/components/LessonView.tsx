"use client";

import { ArrowLeftIcon, ArrowRightIcon } from "lucide-react";
import Link from "next/link";

import { useCurrentUser } from "@/features/auth/hooks";
import { BlockView } from "@/features/content/components/BlockView";
import { useLessonBlocks } from "@/features/content/hooks";
import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useLesson } from "../hooks";
import { LessonHeader } from "./LessonHeader";
import { PreviewBanner } from "./PreviewBanner";

type LessonViewProps = { courseId: number; lessonId: number };

export function LessonView({ courseId, lessonId }: LessonViewProps) {
  const { data: user } = useCurrentUser();
  const lesson = useLesson(lessonId);
  const blocks = useLessonBlocks(lessonId);
  const courseHref = `/courses/${courseId}`;

  if (lesson.isPending || blocks.isPending) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <Spinner className="size-8" />
      </div>
    );
  }
  const error = lesson.error ?? blocks.error;
  if (
    (error instanceof ApiError && error.status === 404) ||
    (lesson.data && lesson.data.course.id !== courseId)
  ) {
    return (
      <PageMessage
        fullScreen
        title="Nie znaleziono lekcji"
        description="Lekcja nie istnieje albo nie jest jeszcze dostępna."
        action={
          <Link
            href={courseHref}
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć do kursu
          </Link>
        }
      />
    );
  }
  if (error || !lesson.data || !blocks.data) {
    return (
      <PageMessage
        fullScreen
        title="Nie udało się wczytać lekcji"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button
            onClick={() => {
              void lesson.refetch();
              void blocks.refetch();
            }}
          >
            Spróbuj ponownie
          </Button>
        }
      />
    );
  }

  const { course, previous_lesson_id, next_lesson_id } = lesson.data;
  const lessonHref = (id: number) => `/courses/${course.id}/lessons/${id}`;
  const isAuthor = user?.id === course.owner_id;

  return (
    <>
      <LessonHeader
        courseHref={courseHref}
        courseTitle={course.title}
        title={lesson.data.title}
      />
      <main className="mx-auto w-full max-w-3xl flex-1 space-y-5 px-4 py-8 sm:px-6">
        {isAuthor && (
          <PreviewBanner
            editHref={`/teach/courses/${course.id}/lessons/${lessonId}`}
            what="lekcję"
          />
        )}

        {blocks.data.blocks.length === 0 ? (
          <p className="text-muted-foreground">Ta lekcja jest jeszcze pusta.</p>
        ) : (
          <ol role="list" aria-label="Treść lekcji" className="space-y-5">
            {blocks.data.blocks.map((block) => (
              <li key={block.id}>
                <BlockView block={block} />
              </li>
            ))}
          </ol>
        )}

        <nav
          aria-label="Lekcje kursu"
          className="flex flex-wrap items-center justify-between gap-3 pt-4"
        >
          {previous_lesson_id ? (
            <Link
              href={lessonHref(previous_lesson_id)}
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              <ArrowLeftIcon data-icon="inline-start" />
              Poprzednia lekcja
            </Link>
          ) : (
            <span />
          )}
          <Link
            href={next_lesson_id ? lessonHref(next_lesson_id) : courseHref}
            className={cn(buttonVariants(), "ml-auto")}
          >
            {next_lesson_id ? "Następna lekcja" : "Wróć do kursu"}
            {next_lesson_id && <ArrowRightIcon data-icon="inline-end" />}
          </Link>
        </nav>
      </main>
    </>
  );
}
