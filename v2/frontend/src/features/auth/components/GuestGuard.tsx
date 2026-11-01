"use client";

import { useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { Spinner } from "@/shared/ui/spinner";

import { useCurrentUser } from "../hooks";

export function GuestGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { data: user, isPending } = useCurrentUser();

  useEffect(() => {
    if (user) {
      router.replace("/dashboard");
    }
  }, [user, router]);

  if (isPending || user) {
    return (
      <div className="flex justify-center py-10">
        <Spinner className="size-6" />
      </div>
    );
  }
  return children;
}
