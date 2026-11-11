import { cn } from "@/shared/lib/utils";
import { Badge } from "@/shared/ui/badge";

import { type Form, FORM_LABELS } from "../types";

/** Literal classes, so Tailwind can find them. */
const FORM_TONES: Record<Form, string> = {
  V: "bg-form-v-soft text-form-v-foreground",
  A: "bg-form-a-soft text-form-a-foreground",
  K: "bg-form-k-soft text-form-k-foreground",
};

/** Material form with its color and name, e.g. "Wzrokowa (V)" on sky. */
export function FormBadge({ form }: { form: Form }) {
  return <Badge className={cn(FORM_TONES[form])}>{FORM_LABELS[form]}</Badge>;
}
