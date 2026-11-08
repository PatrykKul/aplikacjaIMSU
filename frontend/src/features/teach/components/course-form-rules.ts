import { DESCRIPTION_MAX, TITLE_MAX } from "@/features/courses/types";

export const courseTitleRules = {
  validate: (value: string) => value.trim() !== "" || "Wpisz tytuł kursu.",
  maxLength: {
    value: TITLE_MAX,
    message: `Tytuł może mieć najwyżej ${TITLE_MAX} znaków.`,
  },
};

export const courseDescriptionRules = {
  maxLength: {
    value: DESCRIPTION_MAX,
    message: `Opis może mieć najwyżej ${DESCRIPTION_MAX} znaków.`,
  },
};

export const lessonTitleRules = {
  validate: (value: string) => value.trim() !== "" || "Wpisz tytuł lekcji.",
  maxLength: {
    value: TITLE_MAX,
    message: `Tytuł może mieć najwyżej ${TITLE_MAX} znaków.`,
  },
};
