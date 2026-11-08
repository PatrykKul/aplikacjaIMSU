import { FORMS, type Form } from "@/features/content/types";

import type { LearningStyle, StyleSource } from "./types";

export const STYLE_NAMES: Record<Form, string> = {
  V: "wzrokowiec",
  A: "słuchowiec",
  K: "kinestetyk",
};

export const STYLE_DESCRIPTIONS: Record<Form, string> = {
  V: "Najłatwiej uczysz się z obrazów, schematów, wykresów i filmów.",
  A: "Najłatwiej uczysz się, słuchając wyjaśnień, nagrań i czytając na głos.",
  K: "Najłatwiej uczysz się, działając: przez ćwiczenia, przykłady i próby.",
};

export const SOURCE_LABELS: Record<StyleSource, string> = {
  survey: "z ankiety",
  manual: "wybrany ręcznie",
  adaptation: "po propozycji systemu",
};

/** Letters of a style in V-A-K order, e.g. "AV" is never produced. */
export function styleLetters(style: LearningStyle): Form[] {
  return FORMS.filter((form) => style.includes(form));
}

/** "VA" -> "wzrokowiec + słuchowiec". */
export function describeStyle(style: LearningStyle): string {
  return styleLetters(style)
    .map((form) => STYLE_NAMES[form])
    .join(" + ");
}

export function joinStyle(forms: Form[]): LearningStyle {
  return FORMS.filter((form) => forms.includes(form)).join("");
}
