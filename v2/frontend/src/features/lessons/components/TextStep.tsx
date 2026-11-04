import { MathMarkdown } from "@/shared/ui/math-markdown";

import type { TextStep as TextStepData } from "../types";

export function TextStep({ step }: { step: TextStepData }) {
  return <MathMarkdown>{step.body}</MathMarkdown>;
}
