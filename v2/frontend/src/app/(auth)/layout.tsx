import type { ReactNode } from "react";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted px-4 py-10">
      <div className="text-center">
        <p className="text-2xl font-semibold tracking-tight">IMSU</p>
        <p className="text-sm text-muted-foreground">
          Nauka matematyki na Twoją miarę
        </p>
      </div>
      <main className="w-full max-w-sm">{children}</main>
    </div>
  );
}
