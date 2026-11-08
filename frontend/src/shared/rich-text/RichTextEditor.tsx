"use client";

import "katex/dist/katex.min.css";

import { EditorContent, type JSONContent, useEditor } from "@tiptap/react";
import { useLayoutEffect, useRef, useState } from "react";

import { cn } from "@/shared/lib/utils";
import type { FieldControlProps } from "@/shared/ui/form-field";

import { richTextExtensions } from "./extensions";
import { LinkDialog } from "./LinkDialog";
import { MathDialog, type MathTarget } from "./MathDialog";
import { RichTextToolbar } from "./RichTextToolbar";

type RichTextEditorProps = Partial<FieldControlProps> & {
  /** Accessible name: <label for> does not name a contenteditable element. */
  label: string;
  /** Content when the editor mounts; later changes come only from the editor. */
  initialContent: JSONContent | null;
  onChange: (doc: JSONContent) => void;
  className?: string;
};

export function RichTextEditor({
  initialContent,
  onChange,
  className,
  label,
  id,
  "aria-invalid": invalid,
  "aria-describedby": describedBy,
}: RichTextEditorProps) {
  const [mathTarget, setMathTarget] = useState<MathTarget | null>(null);
  const [linkHref, setLinkHref] = useState<string | null>(null);
  // The editor is created once; the ref always calls the latest callback
  const onChangeRef = useRef(onChange);
  useLayoutEffect(() => {
    onChangeRef.current = onChange;
  });

  const editor = useEditor({
    extensions: richTextExtensions({
      onMathClick: (latex, pos) => setMathTarget({ latex, pos }),
    }),
    content: initialContent ?? "",
    immediatelyRender: false,
    editorProps: {
      attributes: {
        ...(id && { id }),
        ...(invalid && { "aria-invalid": "true" }),
        ...(describedBy && { "aria-describedby": describedBy }),
        "aria-label": label,
        role: "textbox",
        "aria-multiline": "true",
        class: "rich-text min-h-40 px-4 py-3 text-base outline-none",
      },
    },
    onUpdate: ({ editor: e }) => onChangeRef.current(e.getJSON()),
  });

  if (!editor) {
    return <div className={cn("min-h-52 rounded-lg border", className)} />;
  }

  return (
    <div
      className={cn(
        "overflow-hidden rounded-lg border border-input focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50 has-aria-invalid:border-destructive",
        className,
      )}
    >
      <RichTextToolbar
        editor={editor}
        onLink={() => setLinkHref(editor.getAttributes("link").href ?? "")}
        onMath={() => setMathTarget({ latex: "" })}
      />
      <EditorContent editor={editor} />

      <MathDialog
        target={mathTarget}
        onClose={() => setMathTarget(null)}
        onSave={(latex, pos) => {
          const chain = editor.chain().focus();
          if (pos === undefined) {
            chain.insertInlineMath({ latex }).run();
          } else {
            chain.updateInlineMath({ latex, pos }).run();
          }
          setMathTarget(null);
        }}
        onRemove={(pos) => {
          editor.chain().focus().deleteInlineMath({ pos }).run();
          setMathTarget(null);
        }}
      />
      <LinkDialog
        href={linkHref}
        onClose={() => setLinkHref(null)}
        onSave={(href) => {
          const chain = editor.chain().focus().extendMarkRange("link");
          if (editor.state.selection.empty && !editor.isActive("link")) {
            // No selected text: insert the address itself as the link text
            chain
              .insertContent({
                type: "text",
                text: href,
                marks: [{ type: "link", attrs: { href } }],
              })
              .run();
          } else {
            chain.setLink({ href }).run();
          }
          setLinkHref(null);
        }}
        onRemove={() => {
          editor.chain().focus().extendMarkRange("link").unsetLink().run();
          setLinkHref(null);
        }}
      />
    </div>
  );
}
