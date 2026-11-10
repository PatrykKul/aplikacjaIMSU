import { ChevronDownIcon } from "lucide-react";

import { KIND_INFO } from "@/features/content/attachment-kinds";
import type { Attachment } from "@/features/content/types";
import { Button } from "@/shared/ui/button";

type CollapsedMaterialProps = {
  attachment: Attachment;
  onShow: () => void;
};

/** A material for another learning style, folded to one row in its place in the lesson. */
export function CollapsedMaterial({
  attachment,
  onShow,
}: CollapsedMaterialProps) {
  const { icon: Icon, label } = KIND_INFO[attachment.kind];
  return (
    <div className="flex flex-col gap-3 rounded-xl px-5 py-4 ring-1 ring-foreground/10 sm:flex-row sm:items-center sm:gap-4 sm:px-9">
      <div className="flex min-w-0 flex-1 gap-4">
        <Icon
          aria-hidden="true"
          className="mt-0.5 size-5 shrink-0 text-muted-foreground"
        />
        <div className="min-w-0 space-y-1">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="font-medium">{attachment.title}</p>
        </div>
      </div>
      <Button
        variant="outline"
        className="self-start sm:self-center"
        onClick={onShow}
      >
        <ChevronDownIcon data-icon="inline-start" />
        Pokaż materiał
      </Button>
    </div>
  );
}
