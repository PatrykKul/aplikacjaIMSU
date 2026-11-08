"use client";

import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useRenameLesson } from "@/features/courses/hooks";
import type { LessonSummary } from "@/features/courses/types";
import { errorMessage } from "@/shared/api/error-messages";
import { Button } from "@/shared/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/ui/dialog";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";

import { lessonTitleRules } from "./course-form-rules";

type RenameLessonDialogProps = {
  courseId: number;
  lesson: LessonSummary | null;
  onClose: () => void;
};

export function RenameLessonDialog({
  courseId,
  lesson,
  onClose,
}: RenameLessonDialogProps) {
  return (
    <Dialog
      open={lesson !== null}
      onOpenChange={(open) => {
        if (!open) {
          onClose();
        }
      }}
    >
      <DialogContent>
        {lesson && (
          <RenameForm
            key={lesson.id}
            courseId={courseId}
            lesson={lesson}
            onDone={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  );
}

type RenameFormProps = {
  courseId: number;
  lesson: LessonSummary;
  onDone: () => void;
};

function RenameForm({ courseId, lesson, onDone }: RenameFormProps) {
  const rename = useRenameLesson(courseId);
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ title: string }>({ defaultValues: { title: lesson.title } });

  const onSubmit = handleSubmit(({ title }) =>
    rename.mutate(
      { id: lesson.id, title },
      {
        onSuccess: onDone,
        onError: (error) => toast.error(errorMessage(error)),
      },
    ),
  );

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-4">
      <DialogHeader>
        <DialogTitle>Zmiana nazwy lekcji</DialogTitle>
      </DialogHeader>
      <FormField label="Tytuł lekcji" error={errors.title?.message}>
        {(field) => (
          <Input
            {...field}
            autoComplete="off"
            {...register("title", lessonTitleRules)}
          />
        )}
      </FormField>
      <DialogFooter>
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button type="submit" disabled={rename.isPending}>
          {rename.isPending && <Spinner data-icon="inline-start" />}
          Zapisz
        </Button>
      </DialogFooter>
    </form>
  );
}
