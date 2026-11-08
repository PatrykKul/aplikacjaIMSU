import { ArrowLeftIcon } from "lucide-react";
import Link from "next/link";

import { cn } from "@/shared/lib/utils";
import { buttonVariants } from "@/shared/ui/button";

type LessonHeaderProps = {
  courseHref: string;
  courseTitle: string;
  title: string;
};

export function LessonHeader({
  courseHref,
  courseTitle,
  title,
}: LessonHeaderProps) {
  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <div className="grid h-14 grid-cols-[minmax(max-content,1fr)_minmax(0,48rem)_minmax(max-content,1fr)] items-center px-2 sm:h-16 sm:px-6">
        <Link
          href={courseHref}
          aria-label={`Wróć do kursu: ${courseTitle}`}
          className={cn(
            buttonVariants({ variant: "ghost" }),
            "justify-self-start px-3",
          )}
        >
          <ArrowLeftIcon aria-hidden="true" />
          <span className="hidden sm:inline">Kurs</span>
        </Link>
        <div className="min-w-0 px-2 sm:px-6">
          <p className="hidden truncate text-[0.8125rem] text-muted-foreground sm:block">
            {courseTitle}
          </p>
          <h1 className="truncate font-medium">{title}</h1>
        </div>
        <div />
      </div>
    </header>
  );
}
