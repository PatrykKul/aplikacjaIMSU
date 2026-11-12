import { EyeIcon } from "lucide-react";
import Link from "next/link";

type PreviewBannerProps = {
  /** Link back to the editor; none for the admin (read only). */
  editHref?: string;
  what: "kurs" | "lekcję";
};

/** Shown to the author and the admin: the page is a preview, not the editor. */
export function PreviewBanner({ editHref, what }: PreviewBannerProps) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-lg bg-muted px-4 py-3 text-sm">
      <EyeIcon aria-hidden="true" className="size-4 shrink-0" />
      <span className="flex-1">
        {what === "kurs"
          ? "Podgląd: tak uczeń widzi kurs (zapisaną wersję)."
          : "Podgląd lekcji: zarys, wszystkie trzy wersje, wnioski i pula pytań z odpowiedziami."}
        {!editHref && " Tylko odczyt."}
      </span>
      {editHref && (
        <Link
          href={editHref}
          className="font-medium underline underline-offset-4"
        >
          Wróć do edycji
        </Link>
      )}
    </div>
  );
}
