"use client";

import { type Editor, useEditorState } from "@tiptap/react";
import {
  BetweenHorizontalEndIcon,
  BetweenVerticalEndIcon,
  BoldIcon,
  Heading2Icon,
  Heading3Icon,
  ItalicIcon,
  LinkIcon,
  ListIcon,
  ListOrderedIcon,
  type LucideIcon,
  Redo2Icon,
  SigmaIcon,
  TableIcon,
  Trash2Icon,
  UnderlineIcon,
  Undo2Icon,
} from "lucide-react";

import { Button } from "@/shared/ui/button";

type ToolbarButtonProps = {
  label: string;
  icon: LucideIcon;
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
};

function ToolbarButton({
  label,
  icon: Icon,
  onClick,
  active,
  disabled,
}: ToolbarButtonProps) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      aria-label={label}
      title={label}
      aria-pressed={active}
      disabled={disabled}
      className="aria-pressed:bg-muted aria-pressed:text-foreground"
      // Keep the selection in the document while clicking the toolbar
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      <Icon />
    </Button>
  );
}

function Separator() {
  return <span aria-hidden="true" className="mx-1 h-6 w-px bg-border" />;
}

type RichTextToolbarProps = {
  editor: Editor;
  onLink: () => void;
  onMath: () => void;
};

export function RichTextToolbar({
  editor,
  onLink,
  onMath,
}: RichTextToolbarProps) {
  const state = useEditorState({
    editor,
    selector: ({ editor: e }) => ({
      h2: e.isActive("heading", { level: 2 }),
      h3: e.isActive("heading", { level: 3 }),
      bold: e.isActive("bold"),
      italic: e.isActive("italic"),
      underline: e.isActive("underline"),
      bulletList: e.isActive("bulletList"),
      orderedList: e.isActive("orderedList"),
      link: e.isActive("link"),
      table: e.isActive("table"),
      canUndo: e.can().undo(),
      canRedo: e.can().redo(),
    }),
  });
  const chain = () => editor.chain().focus();

  return (
    <div
      role="toolbar"
      aria-label="Formatowanie tekstu"
      className="flex flex-wrap items-center gap-0.5 border-b p-1"
    >
      <ToolbarButton
        label="Nagłówek"
        icon={Heading2Icon}
        active={state.h2}
        onClick={() => chain().toggleHeading({ level: 2 }).run()}
      />
      <ToolbarButton
        label="Podtytuł"
        icon={Heading3Icon}
        active={state.h3}
        onClick={() => chain().toggleHeading({ level: 3 }).run()}
      />
      <Separator />
      <ToolbarButton
        label="Pogrubienie"
        icon={BoldIcon}
        active={state.bold}
        onClick={() => chain().toggleBold().run()}
      />
      <ToolbarButton
        label="Kursywa"
        icon={ItalicIcon}
        active={state.italic}
        onClick={() => chain().toggleItalic().run()}
      />
      <ToolbarButton
        label="Podkreślenie"
        icon={UnderlineIcon}
        active={state.underline}
        onClick={() => chain().toggleUnderline().run()}
      />
      <Separator />
      <ToolbarButton
        label="Lista"
        icon={ListIcon}
        active={state.bulletList}
        onClick={() => chain().toggleBulletList().run()}
      />
      <ToolbarButton
        label="Lista numerowana"
        icon={ListOrderedIcon}
        active={state.orderedList}
        onClick={() => chain().toggleOrderedList().run()}
      />
      <Separator />
      <ToolbarButton
        label="Link"
        icon={LinkIcon}
        active={state.link}
        onClick={onLink}
      />
      <ToolbarButton label="Wzór" icon={SigmaIcon} onClick={onMath} />
      <Separator />
      {state.table ? (
        <>
          <ToolbarButton
            label="Dodaj wiersz"
            icon={BetweenHorizontalEndIcon}
            onClick={() => chain().addRowAfter().run()}
          />
          <ToolbarButton
            label="Dodaj kolumnę"
            icon={BetweenVerticalEndIcon}
            onClick={() => chain().addColumnAfter().run()}
          />
          <ToolbarButton
            label="Usuń tabelę"
            icon={Trash2Icon}
            onClick={() => chain().deleteTable().run()}
          />
        </>
      ) : (
        <ToolbarButton
          label="Tabela"
          icon={TableIcon}
          onClick={() =>
            chain().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
          }
        />
      )}
      <Separator />
      <ToolbarButton
        label="Cofnij"
        icon={Undo2Icon}
        disabled={!state.canUndo}
        onClick={() => chain().undo().run()}
      />
      <ToolbarButton
        label="Ponów"
        icon={Redo2Icon}
        disabled={!state.canRedo}
        onClick={() => chain().redo().run()}
      />
    </div>
  );
}
