import type { ReactNode } from "react";

import { AuthenticatedShell } from "@/features/auth/components/AuthenticatedShell";
import { AuthGuard } from "@/features/auth/components/AuthGuard";

export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <AuthenticatedShell>{children}</AuthenticatedShell>
    </AuthGuard>
  );
}
