import type { Form } from "@/features/content/types";
import { cn } from "@/shared/lib/utils";

import { FORM_BAR } from "../format";

type FormLabelProps = { form: Form; name: string; className?: string };

/** The color of a form is never alone: a square, the letter and the name. */
export function FormLabel({ form, name, className }: FormLabelProps) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span
        aria-hidden="true"
        className={cn("size-2.5 shrink-0 rounded-[2px]", FORM_BAR[form])}
      />
      <span>
        <span className="font-medium">{form}</span> · {name}
      </span>
    </span>
  );
}

type BarProps = {
  /** 0–100 */
  value: number;
  className: string;
};

/** Thin horizontal bar; the number is always printed next to it. */
export function Bar({ value, className }: BarProps) {
  return (
    <span
      aria-hidden="true"
      className="block h-2 w-full min-w-24 overflow-hidden rounded-full bg-muted"
    >
      <span
        className={cn("block h-full rounded-full", className)}
        style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
      />
    </span>
  );
}
