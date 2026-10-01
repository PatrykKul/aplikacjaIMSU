import { notFound } from "next/navigation";
import { serverFetchJson } from "@/lib/server-fetch";
import type { Kurs } from "@/lib/types";
import { KursDetailClient } from "./KursDetailClient";

export const dynamic = "force-dynamic";

type PageProps = { params: Promise<{ kursId: string }> };

export default async function KursPage({ params }: PageProps) {
  const { kursId: raw } = await params;
  const kursId = Number(raw);
  if (!Number.isFinite(kursId)) notFound();

  let kurs: Kurs;
  try {
    kurs = await serverFetchJson<Kurs>(`/kursy/${kursId}`);
  } catch {
    notFound();
  }
  return <KursDetailClient kursId={kursId} initialKurs={kurs} />;
}
