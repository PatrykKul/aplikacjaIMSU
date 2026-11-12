import { notFound } from "next/navigation";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { StudentDetailPage } from "@/features/teach/components/StudentDetailPage";

function parseId(value: string): number {
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return id;
}

export default async function TeachStudentPage(
  props: PageProps<"/teach/courses/[courseId]/students/[studentId]">,
) {
  const { courseId, studentId } = await props.params;
  return (
    <RoleGate roles={["teacher"]}>
      <StudentDetailPage
        courseId={parseId(courseId)}
        studentId={parseId(studentId)}
      />
    </RoleGate>
  );
}
