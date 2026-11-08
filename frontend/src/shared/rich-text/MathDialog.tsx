"use client";

import katex from "katex";
import { useState } from "react";

import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";

/** Formula being edited: `pos` is set for an existing formula, empty for a new one. */
export type MathTarget = { latex: string; pos?: number };

type MathDialogProps = {
  target: MathTarget | null;
  onClose: () => void;
  onSave: (latex: string, pos?: number) => void;
  onRemove: (pos: number) => void;
};

function preview(latex: string): string {
  // KaTeX output with `trust: false` (default) contains no scripts or links
  return katex.renderToString(latex, { throwOnError: false });
}

export function MathDialog({
  target,
  onClose,
  onSave,
  onRemove,
}: MathDialogProps) {
  return (
    <Dialog
      open={target !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent>
        {target && (
          // Remount per formula, so the field starts with its LaTeX
          <MathForm
            key={target.pos ?? "new"}
            target={target}
            onSave={onSave}
            onRemove={onRemove}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

type MathFormProps = Omit<MathDialogProps, "onClose"> & { target: MathTarget };

function MathForm({ target, onSave, onRemove }: MathFormProps) {
  const [latex, setLatex] = useState(target.latex);
  const [error, setError] = useState<string>();
  const isNew = target.pos === undefined;

  return (
    <form
      noValidate
      className="grid gap-4"
      onSubmit={(event) => {
        event.preventDefault();
        // The dialog is portaled, but React still bubbles the submit
        // to the form around the editor (e.g. the course form)
        event.stopPropagation();
        if (latex.trim() === "") {
          setError("Wpisz wzór, np. \\frac{1}{2}.");
          return;
        }
        onSave(latex.trim(), target.pos);
      }}
    >
      <DialogHeader>
        <DialogTitle>{isNew ? "Nowy wzór" : "Edycja wzoru"}</DialogTitle>
        <DialogDescription>
          Wzór w zapisie LaTeX. W tekście możesz też wpisać go między znakami $,
          np. $\frac{"{1}{4}"}$.
        </DialogDescription>
      </DialogHeader>
      <FormField label="Wzór (LaTeX)" error={error}>
        {(control) => (
          <Input
            {...control}
            value={latex}
            autoComplete="off"
            spellCheck={false}
            className="font-mono"
            onChange={(event) => {
              setLatex(event.target.value);
              setError(undefined);
            }}
          />
        )}
      </FormField>
      <div
        aria-label="Podgląd wzoru"
        className="min-h-12 rounded-lg bg-muted px-3 py-2 text-lg"
        dangerouslySetInnerHTML={{ __html: latex.trim() ? preview(latex) : "" }}
      />
      <DialogFooter>
        {!isNew && (
          <Button
            type="button"
            variant="destructive"
            className="sm:mr-auto"
            onClick={() => onRemove(target.pos!)}
          >
            Usuń wzór
          </Button>
        )}
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button type="submit">{isNew ? "Wstaw" : "Zapisz"}</Button>
      </DialogFooter>
    </form>
  );
}
