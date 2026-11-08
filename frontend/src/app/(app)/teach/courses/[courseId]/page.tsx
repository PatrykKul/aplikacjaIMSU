import { notFound } from "next/navigation";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { CourseEditor } from "@/features/teach/components/CourseEditor";

export default async function TeachCoursePage(
  props: PageProps<"/teach/courses/[courseId]">,
) {
  const { courseId } = await props.params;
  const id = Number(courseId);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return (
    <RoleGate roles={["teacher"]}>
      <CourseEditor courseId={id} />
    </RoleGate>
  );
}
