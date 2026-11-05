/** Shared Tailwind class strings for panels. */
export const CARD =
  "rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm md:p-8 dark:border-white/10 dark:bg-slate-900/80";

export const BTN_PRIMARY =
  "inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-4 py-2 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95 disabled:opacity-50";

export const BTN_SECONDARY =
  "inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-primary/40 disabled:opacity-50 dark:border-white/10 dark:text-slate-200";

export const INPUT =
  "w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/25 dark:border-white/10 dark:bg-slate-950 dark:text-slate-100";

export const TH = "px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider text-slate-500";
export const TD = "px-3 py-3 align-middle text-sm text-slate-700 dark:text-slate-300";

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("pl-PL", { dateStyle: "medium", timeStyle: "short" });
}
