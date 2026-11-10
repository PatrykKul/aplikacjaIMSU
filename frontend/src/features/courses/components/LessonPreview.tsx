"use client";

import { BlockView } from "@/features/content/components/BlockView";
import { useLessonBlocks } from "@/features/content/hooks";

import { LessonFrame } from "./LessonFrame";

type LessonPreviewProps = { courseId: number; lessonId: number };

/**
 * A lesson for teachers and admins: the saved blocks, every material expanded.
 * Uses the lesson editor's query, so the preview is fresh right after saving.
 */
export function LessonPreview({ courseId, lessonId }: LessonPreviewProps) {
  const blocks = useLessonBlocks(lessonId);
  return (
    <LessonFrame
      courseId={courseId}
      lessonId={lessonId}
      blocks={blocks}
      intro={
        <p className="text-sm text-muted-foreground">
          Widać wszystkie materiały. Uczeń widzi rozwinięte materiały swojego
          stylu, a pozostałe zwinięte – może je rozwinąć.
        </p>
      }
      renderBlock={(block) => <BlockView block={block} />}
    />
  );
}
