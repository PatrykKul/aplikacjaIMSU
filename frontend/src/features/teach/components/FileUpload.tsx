"use client";

import { FileIcon, UploadIcon } from "lucide-react";
import { useState } from "react";
import { type FileRejection, useDropzone } from "react-dropzone";

import {
  ACCEPTED_EXTENSIONS,
  formatFileSize,
} from "@/features/content/attachment-kinds";
import { contentApi } from "@/features/content/api";
import {
  type FileKind,
  MAX_UPLOAD_BYTES,
  type UploadedFile,
} from "@/features/content/types";
import { errorMessage } from "@/shared/api/error-messages";
import { cn } from "@/shared/lib/utils";
import { Button } from "@/shared/ui/button";

/** The file chosen for an attachment (a new upload or the saved one). */
export type ChosenFile = { id: number; name: string; url: string };

type FileUploadProps = {
  kind: FileKind;
  value: ChosenFile | null;
  onChange: (file: ChosenFile) => void;
  /** Validation message from the form, e.g. "Dodaj plik." */
  error?: string;
  id?: string;
  "aria-describedby"?: string;
};

const WRONG_TYPE = "wrong-type";

function extensionOf(name: string): string {
  const dot = name.lastIndexOf(".");
  return dot === -1 ? "" : name.slice(dot).toLowerCase();
}

function rejectionMessage(
  { file, errors }: FileRejection,
  extensions: string[],
): string {
  switch (errors[0]?.code) {
    case WRONG_TYPE:
      return `Ten typ pliku nie pasuje. Wybierz plik: ${extensions.join(", ")}.`;
    case "file-too-large":
      return `Plik ma ${formatFileSize(file.size)}. Największy dozwolony rozmiar to 50 MB.`;
    case "too-many-files":
      return "Dodaj jeden plik naraz.";
    default:
      return "Nie można dodać tego pliku. Wybierz inny.";
  }
}

/**
 * Picks one file (button, drag and drop or paste) and uploads it at once,
 * with a progress bar. react-dropzone checks type and size first, so the
 * teacher does not wait for a 50 MB upload to learn that it is not allowed.
 */
export function FileUpload({
  kind,
  value,
  onChange,
  error,
  id,
  "aria-describedby": describedBy,
}: FileUploadProps) {
  const [progress, setProgress] = useState<number | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const extensions = ACCEPTED_EXTENSIONS[kind];
  const uploading = progress !== null;

  async function upload(file: File) {
    setUploadError(null);
    setProgress(0);
    try {
      const uploaded: UploadedFile = await contentApi.upload(file, setProgress);
      onChange({
        id: uploaded.id,
        name: uploaded.original_name,
        url: uploaded.url,
      });
    } catch (caught) {
      setUploadError(errorMessage(caught));
    } finally {
      setProgress(null);
    }
  }

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    multiple: false,
    maxSize: MAX_UPLOAD_BYTES,
    disabled: uploading,
    // Our own button opens the picker; the zone itself is not a button
    noClick: true,
    noKeyboard: true,
    // Type by extension, like the backend (browsers report MIME types unevenly)
    validator: (file) =>
      extensions.includes(extensionOf(file.name))
        ? null
        : { code: WRONG_TYPE, message: "Wrong file type" },
    onDropAccepted: ([file]) => void upload(file),
    onDropRejected: ([rejection]) =>
      setUploadError(rejectionMessage(rejection, extensions)),
  });

  const message = uploadError ?? error;

  return (
    <div className="space-y-2">
      <div
        {...getRootProps({
          className: cn(
            "rounded-lg border transition-colors",
            !value && !uploading && "border-dashed",
            isDragActive && "border-ring bg-muted",
            message && !isDragActive && "border-destructive",
          ),
        })}
      >
        <input
          {...getInputProps({
            id,
            accept: extensions.join(","),
            "aria-describedby": describedBy,
          })}
        />

        {uploading ? (
          <div className="space-y-2 p-4">
            <p className="text-sm">Wysyłanie… {Math.round(progress * 100)}%</p>
            <div
              role="progressbar"
              aria-label="Wysyłanie pliku"
              aria-valuemin={0}
              aria-valuemax={100}
              aria-valuenow={Math.round(progress * 100)}
              className="h-2 overflow-hidden rounded-full bg-muted"
            >
              <div
                className="h-full bg-primary transition-[width]"
                style={{ width: `${progress * 100}%` }}
              />
            </div>
          </div>
        ) : value ? (
          <div className="flex items-center gap-3 p-3">
            <FileIcon aria-hidden="true" className="size-5 shrink-0" />
            <span className="min-w-0 flex-1 truncate text-sm font-medium">
              {value.name}
            </span>
            <Button type="button" variant="outline" size="sm" onClick={open}>
              Zmień plik
            </Button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3 p-6 text-center">
            <UploadIcon
              aria-hidden="true"
              className="size-6 text-muted-foreground"
            />
            <p className="text-sm text-muted-foreground">
              {isDragActive
                ? "Upuść plik tutaj"
                : "Przeciągnij plik tutaj albo"}
            </p>
            <Button type="button" variant="outline" onClick={open}>
              Wybierz plik
            </Button>
            <p className="text-xs text-muted-foreground">
              {extensions.join(", ")} · do 50 MB
            </p>
          </div>
        )}
      </div>

      {message && (
        <p role="alert" className="text-sm text-destructive">
          {message}
        </p>
      )}
    </div>
  );
}
