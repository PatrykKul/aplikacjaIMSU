"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { PageMessage, PageSpinner } from "@/shared/layout/page-states";

import { useCurrentUser } from "../hooks";
import { isUnapprovedTeacher, PENDING_PATH } from "../roles";
import type { UserRole } from "../types";

type RoleGateProps = { roles: UserRole[]; children: ReactNode };

/**
 * Shows the page only to the given roles. A teacher the admin has not
 * approved is sent to the waiting screen from every teacher page.
 */
export function RoleGate({ roles, children }: RoleGateProps) {
  const router = useRouter();
  const { data: user } = useCurrentUser();
  const mustWait = !!user && isUnapprovedTeacher(user);

  useEffect(() => {
    if (mustWait) {
      router.replace(PENDING_PATH);
    }
  }, [mustWait, router]);

  if (user && roles.includes(user.role) && mustWait) {
    return <PageSpinner />;
  }
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
