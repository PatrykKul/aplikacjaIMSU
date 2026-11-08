"use client";

import type { JSONContent } from "@tiptap/react";
import {
  ArrowDownIcon,
  ArrowUpIcon,
  PencilIcon,
  PilcrowIcon,
  Trash2Icon,
} from "lucide-react";

import { KIND_INFO } from "@/features/content/attachment-kinds";
import type { Block } from "@/features/content/types";
import { RichTextEditor } from "@/shared/rich-text/RichTextEditor";
import { Button } from "@/shared/ui/button";

import { AttachmentSummary } from "./AttachmentSummary";

type BlockCardProps = {
  block: Block;
  /** Position in the lesson, from 1 (names the buttons for screen readers). */
  number: number;
  isFirst: boolean;
  isLast: boolean;
  onMove: (step: -1 | 1) => void;
  onRemove: () => void;
  onEditAttachment: () => void;
  onTextChange: (doc: JSONContent) => void;
};

export function BlockCard({
  block,
  number,
  isFirst,
  isLast,
  onMove,
  onRemove,
  onEditAttachment,
  onTextChange,
}: BlockCardProps) {
  const isText = block.type === "text";
  const label = isText ? "Tekst" : KIND_INFO[block.kind].label;
  const Icon = isText ? PilcrowIcon : KIND_INFO[block.kind].icon;
  const name = `blok ${number} (${label.toLowerCase()})`;

  return (
    <div className="overflow-hidden rounded-xl ring-1 ring-foreground/10">
      <div className="flex items-center gap-2 border-b bg-muted/50 py-1 pr-1 pl-4">
        <Icon aria-hidden="true" className="size-4 text-muted-foreground" />
        <span className="flex-1 text-sm font-medium">{label}</span>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Przesuń wyżej: ${name}`}
          title="Przesuń wyżej"
          disabled={isFirst}
          onClick={() => onMove(-1)}
        >
          <ArrowUpIcon />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Przesuń niżej: ${name}`}
          title="Przesuń niżej"
          disabled={isLast}
          onClick={() => onMove(1)}
        >
          <ArrowDownIcon />
        </Button>
        {!isText && (
          <Button
            variant="ghost"
            size="icon"
            aria-label={`Edytuj: ${name}`}
            title="Edytuj"
            onClick={onEditAttachment}
          >
            <PencilIcon />
          </Button>
        )}
        <Button
          variant="ghost"
          size="icon"
          aria-label={`Usuń: ${name}`}
          title="Usuń"
          onClick={onRemove}
        >
          <Trash2Icon />
        </Button>
      </div>
      <div className="p-4">
        {block.type === "text" ? (
          <RichTextEditor
            label={`Tekst, ${name}`}
            initialContent={block.doc}
            onChange={onTextChange}
          />
        ) : (
          <AttachmentSummary attachment={block} />
        )}
      </div>
    </div>
  );
}
