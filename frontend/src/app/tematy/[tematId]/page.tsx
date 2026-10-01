import { Suspense } from "react";
import { notFound } from "next/navigation";
import { TematPageClient } from "./TematPageClient";

type PageProps = { params: Promise<{ tematId: string }> };

export default async function TematPage({ params }: PageProps) {
  const tematId = Number((await params).tematId);
  if (!Number.isFinite(tematId)) notFound();
  return (
    // TematPageClient reads the query string (?styl=), which needs a Suspense boundary
    <Suspense fallback={null}>
      <TematPageClient tematId={tematId} />
    </Suspense>
  );
}
