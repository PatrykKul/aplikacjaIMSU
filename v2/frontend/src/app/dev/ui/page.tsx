import { notFound } from "next/navigation";

import { Button } from "@/shared/ui/button";

export default function DevUiPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }

  return (
    <main className="mx-auto max-w-3xl space-y-10 p-8">
      <h1 className="text-2xl font-semibold">Komponenty</h1>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Button</h2>
        <div className="flex flex-wrap gap-3">
          <Button>Domyślny</Button>
          <Button variant="secondary">Drugorzędny</Button>
          <Button variant="outline">Obrys</Button>
          <Button variant="ghost">Duch</Button>
          <Button variant="destructive">Usuń</Button>
          <Button disabled>Wyłączony</Button>
        </div>
      </section>
    </main>
  );
}
