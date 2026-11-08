"use client";

import Link from "next/link";

import { useCurrentUser } from "@/features/auth/hooks";
import type { UserRole } from "@/features/auth/types";
import { Badge } from "@/shared/ui/badge";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

type RoleCard = { title: string; description: string; href?: string };

const roleCards: Record<UserRole, RoleCard[]> = {
  student: [
    {
      title: "Twoje kursy",
      description: "Zapisz się na kurs.",
    },
  ],
  teacher: [
    {
      href: "/teach",
      title: "Moje kursy",
      description: "Twórz kursy i lekcje.",
    },
  ],
  admin: [
    {
      href: "/admin/users",
      title: "Użytkownicy",
      description: "Dodawaj nauczycieli i uczniów, edytuj i blokuj konta.",
    },
    {
      title: "Kursy nauczycieli",
      description: "Przeglądaj kursy, wycofuj publikację i archiwizuj.",
    },
  ],
};

function CardBody({ card }: { card: RoleCard }) {
  return (
    <CardHeader>
      <CardTitle className="flex items-center gap-2 text-lg">
        {card.title}
        {!card.href && <Badge variant="secondary">Wkrótce</Badge>}
      </CardTitle>
      <CardDescription className="text-base">
        {card.description}
      </CardDescription>
    </CardHeader>
  );
}

export function DashboardHome() {
  const { data: user } = useCurrentUser();
  if (!user) {
    return null;
  }

  const firstName = user.display_name.split(" ")[0];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">
        Cześć, {firstName}!
      </h1>
      <div className="grid gap-4 sm:grid-cols-2">
        {roleCards[user.role].map((card) =>
          card.href ? (
            <Link
              key={card.title}
              href={card.href}
              className="rounded-xl outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
            >
              <Card className="h-full transition-colors hover:bg-muted/50">
                <CardBody card={card} />
              </Card>
            </Link>
          ) : (
            <Card key={card.title} className="h-full">
              <CardBody card={card} />
            </Card>
          ),
        )}
      </div>
    </div>
  );
}
