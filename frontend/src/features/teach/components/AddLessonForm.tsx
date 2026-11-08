"use client";

import { PlusIcon } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

import { useAddLesson } from "@/features/courses/hooks";
import { errorMessage } from "@/shared/api/error-messages";
import { Button } from "@/shared/ui/button";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";

import { lessonTitleRules } from "./course-form-rules";

export function AddLessonForm({ courseId }: { courseId: number }) {
  const addLesson = useAddLesson(courseId);
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<{ title: string }>({ defaultValues: { title: "" } });

  const onSubmit = handleSubmit(({ title }) =>
    addLesson.mutate(title, {
      onSuccess: () => reset(),
      onError: (error) => toast.error(errorMessage(error)),
    }),
  );

  return (
    <form
      onSubmit={onSubmit}
      noValidate
      className="flex flex-col gap-3 sm:flex-row sm:items-start"
    >
      <div className="flex-1">
        <FormField label="Tytuł nowej lekcji" error={errors.title?.message}>
          {(field) => (
            <Input
              {...field}
              autoComplete="off"
              {...register("title", lessonTitleRules)}
            />
          )}
        </FormField>
      </div>
      <Button
        type="submit"
        variant="outline"
        className="sm:mt-7"
        disabled={addLesson.isPending}
      >
        {addLesson.isPending ? (
          <Spinner data-icon="inline-start" />
        ) : (
          <PlusIcon data-icon="inline-start" />
        )}
        Dodaj lekcję
      </Button>
    </form>
  );
}
