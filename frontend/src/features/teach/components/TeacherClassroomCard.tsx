import Link from "next/link";

import type { ClassroomSummary } from "@/features/classes/types";
import { plural } from "@/shared/lib/plural";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

// The name link stretches over the whole card, so the card is clickable
export function TeacherClassroomCard({
  classroom,
}: {
  classroom: ClassroomSummary;
}) {
  const students = classroom.student_count ?? 0;
  const courses = classroom.course_count;

  return (
    <Card className="relative h-full transition-colors hover:bg-muted/50 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
      <CardHeader>
        <CardTitle className="text-lg">
          <Link
            href={`/teach/classes/${classroom.id}`}
            className="outline-none after:absolute after:inset-0"
          >
            {classroom.name}
          </Link>
        </CardTitle>
        <CardDescription className="text-base">
          {students} {plural(students, "uczeń", "uczniów", "uczniów")} ·{" "}
          {courses} {plural(courses, "kurs", "kursy", "kursów")}
        </CardDescription>
      </CardHeader>
    </Card>
  );
}
