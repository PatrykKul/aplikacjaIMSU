"use client";

import { BlockView } from "@/features/content/components/BlockView";
import { PersonalizationNote } from "@/features/learning-style/components/PersonalizationNote";
import { usePersonalizedBlocks } from "@/features/learning-style/hooks";

import { LessonFrame } from "./LessonFrame";

type LessonViewProps = { courseId: number; lessonId: number };

/** A lesson as the student sees it, matched to the learning style. */
export function LessonView({ courseId, lessonId }: LessonViewProps) {
  const blocks = usePersonalizedBlocks(lessonId);
  return (
    <LessonFrame
      courseId={courseId}
      lessonId={lessonId}
      blocks={blocks}
      intro={blocks.data && <PersonalizationNote data={blocks.data} />}
      renderBlock={(block) => <BlockView block={block} />}
    />
  );
}
