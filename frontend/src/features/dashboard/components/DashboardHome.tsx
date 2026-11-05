"use client";

import Link from "next/link";

import type { UserRole } from "@/features/auth/types";
import { useCurrentUser } from "@/features/auth/hooks";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

type RoleCard = { href: string; title: string; description: string };

const roleCards: Record<UserRole, RoleCard[]> = {
  student: [
    {
      href: "/courses",
      title: "Twoje kursy",
      description: "Wybierz kurs i ucz się krok po kroku.",
    },
  ],
  teacher: [
    {
      href: "/courses",
      title: "Kursy (podgląd)",
      description: "Zobacz lekcje tak, jak widzą je twoi uczniowie.",
    },
  ],
  admin: [
    {
      href: "/courses",
      title: "Kursy i publikacja",
      description: "Publikuj kursy dla uczniów albo wycofuj je z publikacji.",
    },
    {
      href: "/admin/users",
      title: "Użytkownicy",
      description: "Zmieniaj role i blokuj konta.",
    },
  ],
};

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
        {roleCards[user.role].map((card) => (
          <Link
            key={card.href}
            href={card.href}
            className="rounded-xl outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
          >
            <Card className="h-full transition-colors hover:bg-muted/50">
              <CardHeader>
                <CardTitle className="text-lg">{card.title}</CardTitle>
                <CardDescription className="text-base">
                  {card.description}
                </CardDescription>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
