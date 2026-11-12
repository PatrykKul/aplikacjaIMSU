import type { JSONContent } from "@tiptap/react";
import { ArrowLeftIcon, ArrowRightIcon } from "lucide-react";
import Link from "next/link";

import { BlockView } from "@/features/content/components/BlockView";
import type { Block } from "@/features/content/types";
import { cn } from "@/shared/lib/utils";
import { isEmptyDocument } from "@/shared/rich-text/is-empty";
import { RichTextView } from "@/shared/rich-text/RichTextView";
import { buttonVariants } from "@/shared/ui/button";

import type { Lesson } from "../types";

/** "Zarys" / "Wnioski": a TipTap document under a heading. */
export function LessonSection({
  id,
  title,
  doc,
}: {
  id: string;
  title: string;
  doc: JSONContent | null;
}) {
  if (isEmptyDocument(doc) || !doc) {
    return null;
  }
  return (
    <section aria-labelledby={id} className="space-y-3">
      <h2 id={id} className="text-xl font-semibold">
        {title}
      </h2>
      <RichTextView
        content={doc}
        className="max-w-[65ch] text-[1.0625rem] leading-[1.65]"
      />
    </section>
  );
}

/** The blocks of one version as cards. */
export function BlockList({
  blocks,
  label,
}: {
  blocks: Block[];
  label: string;
}) {
  if (blocks.length === 0) {
    return (
      <p className="text-muted-foreground">
        Ta wersja lekcji jest jeszcze pusta.
      </p>
    );
  }
  return (
    <ol role="list" aria-label={label} className="space-y-5">
      {blocks.map((block) => (
        <li key={block.id}>
          <BlockView block={block} />
        </li>
      ))}
    </ol>
  );
}

/** Previous / next lesson; a locked next lesson sends back to the course. */
export function LessonNav({
  lesson,
  courseHref,
}: {
  lesson: Lesson;
  courseHref: string;
}) {
  const lessonHref = (id: number) =>
    `/courses/${lesson.course.id}/lessons/${id}`;
  const nextOpen =
    lesson.next_lesson_id !== null && lesson.next_lesson_unlocked !== false;
  return (
    <nav
      aria-label="Lekcje kursu"
      className="flex flex-wrap items-center justify-between gap-3 pt-4"
    >
      {lesson.previous_lesson_id ? (
        <Link
          href={lessonHref(lesson.previous_lesson_id)}
          className={cn(buttonVariants({ variant: "outline" }))}
        >
          <ArrowLeftIcon data-icon="inline-start" />
          Poprzednia lekcja
        </Link>
      ) : (
        <span />
      )}
      {nextOpen && lesson.next_lesson_id ? (
        <Link
          href={lessonHref(lesson.next_lesson_id)}
          className={cn(buttonVariants(), "ml-auto")}
        >
          Następna lekcja
          <ArrowRightIcon data-icon="inline-end" />
        </Link>
      ) : (
        <div className="ml-auto flex flex-wrap items-center justify-end gap-3">
          {lesson.next_lesson_id && (
            <span className="text-sm text-muted-foreground">
              Następna lekcja otworzy się po zaliczeniu quizu.
            </span>
          )}
          <Link
            href={courseHref}
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            Wróć do kursu
          </Link>
        </div>
      )}
    </nav>
  );
}
