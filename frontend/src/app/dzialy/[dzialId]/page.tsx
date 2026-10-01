import { notFound } from "next/navigation";
import { DzialPageClient } from "./DzialPageClient";

type PageProps = { params: Promise<{ dzialId: string }> };

export default async function DzialPage({ params }: PageProps) {
  const dzialId = Number((await params).dzialId);
  if (!Number.isFinite(dzialId)) notFound();
  return <DzialPageClient dzialId={dzialId} />;
}
