"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { AppShell, type NavItem } from "@/shared/layout/AppShell";

import { useCurrentUser, useLogout } from "../hooks";
import { isUnapprovedTeacher, roleLabels } from "../roles";
import type { UserRole } from "../types";

const navByRole: Record<UserRole, NavItem[]> = {
  student: [
    { href: "/courses", label: "Kursy" },
    { href: "/progress", label: "Moje postępy" },
    { href: "/profile", label: "Mój styl" },
  ],
  teacher: [{ href: "/teach", label: "Moje kursy" }],
  admin: [
    { href: "/admin/users", label: "Użytkownicy" },
    { href: "/courses", label: "Kursy" },
  ],
};

export function AuthenticatedShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  if (!user) {
    return null; // AuthGuard above guarantees a user
  }

  // A teacher waiting for approval has nothing to open yet
  const nav: NavItem[] = isUnapprovedTeacher(user) ? [] : navByRole[user.role];

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
