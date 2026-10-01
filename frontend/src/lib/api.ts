import type {
  Blok,
  BlokTyp,
  Dzial,
  GlobalSearchResponse,
  Kurs,
  Profil,
  PytanieAnkiety,
  Styl,
  Temat,
  TokenResponse,
  Uzytkownik,
  WynikAnkiety,
} from "@/lib/types";
import { useAuthStore } from "@/store/useAuthStore";

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

/** Błąd API z kodem HTTP i opcjonalnym kodem domenowym (np. ANKIETA_WYMAGANA). */
export class ApiError extends Error {
  status: number;
  kod?: string;

  constructor(message: string, status: number, kod?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.kod = kod;
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  let message = res.statusText || "Błąd serwera";
  let kod: string | undefined;
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === "string") message = detail;
    else if (Array.isArray(detail)) message = "Nieprawidłowe dane w formularzu.";
    else if (detail && typeof detail === "object") {
      kod = typeof detail.kod === "string" ? detail.kod : undefined;
      if (typeof detail.komunikat === "string") message = detail.komunikat;
    }
  } catch {
    // Non-JSON error body — keep the status text
  }
  return new ApiError(message, res.status, kod);
}

/** fetch z nagłówkiem Authorization; 401 kończy sesję, ANKIETA_WYMAGANA cofa flagę ankiety. */
export async function authFetch(
  input: string | URL,
  init?: RequestInit,
  timeoutMs: number = DEFAULT_FETCH_TIMEOUT_MS
): Promise<Response> {
  const { token } = useAuthStore.getState();
  const headers = new Headers(init?.headers);
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const res = await fetchWithTimeout(input, { ...init, headers }, timeoutMs);
  if (res.status === 401 && token) {
    // Expired or revoked session — AuthGate redirects to the login page
    useAuthStore.getState().logout();
  }
  return res;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const url = `${getApiBase()}${path.startsWith("/") ? path : `/${path}`}`;
  const res = await authFetch(url, init);
  if (!res.ok) {
    const err = await toApiError(res);
    if (err.kod === "ANKIETA_WYMAGANA") {
      const { user, setUser } = useAuthStore.getState();
      if (user) setUser({ ...user, ankieta_wypelniona: false });
    }
    throw err;
  }
  return res.json() as Promise<T>;
}

function jsonInit(method: string, body?: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  };
}

// --- Auth ---

export async function login(data: { email: string; haslo: string }): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/logowanie", jsonInit("POST", data));
}

export async function register(data: {
  email: string;
  imie: string;
  haslo: string;
}): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/rejestracja", jsonInit("POST", data));
}

export async function getMe(): Promise<Uzytkownik> {
  return apiFetch<Uzytkownik>("/auth/me");
}

export async function getSearchIndex(): Promise<GlobalSearchResponse> {
  return apiFetch<GlobalSearchResponse>("/szukaj?q=");
}

// --- Ankieta VAK i profil ---

export async function getPytaniaAnkiety(): Promise<PytanieAnkiety[]> {
  return apiFetch<PytanieAnkiety[]>("/ankieta/pytania");
}

export async function wyslijAnkiete(
  odpowiedzi: { pytanie_id: number; odpowiedz_id: number }[]
): Promise<Profil> {
  return apiFetch<Profil>("/ankieta/odpowiedzi", jsonInit("POST", { odpowiedzi }));
}

export async function getHistoriaAnkiety(): Promise<WynikAnkiety[]> {
  return apiFetch<WynikAnkiety[]>("/ankieta/historia");
}

export async function getProfil(): Promise<Profil> {
  return apiFetch<Profil>("/profil");
}

export async function ustawStylRecznie(styl: Styl): Promise<Profil> {
  return apiFetch<Profil>("/profil/styl", jsonInit("PUT", { styl }));
}

export async function przywrocStylZAnkiety(): Promise<Profil> {
  return apiFetch<Profil>("/profil/styl", { method: "DELETE" });
}

// --- Kursy ---

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
  const res = await authFetch(url, { method: "POST", body }, DEFAULT_FETCH_TIMEOUT_MS * 2);
  if (!res.ok) throw await toApiError(res);
  return res.json() as Promise<{ image_url: string }>;
}
