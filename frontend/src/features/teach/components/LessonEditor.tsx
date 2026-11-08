"use client";

import type { JSONContent } from "@tiptap/react";
import { EyeIcon } from "lucide-react";
import Link from "next/link";
import { type MouseEvent, useState } from "react";
import { toast } from "sonner";

import { useLessonBlocks, useSaveBlocks } from "@/features/content/hooks";
import {
  type Attachment,
  type Block,
  newBlockId,
} from "@/features/content/types";
import { useLesson } from "@/features/courses/hooks";
import type { Lesson } from "@/features/courses/types";
import { ApiError } from "@/shared/api/client";
import { errorMessage } from "@/shared/api/error-messages";
import {
  confirmLeave,
  useUnsavedChangesWarning,
} from "@/shared/hooks/use-unsaved-changes-warning";
import { PageMessage } from "@/shared/layout/page-states";
import { cn } from "@/shared/lib/utils";
import { Button, buttonVariants } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

import { type AttachmentTarget, AttachmentDialog } from "./AttachmentDialog";
import { BlockCard } from "./BlockCard";
import { InsertBlockBar } from "./InsertBlockBar";

type LessonEditorProps = { courseId: number; lessonId: number };

export function LessonEditor({ courseId, lessonId }: LessonEditorProps) {
  const lesson = useLesson(lessonId);
  const blocks = useLessonBlocks(lessonId);

  if (lesson.isPending || blocks.isPending) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="size-6" />
      </div>
    );
  }
  const error = lesson.error ?? blocks.error;
  // A lesson of another course in the address is "not found" as well
  if (
    (error instanceof ApiError && error.status === 404) ||
    (lesson.data && lesson.data.course.id !== courseId)
  ) {
    return (
      <PageMessage
        title="Nie znaleziono lekcji"
        description="Lekcja nie istnieje albo została usunięta."
        action={
          <Link
            href={`/teach/courses/${courseId}`}
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć do kursu
          </Link>
        }
      />
    );
  }
  if (error || !lesson.data || !blocks.data) {
    return (
      <PageMessage
        title="Nie udało się wczytać lekcji"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button
            onClick={() => {
              void lesson.refetch();
              void blocks.refetch();
            }}
          >
            Spróbuj ponownie
          </Button>
        }
      />
    );
  }

  return (
    <BlockEditor lesson={lesson.data} initialBlocks={blocks.data.blocks} />
  );
}

/** Where a new block goes: before the block at `index` (`blocks.length` = at the end). */
type Insertion = { index: number };

type BlockEditorProps = { lesson: Lesson; initialBlocks: Block[] };

function BlockEditor({ lesson, initialBlocks }: BlockEditorProps) {
  const save = useSaveBlocks(lesson.id);
  const [blocks, setBlocks] = useState(initialBlocks);
  const [dirty, setDirty] = useState(false);
  const [attachmentTarget, setAttachmentTarget] =
    useState<AttachmentTarget | null>(null);
  const [insertion, setInsertion] = useState<Insertion | null>(null);
  useUnsavedChangesWarning(dirty);

  const courseHref = `/teach/courses/${lesson.course.id}`;

  function leaveUnlessDirty(event: MouseEvent) {
    if (!confirmLeave(dirty)) {
      event.preventDefault();
    }
  }

  function change(next: Block[]) {
    setBlocks(next);
    setDirty(true);
  }

  function insert(index: number, block: Block) {
    change([...blocks.slice(0, index), block, ...blocks.slice(index)]);
  }

  function move(index: number, step: -1 | 1) {
    const next = [...blocks];
    [next[index], next[index + step]] = [next[index + step], next[index]];
    change(next);
  }

  function updateText(id: string, doc: JSONContent) {
    setBlocks((current) =>
      current.map((block) =>
        block.id === id && block.type === "text" ? { ...block, doc } : block,
      ),
    );
    setDirty(true);
  }

  function saveAttachment(attachment: Attachment) {
    if (insertion) {
      insert(insertion.index, attachment);
    } else {
      change(blocks.map((b) => (b.id === attachment.id ? attachment : b)));
    }
    setAttachmentTarget(null);
    setInsertion(null);
  }

  function addText(index: number) {
    insert(index, {
      id: newBlockId(),
      type: "text",
      doc: { type: "doc", content: [{ type: "paragraph" }] },
    });
  }

  function addAttachment(index: number) {
    setInsertion({ index });
    setAttachmentTarget({ attachment: null });
  }

  function onSave() {
    save.mutate(blocks, {
      onSuccess: (saved) => {
        // Same ids, so the text editors stay mounted; display fields come from the server
        setBlocks(saved.blocks);
        setDirty(false);
        toast.success("Zapisano lekcję.");
      },
      onError: (error) => toast.error(errorMessage(error)),
    });
  }

  return (
    <div className="space-y-6">
      <div className="space-y-3">
        <nav aria-label="Ścieżka" className="text-sm text-muted-foreground">
          <Link
            href="/teach"
            className="hover:text-foreground"
            onClick={leaveUnlessDirty}
          >
            Moje kursy
          </Link>
          <span aria-hidden="true"> / </span>
          <Link
            href={courseHref}
            className="hover:text-foreground"
            onClick={leaveUnlessDirty}
          >
            {lesson.course.title}
          </Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{lesson.title}</span>
        </nav>
        <h1 className="text-2xl font-semibold tracking-tight">
          {lesson.title}
        </h1>
      </div>

      {/* Stays at the top while scrolling a long lesson */}
      <div className="sticky top-16 z-30 -mx-4 flex items-center gap-3 border-b bg-background/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
        <Button onClick={onSave} disabled={!dirty || save.isPending}>
          {save.isPending && <Spinner data-icon="inline-start" />}
          Zapisz lekcję
        </Button>
        <p className="flex-1 text-sm text-muted-foreground" aria-live="polite">
          {dirty ? "Masz niezapisane zmiany." : "Wszystkie zmiany zapisane."}
        </p>
        {/* The preview shows the saved lesson, so unsaved changes need a confirmation */}
        <Link
          href={`/courses/${lesson.course.id}/lessons/${lesson.id}`}
          className={cn(buttonVariants({ variant: "outline" }))}
          onClick={leaveUnlessDirty}
        >
          <EyeIcon data-icon="inline-start" />
          Podgląd
        </Link>
      </div>

      {blocks.length === 0 ? (
        <p className="text-muted-foreground">
          Lekcja jest pusta. Dodaj pierwszy tekst albo załącznik.
        </p>
      ) : (
        <ol role="list" aria-label="Bloki lekcji" className="space-y-2">
          {blocks.map((block, index) => (
            <li key={block.id} className="space-y-2">
              {index > 0 && (
                <InsertBlockBar
                  compact
                  place={`przed blokiem ${index + 1}`}
                  onText={() => addText(index)}
                  onAttachment={() => addAttachment(index)}
                />
              )}
              <BlockCard
                block={block}
                number={index + 1}
                isFirst={index === 0}
                isLast={index === blocks.length - 1}
                onMove={(step) => move(index, step)}
                onRemove={() => change(blocks.filter((b) => b.id !== block.id))}
                onEditAttachment={() => {
                  if (block.type === "attachment") {
                    setInsertion(null);
                    setAttachmentTarget({ attachment: block });
                  }
                }}
                onTextChange={(doc) => updateText(block.id, doc)}
              />
            </li>
          ))}
        </ol>
      )}

      <InsertBlockBar
        place="na końcu lekcji"
        onText={() => addText(blocks.length)}
        onAttachment={() => addAttachment(blocks.length)}
      />

      <AttachmentDialog
        target={attachmentTarget}
        onClose={() => {
          setAttachmentTarget(null);
          setInsertion(null);
        }}
        onSave={saveAttachment}
      />
    </div>
  );
}
