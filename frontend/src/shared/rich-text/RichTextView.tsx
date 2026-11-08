"use client";

import "katex/dist/katex.min.css";

import { EditorContent, type JSONContent, useEditor } from "@tiptap/react";

import { cn } from "@/shared/lib/utils";

import { richTextExtensions } from "./extensions";

type RichTextViewProps = { content: JSONContent; className?: string };

/**
 * Read-only document. Rendered by TipTap from its schema (no raw HTML),
 * so unknown nodes are dropped instead of executed.
 */
export function RichTextView({ content, className }: RichTextViewProps) {
  const editor = useEditor({
    extensions: richTextExtensions(),
    content,
    editable: false,
    immediatelyRender: false,
  });

  return (
    <EditorContent editor={editor} className={cn("rich-text", className)} />
  );
}
