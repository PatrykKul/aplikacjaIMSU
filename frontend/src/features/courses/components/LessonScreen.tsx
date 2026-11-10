"use client";

import { useCurrentUser } from "@/features/auth/hooks";

import { LessonPreview } from "./LessonPreview";
import { LessonView } from "./LessonView";

type LessonScreenProps = { courseId: number; lessonId: number };

/** Students get the lesson matched to their style; teachers and admins a preview. */
export function LessonScreen(props: LessonScreenProps) {
  const { data: user } = useCurrentUser();
  return user?.role === "student" ? (
    <LessonView {...props} />
  ) : (
    <LessonPreview {...props} />
  );
}
