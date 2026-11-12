import { redirect } from "next/navigation";

// The quiz is edited in the "Quiz (pula)" tab of the lesson editor (v3)
export default async function TeachLessonQuizPage(
  props: PageProps<"/teach/courses/[courseId]/lessons/[lessonId]/quiz">,
) {
  const { courseId, lessonId } = await props.params;
  redirect(`/teach/courses/${courseId}/lessons/${lessonId}?tab=quiz`);
}
