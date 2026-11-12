import { FORMS, type Form } from "@/features/content/types";

import type { IssueArea } from "./types";

/** Tabs of the lesson editor; also the `?tab=` value in the address. */
export type EditorTab = "outline" | Form | "quiz";

export const EDITOR_TABS: EditorTab[] = ["outline", ...FORMS, "quiz"];

export const TAB_LABELS: Record<EditorTab, string> = {
  outline: "Zarys i wnioski",
  V: "Wzrokowa (V)",
  A: "Słuchowa (A)",
  K: "Kinestetyczna (K)",
  quiz: "Quiz (pula)",
};

/** The tab named in the address, or the first one. */
export function parseEditorTab(value: unknown): EditorTab {
  return EDITOR_TABS.find((tab) => tab === value) ?? "outline";
}

/** The tab where a missing part (R11) is fixed. */
export function tabOfArea(area: IssueArea): EditorTab {
  return area === "lesson" ? "outline" : area;
}
