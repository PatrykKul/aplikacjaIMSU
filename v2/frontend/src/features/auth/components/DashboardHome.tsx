"use client";

import type { UserRole } from "@/features/auth/types";
import { useCurrentUser } from "@/features/auth/hooks";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

const roleCards: Record<UserRole, { title: string; description: string }> = {
  student: {
    title: "Tu pojawią się Twoje kursy",
    description:
      "Gdy nauczyciel doda Cię do klasy, zobaczysz tu swoje materiały.",
  },
  teacher: {
    title: "Tu pojawią się Twoje klasy",
    description: "Wkrótce utworzysz klasę i zaprosisz do niej uczniów.",
  },
  admin: {
    title: "Zarządzaj użytkownikami",
    description: "W zakładce „Użytkownicy” zmienisz role i zablokujesz konta.",
  },
};

export function DashboardHome() {
  const { data: user } = useCurrentUser();
  if (!user) {
    return null;
  }

  const firstName = user.display_name.split(" ")[0];
  const card = roleCards[user.role];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        Cześć, {firstName}!
      </h1>
      <Card>
        <CardHeader>
          <CardTitle>{card.title}</CardTitle>
          <CardDescription>{card.description}</CardDescription>
        </CardHeader>
      </Card>
    </div>
  );
}
