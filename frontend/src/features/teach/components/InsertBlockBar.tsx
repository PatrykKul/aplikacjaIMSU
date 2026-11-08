import { PaperclipIcon, PilcrowIcon } from "lucide-react";

import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";

type InsertBlockBarProps = {
  onText: () => void;
  onAttachment: () => void;
  /** Between blocks the bar is quieter than the one under the list. */
  compact?: boolean;
  /** Where the block lands, for screen readers, e.g. "przed blokiem 2". */
  place: string;
};

export function InsertBlockBar({
  onText,
  onAttachment,
  compact,
  place,
}: InsertBlockBarProps) {
  const variant = compact ? "ghost" : "outline";
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-2",
        compact && "justify-center",
      )}
    >
      <Button
        type="button"
        variant={variant}
        size={compact ? "sm" : "default"}
        aria-label={`Dodaj tekst ${place}`}
        onClick={onText}
      >
        <PilcrowIcon data-icon="inline-start" />
        Tekst
      </Button>
      <Button
        type="button"
        variant={variant}
        size={compact ? "sm" : "default"}
        aria-label={`Dodaj załącznik ${place}`}
        onClick={onAttachment}
      >
        <PaperclipIcon data-icon="inline-start" />
        Załącznik
      </Button>
    </div>
  );
}
