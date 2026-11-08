import type { JSONContent } from "@tiptap/react";

/** True for a missing document or one with only empty paragraphs. */
export function isEmptyDocument(doc: JSONContent | null | undefined): boolean {
  return !doc?.content?.some(
    (node) => node.type !== "paragraph" || (node.content?.length ?? 0) > 0,
  );
}
