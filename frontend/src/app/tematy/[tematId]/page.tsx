import { notFound } from "next/navigation";
import { TematPageClient } from "./TematPageClient";

type PageProps = { params: Promise<{ tematId: string }> };

export default async function TematPage({ params }: PageProps) {
  const tematId = Number((await params).tematId);
  if (!Number.isFinite(tematId)) notFound();
  return <TematPageClient tematId={tematId} />;
}
