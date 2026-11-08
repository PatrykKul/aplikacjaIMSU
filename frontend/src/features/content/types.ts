import type { JSONContent } from "@tiptap/react";

/** Form of an attachment: visual, auditory, kinesthetic. */
export type Form = "V" | "A" | "K";

export const FORMS: Form[] = ["V", "A", "K"];

export const FORM_LABELS: Record<Form, string> = {
  V: "Wzrokowa (V)",
  A: "Słuchowa (A)",
  K: "Kinestetyczna (K)",
};

export type AttachmentKind = "image" | "video" | "audio" | "pdf" | "link";

export type FileKind = "image" | "audio" | "video" | "pdf";

/** Read-only fields the API adds to blocks for display; ignored when saving. */
type DisplayFields = {
  file_url?: string;
  file_name?: string | null;
  youtube_id?: string;
};

type AttachmentBase = DisplayFields & {
  id: string;
  type: "attachment";
  forms: Form[];
  title: string;
  description?: string;
};

export type ImageAttachment = AttachmentBase & {
  kind: "image";
  file_id: number;
  alt?: string;
};

export type VideoAttachment = AttachmentBase & {
  kind: "video";
  file_id?: number;
  youtube_url?: string;
};

export type AudioAttachment = AttachmentBase & {
  kind: "audio";
  file_id?: number;
  /** Read aloud by the browser's speech synthesis. */
  transcript?: string;
};

export type PdfAttachment = AttachmentBase & { kind: "pdf"; file_id: number };

export type LinkAttachment = AttachmentBase & { kind: "link"; url: string };

export type Attachment =
  | ImageAttachment
  | VideoAttachment
  | AudioAttachment
  | PdfAttachment
  | LinkAttachment;

export type TextBlock = { id: string; type: "text"; doc: JSONContent };

export type Block = TextBlock | Attachment;

export type LessonBlocks = { blocks: Block[] };

export type UploadedFile = {
  id: number;
  url: string;
  original_name: string;
  content_type: string;
  size: number;
  kind: FileKind;
};

/** Limit of the backend (`max_upload_bytes`). */
export const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;

/** Id of a new block: unique in the lesson, letters, digits and dashes only. */
export function newBlockId(): string {
  return `b-${crypto.randomUUID().slice(0, 8)}`;
}
