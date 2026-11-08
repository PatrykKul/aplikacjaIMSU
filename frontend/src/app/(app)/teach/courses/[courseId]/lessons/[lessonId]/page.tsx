import { notFound } from "next/navigation";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { LessonEditor } from "@/features/teach/components/LessonEditor";

function parseId(value: string): number {
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return id;
}

export default async function TeachLessonPage(
  props: PageProps<"/teach/courses/[courseId]/lessons/[lessonId]">,
) {
  const { courseId, lessonId } = await props.params;
  return (
    <RoleGate roles={["teacher"]}>
      <LessonEditor courseId={parseId(courseId)} lessonId={parseId(lessonId)} />
    </RoleGate>
  );
}
