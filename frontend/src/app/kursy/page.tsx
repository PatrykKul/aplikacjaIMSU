import { serverFetchJson } from "@/lib/server-fetch";
import type { Kurs } from "@/lib/types";
import { KursyListClient } from "./KursyListClient";

export const dynamic = "force-dynamic";

export default async function KursyPage() {
  let initialKursy: Kurs[] = [];
  try {
    initialKursy = await serverFetchJson<Kurs[]>("/kursy");
    if (process.env.NODE_ENV === "production") {
      initialKursy = initialKursy.filter((k) => k.is_published === true);
    }
  } catch {
    console.warn("Nie udało się pobrać /kursy — lista startuje pusta. Czy backend działa?");
  }
  return <KursyListClient initialKursy={initialKursy} />;
}
