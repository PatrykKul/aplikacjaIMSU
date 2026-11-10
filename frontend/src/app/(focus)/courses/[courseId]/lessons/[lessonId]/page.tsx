import { notFound } from "next/navigation";

import { LessonScreen } from "@/features/courses/components/LessonScreen";

function parseId(value: string): number {
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return id;
}

export default async function LessonPage(
  props: PageProps<"/courses/[courseId]/lessons/[lessonId]">,
) {
  const { courseId, lessonId } = await props.params;
  return (
    <LessonScreen courseId={parseId(courseId)} lessonId={parseId(lessonId)} />
  );
}
