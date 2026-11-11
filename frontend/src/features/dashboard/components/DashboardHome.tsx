"use client";

import {
  BookOpenIcon,
  type LucideIcon,
  SlidersHorizontalIcon,
  UserCogIcon,
  UsersIcon,
} from "lucide-react";
import Link from "next/link";

import { useCurrentUser } from "@/features/auth/hooks";
import type { UserRole } from "@/features/auth/types";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

type RoleCard = {
  href: string;
  title: string;
  description: string;
  icon: LucideIcon;
};

// The same order as the navigation of the role
const roleCards: Record<UserRole, RoleCard[]> = {
  student: [
    {
      href: "/courses",
      title: "Kursy",
      description: "Wybierz kurs i ucz się lekcja po lekcji.",
      icon: BookOpenIcon,
    },
    {
      href: "/classes",
      title: "Moje klasy",
      description: "Kursy od Twoich nauczycieli i kontakt z nimi.",
      icon: UsersIcon,
    },
    {
      href: "/profile",
      title: "Mój styl",
      description: "Zobacz swój styl uczenia się i jak zmienia się po quizach.",
      icon: SlidersHorizontalIcon,
    },
  ],
  teacher: [
    {
      href: "/teach",
      title: "Moje kursy",
      description: "Twórz kursy i lekcje.",
      icon: BookOpenIcon,
    },
    {
      href: "/teach/classes",
      title: "Klasy",
      description: "Dodawaj uczniów do klas i przypisuj im swoje kursy.",
      icon: UsersIcon,
    },
  ],
  admin: [
    {
      href: "/courses",
      title: "Kursy nauczycieli",
      description: "Przeglądaj kursy wszystkich nauczycieli.",
      icon: BookOpenIcon,
    },
    {
      href: "/admin/users",
      title: "Użytkownicy",
      description: "Dodawaj nauczycieli i uczniów, edytuj i blokuj konta.",
      icon: UserCogIcon,
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
      <ul role="list" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {roleCards[user.role].map(
          ({ href, title, description, icon: Icon }) => (
            <li key={href}>
              {/* The title link stretches over the whole card, as in CourseCard */}
              <Card className="relative h-full transition-colors hover:bg-muted/50 has-[a:focus-visible]:ring-3 has-[a:focus-visible]:ring-ring/50">
                <CardHeader className="gap-3">
                  <span
                    aria-hidden="true"
                    className="flex size-10 items-center justify-center rounded-full bg-accent text-accent-foreground"
                  >
                    <Icon className="size-5" />
                  </span>
                  <CardTitle className="text-lg">
                    <Link
                      href={href}
                      className="outline-none after:absolute after:inset-0"
                    >
                      {title}
                    </Link>
                  </CardTitle>
                  <CardDescription className="text-base">
                    {description}
                  </CardDescription>
                </CardHeader>
              </Card>
            </li>
          ),
        )}
      </ul>
    </div>
  );
}
