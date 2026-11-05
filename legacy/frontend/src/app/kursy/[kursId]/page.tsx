import { notFound } from "next/navigation";
import { KursDetailClient } from "./KursDetailClient";

type PageProps = { params: Promise<{ kursId: string }> };

export default async function KursPage({ params }: PageProps) {
  const kursId = Number((await params).kursId);
  if (!Number.isFinite(kursId)) notFound();
  return <KursDetailClient kursId={kursId} />;
}
