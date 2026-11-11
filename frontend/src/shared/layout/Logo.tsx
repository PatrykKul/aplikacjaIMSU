import { GraduationCapIcon } from "lucide-react";

import { cn } from "@/shared/lib/utils";

type LogoProps = {
  /** "lg" on the login and register screens, "default" in headers. */
  size?: "default" | "lg";
  className?: string;
};

/** Brand mark (cap on an indigo square) and the name. Visual only: callers wrap it in a link. */
export function Logo({ size = "default", className }: LogoProps) {
  const large = size === "lg";
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <span
        aria-hidden="true"
        className={cn(
          "flex items-center justify-center rounded-lg bg-primary text-primary-foreground",
          large ? "size-10" : "size-8",
        )}
      >
        <GraduationCapIcon className={large ? "size-6" : "size-5"} />
      </span>
      <span
        className={cn(
          "font-semibold tracking-tight",
          large ? "text-2xl" : "text-lg",
        )}
      >
        IMSU
      </span>
    </span>
  );
}
