import { notFound } from "next/navigation";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { CoursePanel } from "@/features/teach/components/CoursePanel";

export default async function TeachCoursePanelPage(
  props: PageProps<"/teach/courses/[courseId]/panel">,
) {
  const { courseId } = await props.params;
  const id = Number(courseId);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return (
    <RoleGate roles={["teacher"]}>
      <CoursePanel courseId={id} />
    </RoleGate>
  );
}
