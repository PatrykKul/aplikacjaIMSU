"use client";

import Link from "next/link";
import type { ReactNode } from "react";

import { PageMessage } from "@/shared/layout/page-states";

import { useCurrentUser } from "../hooks";
import type { UserRole } from "../types";

type RoleGateProps = { roles: UserRole[]; children: ReactNode };

export function RoleGate({ roles, children }: RoleGateProps) {
  const { data: user } = useCurrentUser();

  if (!user || !roles.includes(user.role)) {
    return (
      <PageMessage
        title="Nie masz dostępu do tej strony"
        description="Ta strona jest dostępna tylko dla innych ról."
        action={
          <Link
            href="/dashboard"
            className="text-sm font-medium underline underline-offset-4"
          >
            Wróć na stronę główną
          </Link>
        }
      />
    );
  }
  return children;
}
