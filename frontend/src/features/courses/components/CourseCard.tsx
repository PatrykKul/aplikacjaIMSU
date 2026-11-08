import Link from "next/link";

import { Badge } from "@/shared/ui/badge";
import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";

import type { CourseSummary } from "../types";

function StatusBadge({ course }: { course: CourseSummary }) {
  if (course.is_archived) {
    return <Badge variant="outline">Usunięty przez autora</Badge>;
  }
  return course.is_published ? (
    <Badge>Opublikowany</Badge>
  ) : (
    <Badge variant="outline">Prywatny</Badge>
  );
}

type CourseCardProps = {
  course: CourseSummary;
  /** Publication status, for the admin who sees every course. */
  showStatus?: boolean;
};

// The title link stretches over the whole card, so the card is clickable
export function CourseCard({ course, showStatus }: CourseCardProps) {
  return (
    <Card className="relative h-full transition-colors hover:bg-muted/50 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
      <CardHeader>
        <CardTitle className="text-lg">
          <Link
            href={`/courses/${course.id}`}
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
      {showStatus && (
        <CardFooter className="mt-auto">
          <StatusBadge course={course} />
        </CardFooter>
      )}
    </Card>
  );
}
