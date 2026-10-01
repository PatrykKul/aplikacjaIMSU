import { notFound } from "next/navigation";
import { serverFetchJson } from "@/lib/server-fetch";
import type { Dzial, Kurs } from "@/lib/types";
import { DzialPageClient } from "./DzialPageClient";

export const dynamic = "force-dynamic";

type PageProps = { params: Promise<{ dzialId: string }> };

export default async function DzialPage({ params }: PageProps) {
  const { dzialId: raw } = await params;
  const dzialId = Number(raw);
  if (!Number.isFinite(dzialId)) notFound();

  let dzial: Dzial;
  let kurs: Kurs;
  try {
    dzial = await serverFetchJson<Dzial>(`/dzialy/${dzialId}`);
    kurs = await serverFetchJson<Kurs>(`/kursy/${dzial.kurs_id}`);
  } catch {
    notFound();
  }
  return (
    <DzialPageClient
      dzialId={dzialId}
      initialDzial={dzial}
      initialKurs={kurs}
    />
  );
}
