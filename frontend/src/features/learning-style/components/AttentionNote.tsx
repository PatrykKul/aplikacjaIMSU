import { attentionText } from "../explain";
import type { Attention } from "../types";

/** R12: three counted results in a row below the threshold; a neutral frame. */
export function AttentionNote({ attention }: { attention: Attention }) {
  return (
    <section
      aria-label="Wymaga uwagi"
      className="rounded-lg border bg-muted/50 p-4 text-pretty tabular-nums sm:p-5"
    >
      {attentionText(attention)}
    </section>
  );
}
