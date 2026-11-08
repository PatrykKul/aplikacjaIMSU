import Link from "next/link";

import type { CourseSummary } from "@/features/courses/types";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";

import { PublicationBadge } from "./PublicationBadge";

// The title link stretches over the whole card, so the card is clickable
export function TeacherCourseCard({ course }: { course: CourseSummary }) {
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
      <CardFooter className="mt-auto">
        <PublicationBadge isPublished={course.is_published} />
      </CardFooter>
    </Card>
  );
}
