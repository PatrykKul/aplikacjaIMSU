import type { Form } from "@/features/content/types";

// Literal class names, so Tailwind can find them in the source

export const FORM_BAR: Record<Form, string> = {
  V: "bg-form-v",
  A: "bg-form-a",
  K: "bg-form-k",
};

export const FORM_STROKE: Record<Form, string> = {
  V: "stroke-form-v",
  A: "stroke-form-a",
  K: "stroke-form-k",
};

export const FORM_FILL: Record<Form, string> = {
  V: "fill-form-v",
  A: "fill-form-a",
  K: "fill-form-k",
};

/** Dark text in the hue of the form (contrast >= 7:1 on the background). */
export const FORM_TEXT_FILL: Record<Form, string> = {
  V: "fill-form-v-foreground",
  A: "fill-form-a-foreground",
  K: "fill-form-k-foreground",
};

/** Second carrier besides color: solid, dashed and dotted lines. */
export const FORM_DASH: Record<Form, string | undefined> = {
  V: undefined,
  A: "7 4",
  K: "1.5 4",
};
