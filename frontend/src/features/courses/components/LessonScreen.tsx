"use client";

import { useCurrentUser } from "@/features/auth/hooks";

import { LessonPreview } from "./LessonPreview";
import { LessonStudy } from "./LessonStudy";

type LessonScreenProps = { courseId: number; lessonId: number };

/** Students study the lesson in one form; teachers and admins get a preview. */
export function LessonScreen(props: LessonScreenProps) {
  const { data: user } = useCurrentUser();
  return user?.role === "student" ? (
    <LessonStudy {...props} />
  ) : (
    <LessonPreview {...props} />
  );
}
