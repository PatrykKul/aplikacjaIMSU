"use client";

import type { JSONContent } from "@tiptap/react";
import { CheckIcon, CircleIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import {
  type Attachment,
  type Block,
  type Form,
  FORM_LABELS,
  newBlockId,
} from "@/features/content/types";
import { cn } from "@/shared/lib/utils";

import { useSaveVersion } from "../hooks";
import { VERSION_INTROS, versionRequirements } from "../readiness";
import { type AttachmentTarget, AttachmentDialog } from "./AttachmentDialog";
import { BlockCard } from "./BlockCard";
import { InsertBlockBar } from "./InsertBlockBar";
import { SaveBar } from "./SaveBar";
import { SaveErrorAlert } from "./SaveErrorAlert";

/** Where a new block goes: before the block at `index` (`blocks.length` = at the end). */
type Insertion = { index: number };

const FORM_CLASSES: Record<Form, string> = {
  V: "border-form-v",
  A: "border-form-a",
  K: "border-form-k",
};

/** What this version must contain (R11), checked live on the unsaved blocks. */
function VersionRequirements({
  form,
  blocks,
}: {
  form: Form;
  blocks: Block[];
}) {
  const requirements = versionRequirements(form, blocks);
  return (
    <section
      aria-label={`Co musi zawierać wersja ${FORM_LABELS[form]}`}
      className={cn("space-y-3 border-l-4 py-1 pl-4", FORM_CLASSES[form])}
    >
      <p className="max-w-[65ch] text-base">{VERSION_INTROS[form]}</p>
      <ul role="list" className="space-y-1 text-sm">
        {requirements.map(({ label, met }) => (
          <li key={label} className="flex items-center gap-2">
            {met ? (
              <CheckIcon aria-hidden="true" className="size-4" />
            ) : (
              <CircleIcon
                aria-hidden="true"
                className="size-4 text-muted-foreground"
              />
            )}
            <span className={cn(!met && "text-muted-foreground")}>{label}</span>
            <span className="sr-only">{met ? "(jest)" : "(brakuje)"}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

type VersionEditorProps = {
  lessonId: number;
  form: Form;
  initialBlocks: Block[];
  onDirtyChange: (dirty: boolean) => void;
};

/** Block editor of one version (V, A or K) of a lesson. */
export function VersionEditor({
  lessonId,
  form,
  initialBlocks,
  onDirtyChange,
}: VersionEditorProps) {
  const save = useSaveVersion(lessonId, form);
  const [blocks, setBlocks] = useState(initialBlocks);
  const [dirty, setDirty] = useState(false);
  const [attachmentTarget, setAttachmentTarget] =
    useState<AttachmentTarget | null>(null);
  const [insertion, setInsertion] = useState<Insertion | null>(null);

  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);

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
        toast.success(`Zapisano wersję ${FORM_LABELS[form].toLowerCase()}.`);
      },
    });
  }

  return (
    <div className="space-y-6">
      <SaveBar
        label={`Zapisz wersję ${form}`}
        dirty={dirty}
        pending={save.isPending}
        onSave={onSave}
      />

      {save.isError && <SaveErrorAlert error={save.error} />}

      <VersionRequirements form={form} blocks={blocks} />

      {blocks.length === 0 ? (
        <p className="text-muted-foreground">
          Ta wersja jest pusta. Dodaj pierwszy tekst albo załącznik.
        </p>
      ) : (
        <ol
          role="list"
          aria-label={`Bloki wersji ${FORM_LABELS[form]}`}
          className="space-y-2"
        >
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
        place="na końcu wersji"
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
