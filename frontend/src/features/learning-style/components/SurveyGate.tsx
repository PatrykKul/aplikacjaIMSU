"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect } from "react";

import { useCurrentUser } from "@/features/auth/hooks";
import { PageMessage, PageSpinner } from "@/shared/layout/page-states";
import { Button } from "@/shared/ui/button";

import { useLearningProfile } from "../hooks";

const SURVEY_PATH = "/survey";
const RESULT_PATH = "/survey/result";

/**
 * A student passes only with a style: without the survey they are sent to it,
 * with an unresolved tie to the result page to choose one style.
 * Teachers and admins pass through. Must be placed under AuthGuard.
 */
export function SurveyGate({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const isStudent = user?.role === "student";
  const profile = useLearningProfile(isStudent);
  const onSurvey =
    pathname === SURVEY_PATH || pathname.startsWith(`${SURVEY_PATH}/`);

  let target: string | null = null;
  if (isStudent && profile.data) {
    if (!profile.data.survey_completed) {
      target = SURVEY_PATH;
    } else if (profile.data.style === null) {
      target = RESULT_PATH;
    }
  }

  useEffect(() => {
    if (target && !onSurvey) {
      router.replace(target);
    }
  }, [target, onSurvey, router]);

  if (!isStudent || onSurvey) {
    return children;
  }
  if (profile.isError) {
    return (
      <PageMessage
        title="Nie udało się sprawdzić Twojego profilu"
        description="Sprawdź połączenie i spróbuj ponownie."
        action={
          <Button onClick={() => profile.refetch()}>Spróbuj ponownie</Button>
        }
      />
    );
  }
  if (profile.isPending || target) {
    return <PageSpinner />;
  }
  return children;
}
