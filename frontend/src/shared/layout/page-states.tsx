import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Spinner } from "@/shared/ui/spinner";

export function PageSpinner() {
  return (
    <div className="flex min-h-svh items-center justify-center">
      <Spinner className="size-8" />
    </div>
  );
}

type PageMessageProps = {
  title: string;
  description?: string;
  action?: ReactNode;
  fullScreen?: boolean;
  /** Icon of the state: what is missing (empty), CloudOff (error), SearchX (not found). */
  icon?: LucideIcon;
};

export function PageMessage({
  title,
  description,
  action,
  fullScreen,
  icon: Icon,
}: PageMessageProps) {
  return (
    <div
      className={
        fullScreen
          ? "flex min-h-svh items-center justify-center px-4"
          : "flex justify-center py-16"
      }
    >
      <div className="flex max-w-sm flex-col items-center gap-4 text-center">
        {Icon && (
          <div className="flex size-12 items-center justify-center rounded-full bg-accent text-accent-foreground">
            <Icon className="size-6" aria-hidden="true" />
          </div>
        )}
        <div className="space-y-2">
          <h1 className="text-xl font-semibold">{title}</h1>
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
        {action}
      </div>
    </div>
  );
}
