import type { Form } from "@/features/content/types";
import { cn } from "@/shared/lib/utils";

import { formLabel } from "../explain";
import { FORM_BAR } from "../form-tones";

type FormMarkProps = { form: Form; className?: string; label?: string };

/** A small square in the color of the form, always with its letter and name. */
export function FormMark({ form, className, label }: FormMarkProps) {
  return (
    <span className={cn("inline-flex items-center gap-1.5", className)}>
      <span
        aria-hidden="true"
        className={cn("size-2.5 shrink-0 rounded-[2px]", FORM_BAR[form])}
      />
      {label ?? formLabel(form)}
    </span>
  );
}
