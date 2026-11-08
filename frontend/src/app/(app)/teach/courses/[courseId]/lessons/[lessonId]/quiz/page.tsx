import { notFound } from "next/navigation";

import { QuizEditor } from "@/features/assessment/components/QuizEditor";
import { RoleGate } from "@/features/auth/components/RoleGate";

function parseId(value: string): number {
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return id;
}

export default async function TeachLessonQuizPage(
  props: PageProps<"/teach/courses/[courseId]/lessons/[lessonId]/quiz">,
) {
  const { courseId, lessonId } = await props.params;
  return (
    <RoleGate roles={["teacher"]}>
      <QuizEditor courseId={parseId(courseId)} lessonId={parseId(lessonId)} />
    </RoleGate>
  );
}
