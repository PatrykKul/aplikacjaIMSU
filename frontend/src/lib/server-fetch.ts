import type { Dzial, Kurs, Temat } from "@/lib/types";

/** Limit czasu fetchu po stronie serwera (ms). */
const SERVER_FETCH_TIMEOUT_MS = 20_000;

function getServerApiBase(): string {
  const raw =
    process.env.NEXT_PUBLIC_API_URL ??
    process.env.API_URL ??
    "http://127.0.0.1:8000";
  return raw.replace(/\/$/, "");
}

/** Fetch JSON po stronie serwera (RSC) — zawsze świeże dane z API. */
export async function serverFetchJson<T>(path: string): Promise<T> {
  return serverFetchJsonWithOptions<T>(path, { cache: "no-store" });
}

type ServerFetchOptions = {
  cache?: RequestCache;
};

export async function serverFetchJsonWithOptions<T>(
  path: string,
  options?: ServerFetchOptions
): Promise<T> {
  const url = `${getServerApiBase()}${path.startsWith("/") ? path : `/${path}`}`;
  const ac = new AbortController();
  const t = setTimeout(() => ac.abort(), SERVER_FETCH_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      cache: options?.cache ?? "no-store",
      signal: ac.signal,
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      const text = await res.text();
      throw new Error(text || `${res.status} ${res.statusText}`);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(t);
  }
}

export async function fetchTematWithBreadcrumb(tematId: number): Promise<{
  temat: Temat;
  dzial: Dzial;
  kurs: Kurs;
}> {
  const temat = await serverFetchJson<Temat>(`/tematy/${tematId}`);
  const dzial = await serverFetchJson<Dzial>(`/dzialy/${temat.dzial_id}`);
  const kurs = await serverFetchJson<Kurs>(`/kursy/${dzial.kurs_id}`);
  return { temat, dzial, kurs };
}
