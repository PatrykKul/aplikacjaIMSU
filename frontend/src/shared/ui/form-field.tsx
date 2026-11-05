import { type ReactNode, useId } from "react";

import {
  Field,
  FieldDescription,
  FieldError,
  FieldLabel,
} from "@/shared/ui/field";

export type FieldControlProps = {
  id: string;
  "aria-invalid"?: true;
  "aria-describedby"?: string;
};

type FormFieldProps = {
  label: string;
  description?: ReactNode;
  error?: string;
  children: (control: FieldControlProps) => ReactNode;
};

export function FormField({
  label,
  description,
  error,
  children,
}: FormFieldProps) {
  const id = useId();
  const descriptionId = `${id}-description`;
  const errorId = `${id}-error`;
  const describedBy = [
    description ? descriptionId : null,
    error ? errorId : null,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <Field data-invalid={error ? true : undefined}>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      {children({
        id,
        "aria-invalid": error ? true : undefined,
        "aria-describedby": describedBy || undefined,
      })}
      {description && (
        <FieldDescription id={descriptionId}>{description}</FieldDescription>
      )}
      {error && <FieldError id={errorId}>{error}</FieldError>}
    </Field>
  );
}
