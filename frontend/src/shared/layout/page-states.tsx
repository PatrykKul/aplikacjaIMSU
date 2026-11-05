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
};

export function PageMessage({
  title,
  description,
  action,
  fullScreen,
}: PageMessageProps) {
  return (
    <div
      className={
        fullScreen
          ? "flex min-h-svh items-center justify-center px-4"
          : "flex justify-center py-16"
      }
    >
      <div className="max-w-sm space-y-4 text-center">
        <h1 className="text-xl font-semibold">{title}</h1>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
        {action}
      </div>
    </div>
  );
}
