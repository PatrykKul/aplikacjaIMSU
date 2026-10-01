"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQueryClient } from "@tanstack/react-query";
import { LogOut } from "lucide-react";
import { ROLA_LABEL } from "@/lib/labels";
import { useAdminStore } from "@/store/useAdminStore";
import { useAuthStore } from "@/store/useAuthStore";

export function UserMenu() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const setIsAdmin = useAdminStore((s) => s.setIsAdmin);

  if (!user) return null;

  const onLogout = () => {
    setIsAdmin(false);
    logout();
    queryClient.clear();
    router.replace("/logowanie");
  };

  return (
    <div className="flex shrink-0 items-center gap-2">
      <Link
        href="/profil"
        title="Mój profil"
        className="hidden rounded-xl px-2 py-1 text-right leading-tight transition hover:bg-slate-100 md:block dark:hover:bg-white/5"
      >
        <span className="block max-w-[10rem] truncate text-sm font-semibold text-slate-900 dark:text-white">
          {user.imie || user.email}
        </span>
        <span className="block text-[11px] uppercase tracking-wider text-slate-500 dark:text-slate-400">
          {ROLA_LABEL[user.rola]}
        </span>
      </Link>
      <button
        type="button"
        onClick={onLogout}
        title="Wyloguj"
        aria-label="Wyloguj"
        className="rounded-xl border border-slate-200 bg-white/70 p-2 text-slate-600 transition hover:border-rose-300 hover:text-rose-600 dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-slate-300 dark:hover:text-rose-300"
      >
        <LogOut className="h-4 w-4" aria-hidden />
      </button>
    </div>
  );
}
