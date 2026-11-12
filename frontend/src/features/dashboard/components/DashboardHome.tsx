"use client";

import {
  BookOpenIcon,
  ChartLineIcon,
  type LucideIcon,
  SlidersHorizontalIcon,
  UserCogIcon,
} from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useCurrentUser } from "@/features/auth/hooks";
import { isUnapprovedTeacher, PENDING_PATH } from "@/features/auth/roles";
import type { UserRole } from "@/features/auth/types";
import { PageSpinner } from "@/shared/layout/page-states";
import { Card, CardDescription, CardHeader, CardTitle } from "@/shared/ui/card";

type RoleCard = {
  href: string;
  title: string;
  description: string;
  icon: LucideIcon;
};

// The same order as the navigation of the role (AuthenticatedShell)
const roleCards: Record<UserRole, RoleCard[]> = {
  student: [
    {
      href: "/courses",
      title: "Kursy",
      description: "Zapisz się na kurs i ucz się lekcja po lekcji.",
      icon: BookOpenIcon,
    },
    {
      href: "/progress",
      title: "Moje postępy",
      description: "Wyniki lekcji, zmiany Twoich procentów i dziennik decyzji.",
      icon: ChartLineIcon,
    },
    {
      href: "/profile",
      title: "Mój styl",
      description: "Twój styl uczenia się i to, co mówią o nim wyniki quizów.",
      icon: SlidersHorizontalIcon,
    },
  ],
  teacher: [
    {
      href: "/teach",
      title: "Moje kursy",
      description:
        "Twórz lekcje w trzech wersjach, przyjmuj uczniów i sprawdzaj, która forma działa.",
      icon: BookOpenIcon,
    },
  ],
  admin: [
    {
      href: "/admin/users",
      title: "Użytkownicy",
      description:
        "Zatwierdzaj nauczycieli, dodawaj konta, edytuj je i blokuj.",
      icon: UserCogIcon,
    },
    {
      href: "/courses",
      title: "Kursy",
      description: "Przeglądaj kursy wszystkich nauczycieli.",
      icon: BookOpenIcon,
    },
  ],
};

export function DashboardHome() {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const mustWait = !!user && isUnapprovedTeacher(user);

  useEffect(() => {
    if (mustWait) {
      router.replace(PENDING_PATH);
    }
  }, [mustWait, router]);

  if (!user || mustWait) {
    return <PageSpinner />;
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
