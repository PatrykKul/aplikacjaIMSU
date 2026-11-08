import { notFound } from "next/navigation";

import { CourseView } from "@/features/courses/components/CourseView";

// Any role: the API decides who may see the course (the author too, as a preview)
export default async function CoursePage(
  props: PageProps<"/courses/[courseId]">,
) {
  const { courseId } = await props.params;
  const id = Number(courseId);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return <CourseView courseId={id} />;
}
