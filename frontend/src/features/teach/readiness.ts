import type { Block, Form } from "@/features/content/types";
import { plural } from "@/shared/lib/plural";
import { isEmptyDocument } from "@/shared/rich-text/is-empty";

import type { IssueArea, ReadinessIssue } from "./types";

// R11: codes of missing parts -> Polish sentences (docs/08-praca-biezaca.md)

const FORM_NAMES: Record<Form, string> = {
  V: "wzrokowa",
  A: "słuchowa",
  K: "kinestetyczna",
};

export const AREA_LABELS: Record<IssueArea, string> = {
  lesson: "Zarys i wnioski",
  V: "Wersja wzrokowa (V)",
  A: "Wersja słuchowa (A)",
  K: "Wersja kinestetyczna (K)",
  quiz: "Quiz (pula)",
};

export const AREA_ORDER: IssueArea[] = ["lesson", "V", "A", "K", "quiz"];

export function questionsCount(count: number): string {
  return `${count} ${plural(count, "pytanie", "pytania", "pytań")}`;
}

/** Full sentence for the readiness panel. */
export function issueText(issue: ReadinessIssue): string {
  switch (issue.code) {
    case "OUTLINE_MISSING":
      return "Zarys lekcji jest pusty.";
    case "CONCLUSIONS_MISSING":
      return "Wnioski są puste.";
    case "VERSION_EMPTY":
      return issue.area === "V" || issue.area === "A" || issue.area === "K"
        ? `Wersja ${FORM_NAMES[issue.area]} jest pusta.`
        : "Jedna z wersji jest pusta.";
    case "V_VISUAL_MISSING":
      return "Potrzebny jest blok tekstu oraz obraz albo film.";
    case "A_AUDIO_MISSING":
      return "Dodaj nagranie: plik dźwiękowy albo tekst dla lektora.";
    case "A_DESCRIPTION_MISSING":
      return "Dodaj krótki opis nagrania w bloku tekstu.";
    case "K_INSTRUCTION_MISSING":
      return "Dodaj instrukcję krok po kroku w bloku tekstu.";
    case "K_WORKSHEET_MISSING":
      return "Dodaj kartę zadania w PDF.";
    case "QUIZ_TOO_FEW_QUESTIONS": {
      const count = issue.count ?? 0;
      const min = issue.min ?? 5;
      if (count === 0) {
        return `Pula pytań jest pusta. Dodaj co najmniej ${questionsCount(min)}.`;
      }
      const verb = plural(count, "jest", "są", "jest");
      return `W puli ${verb} ${questionsCount(count)}, potrzeba co najmniej ${min} (brakuje ${min - count}).`;
    }
    default:
      return `Brakuje wymaganego elementu (${issue.code}).`;
  }
}

/** Short list for the lesson row: "wersja K, 2 pytania". */
export function issuesSummary(issues: ReadinessIssue[]): string {
  const parts: string[] = [];
  for (const area of AREA_ORDER) {
    const inArea = issues.filter((issue) => issue.area === area);
    if (inArea.length === 0) {
      continue;
    }
    if (area === "lesson") {
      for (const issue of inArea) {
        parts.push(issue.code === "OUTLINE_MISSING" ? "zarys" : "wnioski");
      }
    } else if (area === "quiz") {
      const issue = inArea[0];
      const missing = (issue.min ?? 5) - (issue.count ?? 0);
      parts.push(questionsCount(missing));
    } else {
      parts.push(`wersja ${area}`);
    }
  }
  return parts.join(", ");
}

/** Issues grouped by area, in the order of the editor tabs. */
export function groupIssues(
  issues: ReadinessIssue[],
): { area: IssueArea; issues: ReadinessIssue[] }[] {
  return AREA_ORDER.map((area) => ({
    area,
    issues: issues.filter((issue) => issue.area === area),
  })).filter((group) => group.issues.length > 0);
}

// --- What a version must contain (shown live while editing) ---

export type Requirement = { label: string; met: boolean };

function hasText(blocks: Block[]): boolean {
  return blocks.some(
    (block) => block.type === "text" && !isEmptyDocument(block.doc),
  );
}

function hasKind(blocks: Block[], kinds: string[]): boolean {
  return blocks.some(
    (block) => block.type === "attachment" && kinds.includes(block.kind),
  );
}

/** The same rules as `content/readiness.py`, checked on unsaved blocks. */
export function versionRequirements(
  form: Form,
  blocks: Block[],
): Requirement[] {
  switch (form) {
    case "V":
      return [
        { label: "Tekst z wyjaśnieniem", met: hasText(blocks) },
        { label: "Obraz albo film", met: hasKind(blocks, ["image", "video"]) },
      ];
    case "A":
      return [
        {
          label: "Nagranie: plik dźwiękowy albo tekst dla lektora",
          met: hasKind(blocks, ["audio"]),
        },
        { label: "Krótki opis w bloku tekstu", met: hasText(blocks) },
      ];
    case "K":
      return [
        { label: "Instrukcja krok po kroku (tekst)", met: hasText(blocks) },
        { label: "Karta zadania w PDF", met: hasKind(blocks, ["pdf"]) },
      ];
  }
}

export const VERSION_INTROS: Record<Form, string> = {
  V: "Uczeń wzrokowy uczy się z obrazu: schematu, wykresu, filmu. Tekst objaśnia, co na nim widać.",
  A: "Uczeń słuchowy uczy się ze słuchania: nagrania albo tekstu czytanego przez lektora przeglądarki. Krótki opis mówi, czego posłucha.",
  K: "Uczeń kinestetyczny uczy się przez działanie: wykonuje zadanie z karty PDF według instrukcji krok po kroku.",
};
