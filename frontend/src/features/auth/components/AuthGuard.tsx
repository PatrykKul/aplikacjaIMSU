"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { useCurrentUser } from "../hooks";

export function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isError, isPending, refetch } = useCurrentUser();

  useEffect(() => {
    if (user === null) {
      router.replace("/login");
    }
  }, [user, router]);

  if (isError) {
    return (
      <PageMessage
        fullScreen
        title="Brak połączenia z serwerem"
        description="Sprawdź połączenie z internetem i spróbuj ponownie."
        action={<Button onClick={() => refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }
  if (isPending || user === null) {
    return <PageSpinner />;
  }
  return children;
}
