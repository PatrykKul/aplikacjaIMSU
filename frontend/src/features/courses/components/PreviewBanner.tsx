import { EyeIcon } from "lucide-react";
import Link from "next/link";

type PreviewBannerProps = { editHref: string; what: "kurs" | "lekcję" };

/** Shown to the author: the page is what students see, not the editor. */
export function PreviewBanner({ editHref, what }: PreviewBannerProps) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg bg-muted px-4 py-3 text-sm">
      <EyeIcon aria-hidden="true" className="size-4 shrink-0" />
      <span className="flex-1">
        Podgląd: tak uczeń widzi {what} (zapisaną wersję).
      </span>
      <Link
        href={editHref}
        className="font-medium underline underline-offset-4"
      >
        Wróć do edycji
      </Link>
    </div>
  );
}
