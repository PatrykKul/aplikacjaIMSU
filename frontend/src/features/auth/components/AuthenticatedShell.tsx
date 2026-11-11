"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { AppShell, type NavItem } from "@/shared/layout/AppShell";

import { useCurrentUser, useLogout } from "../hooks";
import { roleLabels } from "../roles";
import type { UserRole } from "../types";

const navByRole: Record<UserRole, NavItem[]> = {
  student: [
    { href: "/courses", label: "Kursy" },
    { href: "/classes", label: "Moje klasy" },
    { href: "/profile", label: "Mój styl" },
  ],
  teacher: [
    { href: "/teach", label: "Moje kursy" },
    { href: "/teach/classes", label: "Klasy" },
  ],
  admin: [
    { href: "/courses", label: "Kursy" },
    { href: "/admin/users", label: "Użytkownicy" },
  ],
};

export function AuthenticatedShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  if (!user) {
    return null; // AuthGuard above guarantees a user
  }

  const nav: NavItem[] = navByRole[user.role];

  return (
    <AppShell
      nav={nav}
      user={{
        displayName: user.display_name,
        roleLabel: roleLabels[user.role],
      }}
      onLogout={() =>
        logout.mutate(undefined, { onSettled: () => router.replace("/") })
      }
    >
      {children}
    </AppShell>
  );
}
