"use client";

import { ArrowRightIcon, BookOpenIcon, CloudOffIcon } from "lucide-react";
import Link from "next/link";
import { type ReactNode, useState } from "react";

import { useCurrentUser } from "@/features/auth/hooks";
import { lessonsText } from "@/features/learning-style/explain";
import { useMyProgress } from "@/features/progress/hooks";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { useCourses } from "../hooks";
import type { CourseSummary } from "../types";
import { ChangeOwnerDialog } from "./ChangeOwnerDialog";
import { CourseProgressBar } from "./CourseProgressBar";
import { EnrollmentAction } from "./EnrollmentAction";

function CourseMeta({ course }: { course: CourseSummary }) {
  return (
    <p className="text-sm text-muted-foreground">
      {course.owner.display_name} · {lessonsText(course.lesson_count)}
    </p>
  );
}

function CourseTitle({ course }: { course: CourseSummary }) {
  return (
    <h3 className="text-lg font-medium">
      <Link
        href={`/courses/${course.id}`}
        className="underline-offset-4 hover:underline"
      >
        {course.title}
      </Link>
    </h3>
  );
}

function Row({ children }: { children: ReactNode }) {
  return (
    <li className="grid gap-4 py-5 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center sm:gap-8">
      {children}
    </li>
  );
}

/** Accepted courses with progress and "Kontynuuj" (next lesson from /me/progress). */
function MyCourses({ courses }: { courses: CourseSummary[] }) {
  const progress = useMyProgress(courses.length > 0);
  const nextLesson = new Map(
    (progress.data?.courses ?? []).map((c) => [c.id, c.next_lesson]),
  );

  return (
    <section aria-labelledby="my-courses" className="space-y-3">
      <h2 id="my-courses" className="text-xl font-semibold">
        Moje kursy
      </h2>
      {courses.length === 0 ? (
        <p className="text-muted-foreground">
          Nie masz jeszcze żadnego kursu. Wybierz kurs z katalogu poniżej i
          poproś o zapis. Lekcje otworzą się, gdy nauczyciel przyjmie prośbę.
        </p>
      ) : (
        <ul role="list" className="divide-y border-y">
          {courses.map((course) => {
            const passed = course.progress?.passed ?? 0;
            const total = course.progress?.total ?? course.lesson_count;
            const next = nextLesson.get(course.id);
            const done = total > 0 && passed >= total;
            return (
              <Row key={course.id}>
                <div className="min-w-0 space-y-2">
                  <CourseTitle course={course} />
                  <CourseMeta course={course} />
                  <div className="max-w-sm">
                    <CourseProgressBar passed={passed} total={total} />
                  </div>
                </div>
                <Link
                  href={
                    next
                      ? `/courses/${course.id}/lessons/${next.id}`
                      : `/courses/${course.id}`
                  }
                  className={cn(
                    buttonVariants({ variant: done ? "outline" : "default" }),
                    "h-auto min-h-control max-w-full justify-self-start py-2 text-left whitespace-normal sm:max-w-xs",
                  )}
                >
                  {done
                    ? "Zobacz kurs"
                    : next
                      ? `Kontynuuj: Lekcja ${next.number} – ${next.title}`
                      : "Kontynuuj"}
                  {!done && <ArrowRightIcon data-icon="inline-end" />}
                </Link>
              </Row>
            );
          })}
        </ul>
      )}
    </section>
  );
}

function Catalog({ courses }: { courses: CourseSummary[] }) {
  return (
    <section aria-labelledby="catalog" className="space-y-3">
      <h2 id="catalog" className="text-xl font-semibold">
        Katalog
      </h2>
      {courses.length === 0 ? (
        <p className="text-muted-foreground">
          Na razie nie ma innych kursów. Zajrzyj tu później.
        </p>
      ) : (
        <ul role="list" className="divide-y border-y">
          {courses.map((course) => (
            <Row key={course.id}>
              <div className="min-w-0 space-y-1.5">
                <CourseTitle course={course} />
                {course.description && (
                  <p className="line-clamp-2 max-w-[65ch] text-muted-foreground">
                    {course.description}
                  </p>
                )}
                <CourseMeta course={course} />
              </div>
              <EnrollmentAction
                courseId={course.id}
                status={course.enrollment_status}
              />
            </Row>
          ))}
        </ul>
      )}
    </section>
  );
}

function statusText(course: CourseSummary): string {
  if (course.is_archived) {
    return "Usunięty przez autora";
  }
  return course.is_published ? "Opublikowany" : "Prywatny";
}

/** Every course for the admin; the only change is the owner (D56). */
function AllCourses({ courses }: { courses: CourseSummary[] }) {
  const [target, setTarget] = useState<CourseSummary | null>(null);
  return (
    <>
      <ul role="list" className="divide-y border-y">
        {courses.map((course) => (
          <Row key={course.id}>
            <div className="min-w-0 space-y-1.5">
              <CourseTitle course={course} />
              <CourseMeta course={course} />
            </div>
            <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
              <p className="text-sm text-muted-foreground">
                {statusText(course)}
              </p>
              {!course.is_archived && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTarget(course)}
                  aria-label={`Zmień właściciela: ${course.title}`}
                >
                  Zmień właściciela
                </Button>
              )}
            </div>
          </Row>
        ))}
      </ul>
      <ChangeOwnerDialog
        key={target?.id ?? "closed"}
        course={target}
        onClose={() => setTarget(null)}
      />
    </>
  );
}

/** Students: "Moje kursy" and "Katalog"; admin: every course. */
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
        title="Nie ma jeszcze kursów"
        description={
          isAdmin
            ? "Nauczyciele nie utworzyli jeszcze żadnego kursu."
            : "Nauczyciele nie opublikowali jeszcze żadnego kursu. Zajrzyj tu później."
        }
      />
    );
  } else if (isAdmin) {
    content = <AllCourses courses={courses} />;
  } else {
    const mine = courses.filter((c) => c.enrollment_status === "accepted");
    const others = courses.filter((c) => c.enrollment_status !== "accepted");
    content = (
      <div className="space-y-10">
        <MyCourses courses={mine} />
        <Catalog courses={others} />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold tracking-tight">Kursy</h1>
      {content}
    </div>
  );
}
