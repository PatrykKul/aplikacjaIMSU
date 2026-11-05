"use client";

import Link from "next/link";
import { homeFor } from "@/components/auth/AuthGate";
import { useAuthStore } from "@/store/useAuthStore";

const PRIMARY =
  "inline-flex items-center rounded-xl bg-primary px-6 py-3 font-semibold text-primary-foreground shadow-neon-sm transition hover:opacity-90";
const SECONDARY =
  "inline-flex items-center rounded-xl border border-slate-300 bg-white/80 px-6 py-3 font-semibold text-slate-800 transition hover:border-primary/50 dark:border-white/15 dark:bg-white/[0.04] dark:text-slate-100";

/** Landing page buttons: register / log in, or a shortcut to the panel when already logged in. */
export function LandingCta() {
  const hydrated = useAuthStore((s) => s.hydrated);
  const user = useAuthStore((s) => s.user);

  return (
    <div className="flex flex-wrap items-center justify-center gap-3">
      {hydrated && user ? (
        <Link href={homeFor(user)} className={PRIMARY}>
          Przejdź do swojego panelu
        </Link>
      ) : (
        <>
          <Link href="/rejestracja" className={PRIMARY}>
            Załóż konto
          </Link>
          <Link href="/logowanie" className={SECONDARY}>
            Zaloguj się
          </Link>
        </>
      )}
    </div>
  );
}
