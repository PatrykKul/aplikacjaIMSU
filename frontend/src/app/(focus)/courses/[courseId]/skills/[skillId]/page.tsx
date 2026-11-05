import { notFound } from "next/navigation";

import { LessonPage } from "@/features/lessons/components/LessonPage";

function parseId(value: string): number {
  const id = Number(value);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return id;
}

export default async function SkillLessonPage(
  props: PageProps<"/courses/[courseId]/skills/[skillId]">,
) {
  const { courseId, skillId } = await props.params;
  const { method } = await props.searchParams;
  return (
    <LessonPage
      courseId={parseId(courseId)}
      skillId={parseId(skillId)}
      method={typeof method === "string" ? method : undefined}
    />
  );
}
