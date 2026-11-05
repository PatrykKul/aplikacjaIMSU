"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { PageSpinner } from "@/shared/layout/page-states";

import { useCurrentUser } from "../hooks";

export function RootRedirect() {
  const router = useRouter();
  const { data: user, isError } = useCurrentUser();

  useEffect(() => {
    if (user) {
      router.replace("/dashboard");
    } else if (user === null || isError) {
      router.replace("/login");
    }
  }, [user, isError, router]);

  return <PageSpinner />;
}
