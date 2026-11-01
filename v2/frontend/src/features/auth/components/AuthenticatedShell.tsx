"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { AppShell, type NavItem } from "@/shared/layout/AppShell";

import { useCurrentUser, useLogout } from "../hooks";
import { roleLabels } from "../roles";

export function AuthenticatedShell({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  if (!user) {
    return null; // AuthGuard above guarantees a user
  }

  const nav: NavItem[] =
    user.role === "admin"
      ? [{ href: "/admin/users", label: "Użytkownicy" }]
      : [];

  return (
    <AppShell
      nav={nav}
      user={{
        displayName: user.display_name,
        roleLabel: roleLabels[user.role],
      }}
      onLogout={() =>
        logout.mutate(undefined, { onSettled: () => router.replace("/login") })
      }
    >
      {children}
    </AppShell>
  );
}
