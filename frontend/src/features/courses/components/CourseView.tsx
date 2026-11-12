"use client";

import {
  CheckIcon,
  CloudOffIcon,
  LightbulbIcon,
  LockIcon,
  SearchXIcon,
} from "lucide-react";
import Link from "next/link";

import { useCurrentUser } from "@/features/auth/hooks";
import { hintText, lockedLessonText } from "@/features/learning-style/explain";
import { useCourseHint } from "@/features/learning-style/hooks";
import { useMyProgress } from "@/features/progress/hooks";
import { ApiError } from "@/shared/api/client";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { isEmptyDocument } from "@/shared/rich-text/is-empty";
import { RichTextView } from "@/shared/rich-text/RichTextView";
import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCourse } from "../hooks";
import type { Course, CourseLesson } from "../types";
import { CourseProgressBar } from "./CourseProgressBar";
import { EnrollmentAction } from "./EnrollmentAction";
import { PreviewBanner } from "./PreviewBanner";

const linkClass = "text-sm font-medium underline underline-offset-4";
const proseClass = "max-w-[65ch] text-[1.0625rem] leading-[1.65]";

/** student = not accepted yet; reader = admin or another teacher. */
type Viewer = "student" | "enrolled" | "author" | "reader";

/** Number of a lesson; a check mark once it is passed. */
function LessonNumber({ lesson }: { lesson: CourseLesson }) {
  const passed = lesson.state === "passed";
  return (
    <span
      aria-hidden="true"
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-full text-sm font-medium tabular-nums",
        passed ? "bg-primary text-primary-foreground" : "bg-muted",
        lesson.state === "locked" && "text-muted-foreground",
      )}
    >
      {passed ? <CheckIcon className="size-4" /> : lesson.number}
    </span>
  );
}

function LessonStatus({
  lesson,
  viewer,
  score,
}: {
  lesson: CourseLesson;
  viewer: Viewer;
  score: number | undefined;
}) {
  if (viewer === "author") {
    return (
      <span className="text-sm text-muted-foreground">
        {lesson.is_published
          ? "Opublikowana"
          : "Szkic – uczniowie jej nie widzą"}
      </span>
    );
  }
  if (viewer !== "enrolled") {
    return null;
  }
  switch (lesson.state) {
    case "passed":
      return (
        <span className="text-sm font-medium">
          Zaliczona{score !== undefined && ` z wynikiem ${score}%`}
        </span>
      );
    case "available":
      return <span className="text-sm text-muted-foreground">Dostępna</span>;
    case "locked":
      return (
        <span className="flex items-center gap-1.5 text-sm text-muted-foreground sm:justify-end">
          <LockIcon aria-hidden="true" className="size-4 shrink-0" />
          {lesson.required_lesson_number
            ? lockedLessonText(lesson.required_lesson_number)
            : "Zablokowana"}
        </span>
      );
    default:
      return null;
  }
}

/** "Streszczenie kursu": numbered lessons with outlines and their state. */
function CourseOutline({
  course,
  viewer,
  scores,
}: {
  course: Course;
  viewer: Viewer;
  scores: Map<number, number>;
}) {
  if (course.lessons.length === 0) {
    return (
      <p className="text-muted-foreground">Ten kurs nie ma jeszcze lekcji.</p>
    );
  }
  return (
    <ol role="list" className="divide-y border-y">
      {course.lessons.map((lesson) => {
        const open =
          viewer === "author" ||
          viewer === "reader" ||
          (viewer === "enrolled" && lesson.state !== "locked");
        return (
          <li
            key={lesson.id}
            className="grid grid-cols-[2rem_minmax(0,1fr)] gap-x-4 gap-y-2 py-5 sm:grid-cols-[2rem_minmax(0,1fr)_auto]"
          >
            <LessonNumber lesson={lesson} />
            <div className="min-w-0 space-y-1.5">
              <h3 className="text-lg font-medium">
                {open ? (
                  <Link
                    href={`/courses/${course.id}/lessons/${lesson.id}`}
                    className="underline-offset-4 hover:underline"
                  >
                    <span className="sr-only">Lekcja {lesson.number}: </span>
                    {lesson.title}
                  </Link>
                ) : (
                  <span
                    className={cn(
                      lesson.state === "locked" && "text-muted-foreground",
                    )}
                  >
                    <span className="sr-only">Lekcja {lesson.number}: </span>
                    {lesson.title}
                  </span>
                )}
              </h3>
              {!isEmptyDocument(lesson.outline) && lesson.outline && (
                <RichTextView
                  content={lesson.outline}
                  className="max-w-[65ch] text-muted-foreground"
                />
              )}
            </div>
            <div className="col-start-2 sm:col-start-3 sm:pt-1.5 sm:text-right">
              <LessonStatus
                lesson={lesson}
                viewer={viewer}
                score={scores.get(lesson.id)}
              />
            </div>
          </li>
        );
      })}
    </ol>
  );
}

export function CourseView({ courseId }: { courseId: number }) {
  const { data: user } = useCurrentUser();
  const { data: course, error, isPending, refetch } = useCourse(courseId);
  const isStudent = user?.role === "student";
  const enrolled = isStudent && course?.enrollment_status === "accepted";
  const progress = useMyProgress(enrolled);
  const attempted = (progress.data?.lessons ?? []).some(
    (lesson) => lesson.course_id === courseId && lesson.attempts.length > 0,
  );
  // R8: only for a student without any result in this course
  const hint = useCourseHint(
    courseId,
    enrolled && progress.isSuccess && !attempted,
  );

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
            <Link href="/courses" className={linkClass}>
              Wróć do kursów
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

  const isAuthor = user?.id === course.owner.id;
  const viewer: Viewer = isAuthor
    ? "author"
    : enrolled
      ? "enrolled"
      : isStudent
        ? "student"
        : "reader";

  // Best passed result of each lesson (from "Moje postępy")
  const scores = new Map<number, number>();
  for (const lesson of progress.data?.lessons ?? []) {
    const passed = lesson.attempts.filter((attempt) => attempt.passed);
    if (lesson.course_id === courseId && passed.length > 0) {
      scores.set(
        lesson.lesson_id,
        Math.max(...passed.map((attempt) => attempt.percent)),
      );
    }
  }

  return (
    <div className="space-y-10">
      <div className="space-y-6">
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

        <div className="grid gap-6 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-start">
          <div className="space-y-3">
            <h1 className="text-2xl font-semibold tracking-tight">
              {course.title}
            </h1>
            {course.description && (
              <p className="max-w-[65ch] text-lg text-muted-foreground">
                {course.description}
              </p>
            )}
            <p className="text-sm text-muted-foreground">
              Nauczyciel: {course.owner.display_name}
            </p>
          </div>
          {viewer === "student" && (
            <EnrollmentAction
              courseId={course.id}
              status={course.enrollment_status}
            />
          )}
        </div>

        {viewer === "enrolled" && course.progress && (
          <div className="max-w-sm">
            <CourseProgressBar
              passed={course.progress.passed}
              total={course.progress.total}
            />
          </div>
        )}
      </div>

      {hint.data && (
        <aside className="flex gap-3 border-l-2 border-primary py-1 pl-4">
          <LightbulbIcon
            aria-hidden="true"
            className="mt-0.5 size-5 shrink-0 text-primary"
          />
          <div className="space-y-1">
            <p className="font-medium">Podpowiedź z kursu</p>
            <p className="max-w-[65ch] text-muted-foreground">
              {hintText(hint.data)}. To tylko informacja: lekcje dostajesz w
              swoim stylu, a formę każdej lekcji możesz zmienić w trakcie.
            </p>
          </div>
        </aside>
      )}

      {!isEmptyDocument(course.introduction) && course.introduction && (
        <section aria-labelledby="course-intro" className="space-y-3">
          <h2 id="course-intro" className="text-xl font-semibold">
            Wstęp
          </h2>
          <RichTextView content={course.introduction} className={proseClass} />
        </section>
      )}

      <section aria-labelledby="course-lessons" className="space-y-3">
        <div className="space-y-1">
          <h2 id="course-lessons" className="text-xl font-semibold">
            Streszczenie kursu
          </h2>
          {viewer === "student" && (
            <p className="text-sm text-muted-foreground">
              Lekcje otworzą się po zapisaniu na kurs i przyjęciu przez
              nauczyciela.
            </p>
          )}
          {viewer === "enrolled" && (
            <p className="text-sm text-muted-foreground">
              Kolejna lekcja otwiera się po zaliczeniu quizu poprzedniej (od
              70%).
            </p>
          )}
        </div>
        <CourseOutline course={course} viewer={viewer} scores={scores} />
      </section>

      {!isEmptyDocument(course.summary) && course.summary && (
        <section aria-labelledby="course-summary" className="space-y-3">
          <h2 id="course-summary" className="text-xl font-semibold">
            Podsumowanie i wnioski
          </h2>
          <RichTextView content={course.summary} className={proseClass} />
        </section>
      )}
    </div>
  );
}
