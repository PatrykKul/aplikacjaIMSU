"use client";

import { AlertCircleIcon } from "lucide-react";
import { useForm } from "react-hook-form";

import { classroomsError } from "@/features/classes/errors";
import { CLASSROOM_NAME_MAX } from "@/features/classes/types";
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

const nameRules = {
  validate: (value: string) => value.trim() !== "" || "Wpisz nazwę klasy.",
  maxLength: {
    value: CLASSROOM_NAME_MAX,
    message: `Nazwa może mieć najwyżej ${CLASSROOM_NAME_MAX} znaków.`,
  },
};

type ClassroomNameDialogProps = {
  open: boolean;
  title: string;
  description?: string;
  submitLabel: string;
  defaultName?: string;
  /** The parent owns the mutation: creating and renaming share this form. */
  pending: boolean;
  error: unknown;
  onSubmit: (name: string) => void;
  onClose: () => void;
};

export function ClassroomNameDialog({
  open,
  onClose,
  ...formProps
}: ClassroomNameDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={(isOpen) => {
        if (!isOpen) {
          onClose();
        }
      }}
    >
      {/* Mounted only while open, so the field starts from `defaultName` each time */}
      <DialogContent>{open && <NameForm {...formProps} />}</DialogContent>
    </Dialog>
  );
}

type NameFormProps = Omit<ClassroomNameDialogProps, "open" | "onClose">;

function NameForm({
  title,
  description,
  submitLabel,
  defaultName = "",
  pending,
  error,
  onSubmit,
}: NameFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<{ name: string }>({ defaultValues: { name: defaultName } });

  return (
    <form
      onSubmit={handleSubmit(({ name }) => onSubmit(name.trim()))}
      noValidate
      className="grid gap-4"
    >
      <DialogHeader>
        <DialogTitle>{title}</DialogTitle>
        {description && <DialogDescription>{description}</DialogDescription>}
      </DialogHeader>

      <FieldGroup>
        {error != null && (
          <Alert variant="destructive">
            <AlertCircleIcon />
            <AlertTitle>Nie udało się zapisać</AlertTitle>
            <AlertDescription>{classroomsError(error)}</AlertDescription>
          </Alert>
        )}
        <FormField
          label="Nazwa klasy"
          description="Na przykład „Klasa 7a” albo „Kółko matematyczne”."
          error={errors.name?.message}
        >
          {(control) => (
            <Input
              {...control}
              autoComplete="off"
              {...register("name", nameRules)}
            />
          )}
        </FormField>
      </FieldGroup>

      <DialogFooter>
        <DialogClose render={<Button type="button" variant="outline" />}>
          Anuluj
        </DialogClose>
        <Button type="submit" disabled={pending}>
          {pending && <Spinner data-icon="inline-start" />}
          {submitLabel}
        </Button>
      </DialogFooter>
    </form>
  );
}
