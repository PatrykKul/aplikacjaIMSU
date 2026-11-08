import { notFound } from "next/navigation";

import { LessonView } from "@/features/courses/components/LessonView";

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
    <LessonView courseId={parseId(courseId)} lessonId={parseId(lessonId)} />
  );
}
