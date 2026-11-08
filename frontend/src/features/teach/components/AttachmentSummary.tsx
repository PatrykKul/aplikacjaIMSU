import { KIND_INFO } from "@/features/content/attachment-kinds";
import { type Attachment, FORM_LABELS } from "@/features/content/types";
import { apiUrl } from "@/shared/api/client";
import { Badge } from "@/shared/ui/badge";

/** What the attachment points to: file name, address or the reader's text. */
function source(attachment: Attachment): string {
  switch (attachment.kind) {
    case "link":
      return attachment.url;
    case "video":
      return attachment.youtube_url ?? attachment.file_name ?? "Plik wideo";
    case "audio":
      return attachment.transcript
        ? `Lektor: ${attachment.transcript}`
        : (attachment.file_name ?? "Plik dźwiękowy");
    default:
      return attachment.file_name ?? "Plik";
  }
}

/** Compact view of an attachment in the lesson editor (full players come in the lesson view). */
export function AttachmentSummary({ attachment }: { attachment: Attachment }) {
  const { icon: Icon } = KIND_INFO[attachment.kind];

  return (
    <div className="flex gap-4">
      {attachment.kind === "image" && attachment.file_url ? (
        // eslint-disable-next-line @next/next/no-img-element -- file served by the API, not by Next
        <img
          src={apiUrl(attachment.file_url)}
          alt={attachment.alt ?? ""}
          className="size-20 shrink-0 rounded-lg object-cover ring-1 ring-foreground/10"
        />
      ) : (
        <div className="flex size-20 shrink-0 items-center justify-center rounded-lg bg-muted">
          <Icon aria-hidden="true" className="size-8 text-muted-foreground" />
        </div>
      )}
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-medium">{attachment.title}</p>
        <p className="line-clamp-2 text-sm break-words text-muted-foreground">
          {source(attachment)}
        </p>
        <ul
          role="list"
          aria-label="Formy"
          className="flex flex-wrap gap-1 pt-1"
        >
          {attachment.forms.map((form) => (
            <li key={form}>
              <Badge variant="secondary">{FORM_LABELS[form]}</Badge>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
