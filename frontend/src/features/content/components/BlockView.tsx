import { RichTextView } from "@/shared/rich-text/RichTextView";

import type { Block } from "../types";
import { AttachmentView } from "./AttachmentView";

/** One block of a lesson as a card; text in the lesson type scale (17 px, 65 characters). */
export function BlockView({ block }: { block: Block }) {
  return (
    <div className="rounded-xl p-5 ring-1 ring-foreground/10 sm:px-9 sm:py-8">
      {block.type === "text" ? (
        <RichTextView
          content={block.doc}
          className="max-w-[65ch] text-[1.0625rem] leading-[1.65]"
        />
      ) : (
        <AttachmentView attachment={block} />
      )}
    </div>
  );
}
