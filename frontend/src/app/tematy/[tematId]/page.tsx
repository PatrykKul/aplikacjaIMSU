import { notFound } from "next/navigation";
import { fetchTematWithBreadcrumb } from "@/lib/server-fetch";
import { TematPageClient } from "./TematPageClient";

export const dynamic = "force-dynamic";

type PageProps = { params: Promise<{ tematId: string }> };

export default async function TematPage({ params }: PageProps) {
  const { tematId: raw } = await params;
  const tematId = Number(raw);
  if (!Number.isFinite(tematId)) notFound();

  let dane: Awaited<ReturnType<typeof fetchTematWithBreadcrumb>>;
  try {
    dane = await fetchTematWithBreadcrumb(tematId);
  } catch {
    notFound();
  }
  return (
    <TematPageClient
      tematId={tematId}
      initialTemat={dane.temat}
      initialDzial={dane.dzial}
      initialKurs={dane.kurs}
    />
  );
}
