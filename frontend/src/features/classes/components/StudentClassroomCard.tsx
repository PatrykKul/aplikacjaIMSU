import Link from "next/link";

import { plural } from "@/shared/lib/plural";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

import type { ClassroomSummary } from "../types";

// The name link stretches over the whole card, so the card is clickable
export function StudentClassroomCard({
  classroom,
}: {
  classroom: ClassroomSummary;
}) {
  const courses = classroom.course_count;

  return (
    <Card className="relative h-full transition-colors hover:bg-muted/50 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
      <CardHeader>
        <CardTitle className="text-lg">
          <Link
            href={`/classes/${classroom.id}`}
            className="outline-none after:absolute after:inset-0"
          >
            {classroom.name}
          </Link>
        </CardTitle>
        <CardDescription className="text-base">
          Nauczyciel: {classroom.teacher.display_name} · {courses}{" "}
          {plural(courses, "kurs", "kursy", "kursów")}
        </CardDescription>
      </CardHeader>
    </Card>
  );
}
