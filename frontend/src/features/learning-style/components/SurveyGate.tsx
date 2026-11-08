"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { useCurrentUser } from "@/features/auth/hooks";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { useLearningProfile } from "../hooks";

const SURVEY_PATH = "/survey";

/**
 * A student who has not filled in the VAK survey is sent to it from every page.
 * Teachers and admins pass through. Must be placed under AuthGuard.
 */
export function SurveyGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const isStudent = user?.role === "student";
  const profile = useLearningProfile(isStudent);
  const onSurvey = pathname === SURVEY_PATH || pathname.startsWith(`${SURVEY_PATH}/`);
  const mustFillIn = isStudent && profile.data?.survey_completed === false;

  useEffect(() => {
    if (mustFillIn && !onSurvey) {
      router.replace(SURVEY_PATH);
    }
  }, [mustFillIn, onSurvey, router]);

  if (!isStudent || onSurvey) {
    return children;
  }
  if (profile.isError) {
    return (
      <PageMessage
        title="Nie udało się sprawdzić Twojego profilu"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={<Button onClick={() => profile.refetch()}>Spróbuj ponownie</Button>}
      />
    );
  }
  if (profile.isPending || mustFillIn) {
    return <PageSpinner />;
  }
  return children;
}
