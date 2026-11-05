const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const emailRules = {
  required: "Podaj adres e-mail.",
  pattern: {
    value: EMAIL_PATTERN,
    message: "Podaj poprawny adres e-mail, np. jan@przyklad.pl.",
  },
};

export const loginPasswordRules = {
  required: "Podaj hasło.",
};

export const newPasswordRules = {
  required: "Podaj hasło.",
  minLength: { value: 8, message: "Hasło musi mieć co najmniej 8 znaków." },
  validate: (value: string) =>
    new TextEncoder().encode(value).length <= 72 || "Hasło jest za długie.",
};

export const displayNameRules = {
  validate: (value: string) => value.trim().length > 0 || "Podaj swoje imię.",
  maxLength: { value: 80, message: "Imię może mieć najwyżej 80 znaków." },
};
