"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { getMe } from "@/lib/api";
import type { Rola, Uzytkownik } from "@/lib/types";
import { useAuthStore } from "@/store/useAuthStore";

export const PUBLIC_PATHS = ["/", "/logowanie", "/rejestracja"];
const AUTH_FORM_PATHS = ["/logowanie", "/rejestracja"];

/** Path prefixes restricted to given roles. */
const ROLE_PREFIXES: { prefix: string; role: Rola[] }[] = [
  { prefix: "/admin", role: ["admin"] },
  { prefix: "/nauczyciel", role: ["nauczyciel", "admin"] },
];

export function homeFor(user: Uzytkownik): string {
  if (user.rola === "uczen" && !user.ankieta_wypelniona) return "/ankieta";
  return "/kursy";
}

/** Where the user must be sent instead of `pathname`, or null when the page is allowed. */
function redirectTarget(pathname: string, user: Uzytkownik | null): string | null {
  const isPublic = PUBLIC_PATHS.includes(pathname);
  if (!user) return isPublic ? null : "/logowanie";
  if (AUTH_FORM_PATHS.includes(pathname)) return homeFor(user);
  // Survey gate: a student without a completed survey can only see the survey
  if (user.rola === "uczen" && !user.ankieta_wypelniona && pathname !== "/" && !pathname.startsWith("/ankieta")) {
    return "/ankieta";
  }
  const rule = ROLE_PREFIXES.find((r) => pathname.startsWith(r.prefix));
  if (rule && !rule.role.includes(user.rola)) return "/kursy";
  return null;
}

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const hydrated = useAuthStore((s) => s.hydrated);
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);

  // Read the persisted session from localStorage once, on the client
  useEffect(() => {
    void Promise.resolve(useAuthStore.persist.rehydrate()).then(() => {
      useAuthStore.setState({ hydrated: true });
    });
  }, []);

  // Refresh role / survey flag from the server on every app load
  const me = useQuery({
    queryKey: ["me", token],
    queryFn: getMe,
    enabled: hydrated && !!token,
    staleTime: 60_000,
  });

  useEffect(() => {
    if (me.data) setUser(me.data);
  }, [me.data, setUser]);

  const target = hydrated ? redirectTarget(pathname, token ? user : null) : null;

  useEffect(() => {
    if (target) router.replace(target);
  }, [target, router]);

  const isPublic = PUBLIC_PATHS.includes(pathname);
  if ((!hydrated && !isPublic) || target) {
    return (
      <div className="flex flex-1 items-center justify-center p-16">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Ładowanie" />
      </div>
    );
  }

  return <>{children}</>;
}
