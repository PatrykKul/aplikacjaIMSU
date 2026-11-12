"use client";

import { ChevronRightIcon, ExternalLinkIcon, FileTextIcon } from "lucide-react";

import { apiUrl } from "@/shared/api/client";
import { cn } from "@/shared/lib/utils";
import { buttonVariants } from "@/shared/ui/button";

import type { Attachment } from "../types";
import { SpeechReader } from "./SpeechReader";

function hostOf(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

/** Collapsed by default; <summary> opens it with Enter or Space. */
function Transcript({ text }: { text: string }) {
  return (
    <details className="group">
      <summary className="inline-flex h-9 cursor-pointer list-none items-center gap-1.5 rounded-md text-sm font-medium underline-offset-4 outline-none hover:underline focus-visible:ring-3 focus-visible:ring-ring/50 [&::-webkit-details-marker]:hidden">
        <ChevronRightIcon
          aria-hidden="true"
          className="size-4 transition-transform group-open:rotate-90"
        />
        Transkrypcja
      </summary>
      <p className="mt-2 border-l-2 pl-4 whitespace-pre-line text-muted-foreground">
        {text}
      </p>
    </details>
  );
}

function AttachmentBody({ attachment }: { attachment: Attachment }) {
  const fileUrl = attachment.file_url ? apiUrl(attachment.file_url) : null;

  switch (attachment.kind) {
    case "image":
      return fileUrl ? (
        // eslint-disable-next-line @next/next/no-img-element -- file served by the API, not by Next
        <img
          src={fileUrl}
          alt={attachment.alt ?? ""}
          className="mx-auto max-h-[70svh] rounded-lg"
        />
      ) : null;

    case "video":
      if (attachment.youtube_id) {
        return (
          <iframe
            src={`https://www.youtube-nocookie.com/embed/${attachment.youtube_id}`}
            title={attachment.title}
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowFullScreen
            className="aspect-video w-full rounded-lg"
          />
        );
      }
      return fileUrl ? (
        <video
          controls
          preload="metadata"
          src={fileUrl}
          className="w-full rounded-lg bg-black"
        />
      ) : null;

    case "audio":
      // D58: a recording with an optional transcript under it
      if (fileUrl) {
        return (
          <div className="space-y-3">
            <audio
              controls
              preload="metadata"
              src={fileUrl}
              className="w-full"
            />
            {attachment.transcript && (
              <Transcript text={attachment.transcript} />
            )}
          </div>
        );
      }
      // No file: the browser reads the transcript aloud
      return attachment.transcript ? (
        <div className="space-y-3">
          <SpeechReader text={attachment.transcript} />
          <p className="whitespace-pre-line">{attachment.transcript}</p>
        </div>
      ) : null;

    case "pdf":
      return fileUrl ? (
        <div className="space-y-3">
          {/* Phones rarely show PDFs inside a page, so the link comes first */}
          <a
            href={fileUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            <FileTextIcon data-icon="inline-start" />
            Otwórz PDF
          </a>
          <iframe
            src={fileUrl}
            title={attachment.title}
            className="hidden h-[70svh] w-full rounded-lg ring-1 ring-foreground/10 sm:block"
          />
        </div>
      ) : null;

    case "link":
      return (
        <a
          href={attachment.url}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(buttonVariants({ variant: "outline" }))}
        >
          <ExternalLinkIcon data-icon="inline-start" />
          Otwórz stronę {hostOf(attachment.url)}
        </a>
      );
  }
}

/** An attachment as the student sees it: title, description and the player or link. */
export function AttachmentView({ attachment }: { attachment: Attachment }) {
  return (
    <figure className="space-y-4">
      <figcaption className="space-y-1">
        <span className="block text-lg font-medium">{attachment.title}</span>
        {attachment.description && (
          <span className="block text-muted-foreground">
            {attachment.description}
          </span>
        )}
      </figcaption>
      <AttachmentBody attachment={attachment} />
    </figure>
  );
}
