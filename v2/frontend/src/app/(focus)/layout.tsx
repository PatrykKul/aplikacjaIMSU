import type { ReactNode } from "react";

import { AuthGuard } from "@/features/auth/components/AuthGuard";

// Focus mode (lesson): signed-in only, but without the app header
export default function FocusLayout({ children }: { children: ReactNode }) {
  return (
    <AuthGuard>
      <div className="flex min-h-svh flex-col">{children}</div>
    </AuthGuard>
  );
}
