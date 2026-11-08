import type { ReactNode } from "react";

import { AuthenticatedShell } from "@/features/auth/components/AuthenticatedShell";
import { AuthGuard } from "@/features/auth/components/AuthGuard";
import { SurveyGate } from "@/features/learning-style/components/SurveyGate";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <AuthenticatedShell>
        <SurveyGate>{children}</SurveyGate>
      </AuthenticatedShell>
    </AuthGuard>
  );
}
