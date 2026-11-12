import type { ReactNode } from "react";

import { Button } from "@/shared/ui/button";
import { Spinner } from "@/shared/ui/spinner";

type SaveBarProps = {
  /** Text of the button, e.g. "Zapisz wersję V". */
  label: string;
  dirty: boolean;
  pending: boolean;
  onSave: () => void;
  /** Extra information next to the state, e.g. the pool counter. */
  children?: ReactNode;
};

/** Stays under the app header while scrolling a long tab of the lesson editor. */
export function SaveBar({
  label,
  dirty,
  pending,
  onSave,
  children,
}: SaveBarProps) {
  return (
    <div className="sticky top-16 z-30 -mx-4 flex flex-wrap items-center gap-x-4 gap-y-2 border-b bg-background/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:px-6">
      <Button onClick={onSave} disabled={!dirty || pending}>
        {pending && <Spinner data-icon="inline-start" />}
        {label}
      </Button>
      <p className="text-sm text-muted-foreground" aria-live="polite">
        {dirty ? "Masz niezapisane zmiany." : "Wszystkie zmiany zapisane."}
      </p>
      {children && <div className="ml-auto text-sm">{children}</div>}
    </div>
  );
}
