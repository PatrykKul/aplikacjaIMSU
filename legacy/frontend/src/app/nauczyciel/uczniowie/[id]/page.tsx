import { notFound } from "next/navigation";
import { UczenSzczegolyClient } from "./UczenSzczegolyClient";

type PageProps = { params: Promise<{ id: string }> };

export default async function UczenPage({ params }: PageProps) {
  const id = Number((await params).id);
  if (!Number.isFinite(id)) notFound();
  return <UczenSzczegolyClient uczenId={id} />;
}
