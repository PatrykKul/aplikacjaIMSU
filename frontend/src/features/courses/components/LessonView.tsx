"use client";

import { useQueryClient } from "@tanstack/react-query";
import { ChevronUpIcon } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { lessonQuizKey } from "@/features/assessment/hooks";
import { BlockView } from "@/features/content/components/BlockView";
import { CollapsedMaterial } from "@/features/learning-style/components/CollapsedMaterial";
import { PersonalizationNote } from "@/features/learning-style/components/PersonalizationNote";
import { learningStyleError } from "@/features/learning-style/errors";
import {
  useOpenMaterial,
  usePersonalizedBlocks,
} from "@/features/learning-style/hooks";
import { Button } from "@/shared/ui/button";

import { LessonFrame } from "./LessonFrame";

type LessonViewProps = { courseId: number; lessonId: number };

/** A lesson as the student sees it, matched to the learning style. */
export function LessonView({ courseId, lessonId }: LessonViewProps) {
  const queryClient = useQueryClient();
  const blocks = usePersonalizedBlocks(lessonId);
  const openMaterial = useOpenMaterial(lessonId);
  // Expanded / collapsed by the student in this view; the default comes from the server
  const [shown, setShown] = useState<Record<string, boolean>>({});

  const collapsed = new Set(blocks.data?.collapsed_block_ids);
  const opened = new Set(blocks.data?.opened_block_ids);

  function show(blockId: string) {
    setShown((prev) => ({ ...prev, [blockId]: true }));
    if (!opened.has(blockId)) {
      openMaterial.mutate(blockId, {
        // The quiz may now include questions about this material
        onSuccess: () =>
          queryClient.invalidateQueries({ queryKey: lessonQuizKey(lessonId) }),
        onError: (error) => toast.error(learningStyleError(error)),
      });
    }
  }

  return (
    <LessonFrame
      courseId={courseId}
      lessonId={lessonId}
      blocks={blocks}
      intro={blocks.data && <PersonalizationNote data={blocks.data} />}
      renderBlock={(block) => {
        if (block.type !== "attachment" || !collapsed.has(block.id)) {
          return <BlockView block={block} />;
        }
        if (!(shown[block.id] ?? opened.has(block.id))) {
          return (
            <CollapsedMaterial
              attachment={block}
              onShow={() => show(block.id)}
            />
          );
        }
        return (
          <div className="space-y-2">
            <BlockView block={block} />
            <Button
              variant="ghost"
              onClick={() =>
                setShown((prev) => ({ ...prev, [block.id]: false }))
              }
            >
              <ChevronUpIcon data-icon="inline-start" />
              Zwiń materiał
            </Button>
          </div>
        );
      }}
    />
  );
}
