import type { Blok, BlokTyp, Dzial, Kurs, Temat } from "@/lib/types";

/** Stały adres API (127.0.0.1:8000); opcjonalnie nadpisz NEXT_PUBLIC_API_URL. */
export const API_BASE_DEFAULT = "http://127.0.0.1:8000";

/** Domyślny limit — gdy backend nie odpowiada (SQLite / zawieszony uvicorn), UI nie wisi w nieskończoność. */
export const DEFAULT_FETCH_TIMEOUT_MS = 20_000;

export function getApiBase(): string {
  return (process.env.NEXT_PUBLIC_API_URL ?? API_BASE_DEFAULT).replace(/\/$/, "");
}

/**
 * fetch z limitem czasu; przy przekroczeniu przeglądarka rzuca AbortError.
 */
export async function fetchWithTimeout(
  input: string | URL,
  init: RequestInit | undefined,
  timeoutMs: number
): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  const userSignal = init?.signal;
  if (userSignal) {
    if (userSignal.aborted) controller.abort();
    else
      userSignal.addEventListener("abort", () => controller.abort(), {
        once: true,
      });
  }
  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(id);
  }
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = `${getApiBase()}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await fetchWithTimeout(url, init, DEFAULT_FETCH_TIMEOUT_MS);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export type TematUpdatePayload = { tytul?: string };

export async function updateTemat(
  id: number,
  data: TematUpdatePayload
): Promise<Temat> {
  return apiFetch<Temat>(`/tematy/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export type BlokCreatePayload = {
  typ: BlokTyp;
  tresc: string;
  odpowiedz?: string | null;
  rozwiazanie?: string | null;
  kolejnosc?: number | null;
  image_url?: string | null;
};

export type BlokUpdatePayload = {
  typ?: BlokTyp;
  tresc?: string;
  odpowiedz?: string | null;
  rozwiazanie?: string | null;
  kolejnosc?: number;
  image_url?: string | null;
};

export async function createBlok(
  tematId: number,
  data: BlokCreatePayload
): Promise<Blok> {
  return apiFetch<Blok>(`/tematy/${tematId}/bloki`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function updateBlok(
  blokId: number,
  data: BlokUpdatePayload
): Promise<Blok> {
  return apiFetch<Blok>(`/bloki/${blokId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
}

export async function deleteBlok(blokId: number): Promise<void> {
  await apiFetch<{ status: string }>(`/bloki/${blokId}`, { method: "DELETE" });
}

export async function reorderBloki(
  tematId: number,
  ids: number[]
): Promise<Temat> {
  return apiFetch<Temat>(`/tematy/${tematId}/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
}

export async function reorderKursy(ids: number[]): Promise<Kurs[]> {
  return apiFetch<Kurs[]>("/kursy/reorder", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
}

export type KursPayload = {
  nazwa: string;
  opis: string;
  is_published: boolean;
};

export async function getKursy(): Promise<Kurs[]> {
  return apiFetch<Kurs[]>("/kursy");
}

export async function createKurs(payload: KursPayload): Promise<Kurs> {
  return apiFetch<Kurs>("/kursy", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function updateKurs(kursId: number, payload: KursPayload): Promise<Kurs> {
  return apiFetch<Kurs>(`/kursy/${kursId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function deleteKurs(kursId: number): Promise<void> {
  await apiFetch<{ status: string }>(`/kursy/${kursId}`, { method: "DELETE" });
}

export async function reorderDzialy(kursId: number, ids: number[]): Promise<Kurs> {
  return apiFetch<Kurs>(`/kursy/${kursId}/dzialy/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
}

export async function reorderTematy(dzialId: number, ids: number[]): Promise<Dzial> {
  return apiFetch<Dzial>(`/dzialy/${dzialId}/tematy/reorder`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
}

export async function generujBlokiAI(tematId: number): Promise<Temat> {
  return apiFetch<Temat>(`/tematy/${tematId}/generuj-bloki`, {
    method: "PUT",
  });
}

export type UploadImageContext = {
  kursNazwa: string;
  dzialNazwa: string;
  tematNazwa: string;
};

export async function uploadImage(
  file: File,
  ctx: UploadImageContext
): Promise<{ image_url: string }> {
  const url = `${getApiBase()}/upload-image`;
  const body = new FormData();
  body.append("file", file);
  body.append("kurs_nazwa", ctx.kursNazwa);
  body.append("dzial_nazwa", ctx.dzialNazwa);
  body.append("temat_nazwa", ctx.tematNazwa);
  const res = await fetchWithTimeout(
    url,
    { method: "POST", body },
    DEFAULT_FETCH_TIMEOUT_MS * 2
  );
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<{ image_url: string }>;
}
