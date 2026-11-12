"use client";

import type { JSONContent } from "@tiptap/react";
import { useEffect, useState } from "react";
import { toast } from "sonner";

import { RichTextEditor } from "@/shared/rich-text/RichTextEditor";
import { FieldGroup } from "@/shared/ui/field";
import { FormField } from "@/shared/ui/form-field";

import { useUpdateLesson } from "../hooks";
import type { LessonUpdateInput, TeacherLesson } from "../types";
import { SaveBar } from "./SaveBar";
import { SaveErrorAlert } from "./SaveErrorAlert";

type Docs = { outline?: JSONContent; conclusions?: JSONContent };

type OutlineEditorProps = {
  lesson: TeacherLesson;
  onDirtyChange: (dirty: boolean) => void;
};

/** "Zarys i wnioski": the same for every version of the lesson. */
export function OutlineEditor({ lesson, onDirtyChange }: OutlineEditorProps) {
  const update = useUpdateLesson(lesson.id);
  // Only edited documents are kept (and sent): the editors hold their own content
  const [changes, setChanges] = useState<Docs>({});
  const dirty =
    changes.outline !== undefined || changes.conclusions !== undefined;

  useEffect(() => {
    onDirtyChange(dirty);
  }, [dirty, onDirtyChange]);

  function onSave() {
    const data: LessonUpdateInput = { ...changes };
    update.mutate(data, {
      onSuccess: () => {
        setChanges({});
        toast.success("Zapisano zarys i wnioski.");
      },
    });
  }

  return (
    <div className="space-y-6">
      <SaveBar
        label="Zapisz zarys i wnioski"
        dirty={dirty}
        pending={update.isPending}
        onSave={onSave}
      />

      {update.isError && <SaveErrorAlert error={update.error} />}

      <p className="max-w-[65ch] text-base text-muted-foreground">
        Zarys i wnioski widzi każdy uczeń, niezależnie od wersji, w której
        przerabia lekcję. Zarys pojawia się też w streszczeniu kursu.
      </p>

      <FieldGroup>
        <FormField
          label="Zarys"
          description="2–3 zdania: czego dotyczy lekcja i czego uczeń się z niej dowie."
        >
          {(field) => (
            <RichTextEditor
              {...field}
              label="Zarys"
              initialContent={lesson.outline}
              onChange={(doc) =>
                setChanges((current) => ({ ...current, outline: doc }))
              }
            />
          )}
        </FormField>
        <FormField
          label="Wnioski"
          description="3–4 punkty do zapamiętania. Uczeń zobaczy je po treści lekcji, przed quizem."
        >
          {(field) => (
            <RichTextEditor
              {...field}
              label="Wnioski"
              initialContent={lesson.conclusions}
              onChange={(doc) =>
                setChanges((current) => ({ ...current, conclusions: doc }))
              }
            />
          )}
        </FormField>
      </FieldGroup>
    </div>
  );
}
