"use client";

import Link from "next/link";

import { useCourse } from "@/features/courses/hooks";
import { ApiError } from "@/shared/api/client";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { useSkillLesson } from "../hooks";
import { LessonPlayer } from "./LessonPlayer";

type LessonPageProps = {
  courseId: number;
  skillId: number;
};

function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404;
}

export function LessonPage({ courseId, skillId }: LessonPageProps) {
  const course = useCourse(courseId);
  const lesson = useSkillLesson(skillId);

  const courseHref = `/courses/${courseId}`;
  const error = course.error ?? lesson.error;

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
  if (!course.data || !lesson.data) {
    return <PageSpinner />;
  }

  // The skill must belong to the course from the address
  const skills = course.data.units.flatMap((unit) =>
    unit.skills.map((skill) => ({ skill, unit })),
  );
  const index = skills.findIndex(({ skill }) => skill.id === skillId);
  if (index === -1) {
    return (
      <PageMessage
        fullScreen
        title="Nie znaleziono lekcji"
        description="Ta lekcja nie należy do wybranego kursu."
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

  const { skill, unit } = skills[index];
  const next = skills[index + 1];

  return (
    <LessonPlayer
      key={lesson.data.id}
      lesson={lesson.data}
      courseHref={courseHref}
      context={`${course.data.title} · ${unit.title}`}
      goal={skill.goal}
      nextHref={next ? `${courseHref}/skills/${next.skill.id}` : null}
    />
  );
}
