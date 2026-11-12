"use client";

import { AlertCircleIcon } from "lucide-react";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { toast } from "sonner";

import { RichTextEditor } from "@/shared/rich-text/RichTextEditor";
import { Alert, AlertDescription, AlertTitle } from "@/shared/ui/alert";
import { Button } from "@/shared/ui/button";
import { FieldGroup } from "@/shared/ui/field";
import { FormField } from "@/shared/ui/form-field";
import { Input } from "@/shared/ui/input";
import { Spinner } from "@/shared/ui/spinner";
import { Textarea } from "@/shared/ui/textarea";

import { teachError } from "../errors";
import { useUpdateCourse } from "../hooks";
import type { CourseUpdateInput, TeacherCourse } from "../types";
import { courseDescriptionRules, courseTitleRules } from "./course-form-rules";

type FormValues = Pick<
  TeacherCourse,
  "title" | "description" | "introduction" | "summary"
>;

type CourseSettingsFormProps = {
  course: TeacherCourse;
  onDirtyChange: (dirty: boolean) => void;
};

const MATH_HINT = "Wzór wpiszesz między znakami $, np. $\\frac{1}{2}$.";

export function CourseSettingsForm({
  course,
  onDirtyChange,
}: CourseSettingsFormProps) {
  const updateCourse = useUpdateCourse(course.id);
  const {
    control,
    register,
    handleSubmit,
    reset,
    formState: { errors, isDirty, dirtyFields },
  } = useForm<FormValues>({
    defaultValues: {
      title: course.title,
      description: course.description,
      introduction: course.introduction,
      summary: course.summary,
    },
  });

  useEffect(() => {
    onDirtyChange(isDirty);
  }, [isDirty, onDirtyChange]);

  const onSubmit = handleSubmit((values) => {
    const data: CourseUpdateInput = {
      title: values.title,
      description: values.description,
    };
    // Documents only when edited: the editor reports its own normalised JSON
    if (dirtyFields.introduction && values.introduction) {
      data.introduction = values.introduction;
    }
    if (dirtyFields.summary && values.summary) {
      data.summary = values.summary;
    }
    updateCourse.mutate(data, {
      onSuccess: (saved) => {
        // The editors keep their own content; only the saved state changes
        reset({
          ...values,
          title: saved.title,
          description: saved.description,
        });
        toast.success("Zapisano zmiany kursu.");
      },
    });
  });

  return (
    <form onSubmit={onSubmit} noValidate className="space-y-6">
      <FieldGroup>
        {updateCourse.isError && (
          <Alert variant="destructive">
            <AlertCircleIcon />
            <AlertTitle>Nie udało się zapisać</AlertTitle>
            <AlertDescription>
              {teachError(updateCourse.error)}
            </AlertDescription>
          </Alert>
        )}
        <FormField label="Tytuł" error={errors.title?.message}>
          {(field) => (
            <Input
              {...field}
              autoComplete="off"
              {...register("title", courseTitleRules)}
            />
          )}
        </FormField>
        <FormField
          label="Opis"
          description="Krótki tekst na karcie kursu w katalogu."
          error={errors.description?.message}
        >
          {(field) => (
            <Textarea
              {...field}
              rows={3}
              {...register("description", courseDescriptionRules)}
            />
          )}
        </FormField>
        <FormField
          label="Wstęp"
          description={`Pierwsza strona kursu: czego uczeń się nauczy i jak pracować z lekcjami. ${MATH_HINT}`}
        >
          {(field) => (
            <Controller
              control={control}
              name="introduction"
              render={({ field: { onChange } }) => (
                <RichTextEditor
                  {...field}
                  label="Wstęp"
                  initialContent={course.introduction}
                  onChange={onChange}
                />
              )}
            />
          )}
        </FormField>
        <FormField
          label="Podsumowanie i wnioski"
          description="Uczeń zobaczy je na stronie kursu pod listą lekcji: najważniejsze rzeczy z całego kursu."
        >
          {(field) => (
            <Controller
              control={control}
              name="summary"
              render={({ field: { onChange } }) => (
                <RichTextEditor
                  {...field}
                  label="Podsumowanie i wnioski"
                  initialContent={course.summary}
                  onChange={onChange}
                />
              )}
            />
          )}
        </FormField>
      </FieldGroup>

      <div className="flex items-center gap-3">
        <Button type="submit" disabled={!isDirty || updateCourse.isPending}>
          {updateCourse.isPending && <Spinner data-icon="inline-start" />}
          Zapisz
        </Button>
        {isDirty && (
          <p className="text-sm text-muted-foreground">
            Masz niezapisane zmiany.
          </p>
        )}
      </div>
    </form>
  );
}
