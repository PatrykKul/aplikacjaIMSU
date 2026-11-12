import type { Form } from "@/features/content/types";

// Formatting of the course panel (dates, numbers, names of forms and styles)

const dateFormat = new Intl.DateTimeFormat("pl-PL", { dateStyle: "medium" });
const dateTimeFormat = new Intl.DateTimeFormat("pl-PL", {
  dateStyle: "medium",
  timeStyle: "short",
});

export function formatDate(iso: string): string {
  return dateFormat.format(new Date(iso));
}

export function formatDateTime(iso: string): string {
  return dateTimeFormat.format(new Date(iso));
}

/** "80%" or a dash when there is no data. */
export function formatPercent(value: number | null | undefined): string {
  return value === null || value === undefined ? "–" : `${value}%`;
}

export const FORM_NAMES: Record<Form, string> = {
  V: "wzrokowa",
  A: "słuchowa",
  K: "kinestetyczna",
};

export const STYLE_NAMES: Record<Form, string> = {
  V: "wzrokowy",
  A: "słuchowy",
  K: "kinestetyczny",
};

// Literal class names, so Tailwind can find them in the source
export const FORM_BAR: Record<Form, string> = {
  V: "bg-form-v",
  A: "bg-form-a",
  K: "bg-form-k",
};
