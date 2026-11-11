import Link from "next/link";
import type { ReactNode } from "react";

import { GuestGuard } from "@/features/auth/components/GuestGuard";
import { Logo } from "@/shared/layout/Logo";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted px-4 py-10">
      <div className="flex flex-col items-center gap-2 text-center">
        <Link
          href="/"
          aria-label="IMSU - strona startowa"
          className="rounded-lg outline-none focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          <Logo size="lg" />
        </Link>
        <p className="text-sm text-muted-foreground">Nauka na Twoją miarę</p>
      </div>
      <main className="w-full max-w-sm">
        <GuestGuard>{children}</GuestGuard>
      </main>
    </div>
  );
}
