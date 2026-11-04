"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useCurrentUser } from "@/features/auth/hooks";
import { useCourse } from "@/features/courses/hooks";
import { ApiError } from "@/shared/api/client";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { useLesson, useSkillLessons } from "../hooks";
import { isLessonMethod } from "../methods";
import { LessonPlayer } from "./LessonPlayer";
import { MethodSelect } from "./MethodSelect";

type LessonPageProps = {
  courseId: number;
  skillId: number;
  method?: string;
};

function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export function LessonPage({ courseId, skillId, method }: LessonPageProps) {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const course = useCourse(courseId);
  const lessons = useSkillLessons(skillId);

  const canSwitch = user?.role === "teacher" || user?.role === "admin";
  const wanted = canSwitch && isLessonMethod(method) ? method : "common";
  const summary =
    lessons.data?.find((lesson) => lesson.method === wanted) ??
    lessons.data?.find((lesson) => lesson.method === "common");
  const lesson = useLesson(summary?.id);

  const courseHref = `/courses/${courseId}`;
  const error = course.error ?? lessons.error ?? lesson.error;

  if (error) {
    return isNotFound(error) ? (
      <PageMessage
        fullScreen
        title="Nie znaleziono lekcji"
        description="Lekcja nie istnieje albo nie jest jeszcze dostępna."
        action={
          <Link
            href="/courses"
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć do kursów
          </Link>
        }
      />
    ) : (
      <PageMessage
        fullScreen
        title="Nie udało się wczytać lekcji"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button
            onClick={() => {
              course.refetch();
              lessons.refetch();
              lesson.refetch();
            }}
          >
            Spróbuj ponownie
          </Button>
        }
      />
    );
  }
  // Narrowing on data, not isPending: the errors are handled together above
  if (!course.data || !lessons.data) {
    return <PageSpinner />;
  }

  // The skill must belong to the course from the address
  const skills = course.data.units.flatMap((unit) =>
    unit.skills.map((skill) => ({ skill, unit })),
  );
  const index = skills.findIndex(({ skill }) => skill.id === skillId);
  if (index === -1 || !summary) {
    return (
      <PageMessage
        fullScreen
        title={
          index === -1 ? "Nie znaleziono lekcji" : "Lekcja jest w przygotowaniu"
        }
        description={
          index === -1
            ? "Ta umiejętność nie należy do wybranego kursu."
            : "Wróć do kursu i wybierz inną umiejętność."
        }
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
  if (!lesson.data) {
    return <PageSpinner />;
  }

  const { skill, unit } = skills[index];
  const lessonList = lessons.data;
  const next = skills[index + 1];

  return (
    <LessonPlayer
      key={lesson.data.id}
      lesson={lesson.data}
      courseHref={courseHref}
      context={`${course.data.title} · ${unit.title}`}
      goal={skill.goal}
      nextHref={next ? `${courseHref}/skills/${next.skill.id}` : null}
      methodSelect={
        canSwitch && (
          <MethodSelect
            methods={lessonList.map((item) => item.method)}
            value={summary.method}
            onChange={(selected) => {
              router.replace(
                `${courseHref}/skills/${skillId}?method=${selected}`,
              );
              window.scrollTo({ top: 0 });
            }}
          />
        )
      }
    />
  );
}
