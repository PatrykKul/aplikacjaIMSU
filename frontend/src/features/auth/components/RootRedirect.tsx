"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { LandingPage } from "@/features/landing/components/LandingPage";
import { PageSpinner } from "@/shared/layout/page-states";

import { useCurrentUser } from "../hooks";

/** "/": the start page for guests, the dashboard for a signed-in user. */
export function RootRedirect() {
  const router = useRouter();
  const { data: user, isPending } = useCurrentUser();

  useEffect(() => {
    if (user) {
      router.replace("/dashboard");
    }
  }, [user, router]);

  if (isPending || user) {
    return <PageSpinner />;
  }
  return <LandingPage />;
}
