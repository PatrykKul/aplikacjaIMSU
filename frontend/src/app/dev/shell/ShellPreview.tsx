"use client";

import { AppShell } from "@/shared/layout/AppShell";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

export function ShellPreview() {
  return (
    <AppShell
      nav={[{ href: "/dev/shell", label: "Użytkownicy" }]}
      user={{ displayName: "Jan Kowalski", roleLabel: "Administrator" }}
      onLogout={() => alert("Wylogowano (podgląd)")}
    >
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold tracking-tight">Cześć, Jan!</h1>
        <Card>
          <CardHeader>
            <CardTitle>Tu pojawią się Twoje kursy</CardTitle>
            <CardDescription>
              Gdy nauczyciel doda Cię do klasy, zobaczysz tu swoje materiały.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    </AppShell>
  );
}
