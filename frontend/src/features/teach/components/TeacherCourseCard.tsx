import Link from "next/link";

import { plural } from "@/shared/lib/plural";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";

import type { TeacherCourse, TeacherCourseSummary } from "../types";

/** "3 z 4 lekcji opublikowanych"; null until the course details arrive. */
function publishedLabel(course: TeacherCourse | undefined): string | null {
  if (!course) {
    return null;
  }
  const total = course.lessons.length;
  const published = course.lessons.filter((l) => l.is_published).length;
  if (total === 0) {
    return "Brak lekcji";
  }
  if (total === 1) {
    return published === 1
      ? "1 lekcja, opublikowana"
      : "1 lekcja, nieopublikowana";
  }
  return `${published} z ${total} lekcji opublikowanych`;
}

type TeacherCourseCardProps = {
  course: TeacherCourseSummary;
  /** Details with the lessons (counted as published / all). */
  details: TeacherCourse | undefined;
};

// The title link stretches over the whole card, so the card is clickable
export function TeacherCourseCard({ course, details }: TeacherCourseCardProps) {
  const requests = course.pending_requests ?? 0;
  const lessons = publishedLabel(details);

  return (
    <Card className="relative h-full transition-colors hover:bg-muted/50 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
      <CardHeader>
        <CardTitle className="text-lg">
          <Link
            href={`/teach/courses/${course.id}`}
            className="outline-none after:absolute after:inset-0"
          >
            {course.title}
          </Link>
        </CardTitle>
        {course.description && (
          <CardDescription className="line-clamp-3 text-base">
            {course.description}
          </CardDescription>
        )}
      </CardHeader>
      <CardFooter className="mt-auto flex-col items-start gap-1 text-sm">
        <p>
          <span className="font-medium">
            {course.is_published ? "Opublikowany" : "Prywatny"}
          </span>
          {lessons && (
            <span className="text-muted-foreground"> · {lessons}</span>
          )}
        </p>
        {requests > 0 && (
          <Link
            href={`/teach/courses/${course.id}/panel`}
            className="relative z-10 font-medium text-primary underline-offset-4 hover:underline"
          >
            {requests} {plural(requests, "prośba", "prośby", "próśb")} o zapis
          </Link>
        )}
      </CardFooter>
    </Card>
  );
}
