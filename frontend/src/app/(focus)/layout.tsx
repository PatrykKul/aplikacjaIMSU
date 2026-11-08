import type { ReactNode } from "react";

import { AuthGuard } from "@/features/auth/components/AuthGuard";
import { SurveyGate } from "@/features/learning-style/components/SurveyGate";

// Focus mode (lesson): signed-in only, but without the app header
export default function FocusLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <SurveyGate>
        <div className="flex min-h-svh flex-col">{children}</div>
      </SurveyGate>
    </AuthGuard>
  );
}
