import Link from "next/link";

import { Badge } from "@/shared/ui/badge";
import {
  Card,
  CardAction,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/shared/ui/card";

import type { CourseSummary } from "../types";
import { PublishSwitch } from "./PublishSwitch";

type CourseCardProps = { course: CourseSummary; isAdmin: boolean };

// The title link stretches over the whole card, so the card
// is clickable; the publish switch sits above it.
export function CourseCard({ course, isAdmin }: CourseCardProps) {
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
          <CardDescription className="text-base">
            {course.description}
          </CardDescription>
        )}
        {isAdmin && course.is_archived && (
          <CardAction>
            <Badge variant="outline">Zarchiwizowany</Badge>
          </CardAction>
        )}
      </CardHeader>
      {isAdmin && !course.is_archived && (
        <CardFooter className="relative z-10 mt-auto py-1">
          <PublishSwitch course={course} />
        </CardFooter>
      )}
    </Card>
  );
}
