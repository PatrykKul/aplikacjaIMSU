import type { Rola, Styl } from "@/lib/types";

export const ROLA_LABEL: Record<Rola, string> = {
  admin: "Administrator",
  nauczyciel: "Nauczyciel",
  uczen: "Uczeń",
};

export const STYLE: Styl[] = ["V", "A", "K"];

export const STYL_NAZWA: Record<Styl, string> = {
  V: "wzrokowiec",
  A: "słuchowiec",
  K: "kinestetyk",
};

export const STYL_OPIS: Record<Styl, string> = {
  V: "Najlepiej uczysz się, gdy widzisz: obrazy, diagramy, wideo i kolorowe notatki.",
  A: "Najlepiej uczysz się, gdy słyszysz: nagrania, omówienia i rozmowę o materiale.",
  K: "Najlepiej uczysz się w działaniu: ćwiczenia krok po kroku, quizy i zadania „zrób sam”.",
};

/** Tailwind classes per style — one colour per style across the whole app. */
export const STYL_KOLOR: Record<Styl, { bar: string; text: string; chip: string }> = {
  V: {
    bar: "bg-sky-500",
    text: "text-sky-600 dark:text-sky-300",
    chip: "border-sky-400/50 bg-sky-500/10 text-sky-700 dark:text-sky-200",
  },
  A: {
    bar: "bg-violet-500",
    text: "text-violet-600 dark:text-violet-300",
    chip: "border-violet-400/50 bg-violet-500/10 text-violet-700 dark:text-violet-200",
  },
  K: {
    bar: "bg-emerald-500",
    text: "text-emerald-600 dark:text-emerald-300",
    chip: "border-emerald-400/50 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200",
  },
};

/** Splits a stored style ("V", "VA", "VAK") into single letters. */
export function styleZ(styl: string | null | undefined): Styl[] {
  return STYLE.filter((s) => (styl ?? "").includes(s));
}

/** "wzrokowiec" or, for a tie, "styl mieszany: wzrokowiec + słuchowiec". */
export function nazwaStylu(styl: string | null | undefined): string {
  const lista = styleZ(styl);
  if (lista.length === 0) return "nieokreślony";
  if (lista.length === 1) return STYL_NAZWA[lista[0]];
  return `styl mieszany: ${lista.map((s) => STYL_NAZWA[s]).join(" + ")}`;
}

export const ZRODLO_STYLU_LABEL: Record<string, string> = {
  ankieta: "z ankiety",
  reczny: "wybrany ręcznie",
  adaptacja: "dopasowany po quizach",
};

export const POZIOM_NAZWA: Record<number, string> = {
  1: "łatwiejsze przykłady",
  2: "standardowy",
  3: "z rozszerzeniami",
};

export const ZDARZENIE_LABEL: Record<string, string> = {
  otwarcie_tematu: "Otwarcie tematu",
  odtworzenie_wideo: "Odtworzenie wideo",
  odtworzenie_audio: "Odsłuchanie nagrania",
  ukonczenie_cwiczenia: "Ukończenie ćwiczenia",
  czas_w_temacie: "Czas w temacie",
  wynik_quizu: "Wynik quizu",
  ukonczenie_tematu: "Oznaczenie tematu jako ukończony",
};
