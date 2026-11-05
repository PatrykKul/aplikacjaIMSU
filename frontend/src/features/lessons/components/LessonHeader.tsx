import { ArrowLeftIcon } from "lucide-react";
import Link from "next/link";

import { cn } from "@/shared/lib/utils";
import { buttonVariants } from "@/shared/ui/button";

type LessonHeaderProps = {
  courseHref: string;
  context: string;
  title: string;
  step: number;
  total: number;
  progress: number;
};

// Focus mode: the lesson replaces the app header with its own
export function LessonHeader({
  courseHref,
  context,
  title,
  step,
  total,
  progress,
}: LessonHeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div className="mx-auto flex h-14 w-full max-w-3xl items-center gap-2 px-2 sm:h-16 sm:gap-3 sm:px-4">
        <Link
          href={courseHref}
          aria-label="Wróć do kursu"
          className={cn(
            buttonVariants({ variant: "ghost", size: "icon" }),
            "sm:w-auto sm:px-3 sm:ring-1 sm:ring-foreground/15",
          )}
        >
          <ArrowLeftIcon aria-hidden="true" className="size-5" />
          <span className="hidden sm:inline">Kurs</span>
        </Link>
        <div className="min-w-0 flex-1">
          <p className="hidden truncate text-xs text-muted-foreground sm:block">
            {context}
          </p>
          <h1 className="truncate font-semibold">{title}</h1>
        </div>
        <p className="shrink-0 px-1 text-sm text-muted-foreground">
          <span className="hidden sm:inline">Krok </span>
          {step}
          <span className="sm:hidden"> / </span>
          <span className="hidden sm:inline"> z </span>
          {total}
        </p>
      </div>
      <div
        role="progressbar"
        aria-label="Postęp lekcji"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={Math.round(progress * 100)}
        className="h-1 bg-muted"
      >
        <div
          className="h-full bg-foreground/70 transition-[width]"
          style={{ width: `${progress * 100}%` }}
        />
      </div>
    </header>
  );
}
