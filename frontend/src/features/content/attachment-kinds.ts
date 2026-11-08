import {
  AudioLinesIcon,
  FileTextIcon,
  FilmIcon,
  ImageIcon,
  LinkIcon,
  type LucideIcon,
} from "lucide-react";

import type { AttachmentKind, FileKind } from "./types";

export const ATTACHMENT_KINDS: AttachmentKind[] = [
  "image",
  "video",
  "audio",
  "pdf",
  "link",
];

export const KIND_INFO: Record<
  AttachmentKind,
  { label: string; description: string; icon: LucideIcon }
> = {
  image: {
    label: "Obraz",
    description: "Rysunek, zdjęcie, schemat",
    icon: ImageIcon,
  },
  video: {
    label: "Wideo",
    description: "Plik albo film z YouTube",
    icon: FilmIcon,
  },
  audio: {
    label: "Nagranie",
    description: "Plik albo tekst czytany przez lektora",
    icon: AudioLinesIcon,
  },
  pdf: {
    label: "PDF",
    description: "Karta pracy, notatka",
    icon: FileTextIcon,
  },
  link: { label: "Link", description: "Strona w internecie", icon: LinkIcon },
};

/** Extensions accepted by the backend for each kind of file (`content/files.py`). */
export const ACCEPTED_EXTENSIONS: Record<FileKind, string[]> = {
  image: [".png", ".jpg", ".jpeg", ".webp", ".gif"],
  audio: [".mp3", ".ogg", ".wav", ".m4a"],
  video: [".mp4", ".webm"],
  pdf: [".pdf"],
};

const YOUTUBE_ID = /^[A-Za-z0-9_-]{11}$/;
const YOUTUBE_HOSTS = ["youtube.com", "m.youtube.com", "youtube-nocookie.com"];

/** Same rules as `youtube_id()` in the backend (`content/blocks.py`). */
export function youtubeId(address: string): string | null {
  let url: URL;
  try {
    url = new URL(address.trim());
  } catch {
    return null;
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    return null;
  }
  const host = url.hostname.replace(/^www\./, "");
  const parts = url.pathname.split("/").filter(Boolean);
  let candidate: string | null = null;
  if (host === "youtu.be") {
    candidate = parts[0] ?? null;
  } else if (YOUTUBE_HOSTS.includes(host)) {
    if (parts.length === 1 && parts[0] === "watch") {
      candidate = url.searchParams.get("v");
    } else if (parts.length >= 2 && ["embed", "shorts"].includes(parts[0])) {
      candidate = parts[1];
    }
  }
  return candidate && YOUTUBE_ID.test(candidate) ? candidate : null;
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024 * 1024) {
    return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  }
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} MB`;
}
