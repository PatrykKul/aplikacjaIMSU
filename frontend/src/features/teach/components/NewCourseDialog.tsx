"use client";

import { AlertCircleIcon } from "lucide-react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useCreateCourse } from "@/features/courses/hooks";
import { errorMessage } from "@/shared/api/error-messages";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
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
import { FieldGroup } from "@/shared/ui/field";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";
import { Textarea } from "@/shared/ui/textarea";

import { courseDescriptionRules, courseTitleRules } from "./course-form-rules";

type FormValues = { title: string; description: string };

type NewCourseDialogProps = { open: boolean; onClose: () => void };

export function NewCourseDialog({ open, onClose }: NewCourseDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onClose();
        }
      }}
    >
      <DialogContent>{open && <NewCourseForm />}</DialogContent>
    </Dialog>
  );
}

function NewCourseForm() {
  const router = useRouter();
  const createCourse = useCreateCourse();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ defaultValues: { title: "", description: "" } });

  const onSubmit = handleSubmit((values) =>
    createCourse.mutate(values, {
      onSuccess: (course) => {
        toast.success(`Utworzono kurs: ${course.title}.`);
        router.push(`/teach/courses/${course.id}`);
      },
    }),
  );

  return (
    <form onSubmit={onSubmit} noValidate className="grid gap-4">
      <DialogHeader>
        <DialogTitle>Nowy kurs</DialogTitle>
        <DialogDescription>
          Kurs jest prywatny, dopóki go nie opublikujesz. Wstęp i lekcje dodasz
          na następnej stronie.
        </DialogDescription>
      </DialogHeader>

      <FieldGroup>
        {createCourse.isError && (
          <Alert variant="destructive">
            <AlertCircleIcon />
            <AlertTitle>Nie udało się utworzyć kursu</AlertTitle>
            <AlertDescription>
              {errorMessage(createCourse.error)}
            </AlertDescription>
          </Alert>
        )}
        <FormField label="Tytuł" error={errors.title?.message}>
          {(control) => (
            <Input
              {...control}
              autoComplete="off"
              {...register("title", courseTitleRules)}
            />
          )}
        </FormField>
        <FormField
          label="Opis"
          description="Krótko, o czym jest kurs — uczniowie zobaczą to na karcie kursu."
          error={errors.description?.message}
        >
          {(control) => (
            <Textarea
              {...control}
              rows={3}
              {...register("description", courseDescriptionRules)}
            />
          )}
        </FormField>
      </FieldGroup>

      <DialogFooter>
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button type="submit" disabled={createCourse.isPending}>
          {createCourse.isPending && <Spinner data-icon="inline-start" />}
          Utwórz kurs
        </Button>
      </DialogFooter>
    </form>
  );
}
