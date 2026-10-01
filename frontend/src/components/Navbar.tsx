"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  FolderOpen,
  GraduationCap,
  Search,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import type { GlobalSearchResponse } from "@/lib/types";
import { useQuery } from "@tanstack/react-query";
import { getSearchIndex } from "@/lib/api";
import { useAdminStore } from "@/store/useAdminStore";
import { useAuthStore } from "@/store/useAuthStore";
import { ThemeToggle } from "@/components/ThemeToggle";
import { UserMenu } from "@/components/UserMenu";

const DEBOUNCE_MS = 350;

const EMPTY_INDEX: GlobalSearchResponse = { dzialy: [], tematy: [] };

export function Navbar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const canEdit = user?.rola === "nauczyciel" || user?.rola === "admin";
  const { data: searchIndex = EMPTY_INDEX } = useQuery({
    queryKey: ["szukaj-indeks"],
    queryFn: getSearchIndex,
    // A student without the survey has no access to materials yet
    enabled: !!user && (user.rola !== "uczen" || user.ankieta_wypelniona),
    staleTime: 60_000,
  });
  const isAdmin = useAdminStore((s) => s.isAdmin);
  const setIsAdmin = useAdminStore((s) => s.setIsAdmin);
  const [query, setQuery] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const [results, setResults] = useState<GlobalSearchResponse | null>(null);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(query.trim()), DEBOUNCE_MS);
    return () => clearTimeout(t);
  }, [query]);

  useEffect(() => {
    if (!debounced) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setResults(null);
      return;
    }

    const q = debounced.toLowerCase();
    const data: GlobalSearchResponse = {
      dzialy: searchIndex.dzialy.filter((item) =>
        item.nazwa.toLowerCase().includes(q)
      ),
      tematy: searchIndex.tematy.filter((item) =>
        item.tytul.toLowerCase().includes(q)
      ),
    };
    setResults(data);
    setOpen(true);
  }, [debounced, searchIndex]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setOpen(false);
    setQuery("");
    setDebounced("");
    setResults(null);
  }, [pathname]);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const onFocus = useCallback(() => {
    if (results && query.trim()) setOpen(true);
  }, [results, query]);

  const dzialy = results?.dzialy ?? [];
  const tematy = results?.tematy ?? [];
  const hasResults = dzialy.length > 0 || tematy.length > 0;
  const showPanel = open && debounced.length > 0;
  const isKursyIndex = pathname === "/kursy";

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 shadow-[0_8px_32px_rgba(15,23,42,0.1)] backdrop-blur-xl supports-[backdrop-filter]:bg-white/70 dark:border-white/[0.06] dark:bg-slate-950/80 dark:shadow-[0_8px_32px_rgba(0,0,0,0.35)] dark:supports-[backdrop-filter]:bg-slate-950/70">
      <div className="mx-auto flex max-w-7xl items-center gap-4 px-4 py-3 md:px-8">
        {isKursyIndex ? (
          <Link
            href="/"
            className="group flex shrink-0 items-center gap-2 text-sm font-medium text-slate-600 transition hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
          >
            <ArrowLeft className="h-4 w-4 shrink-0 transition group-hover:-translate-x-0.5" aria-hidden />
            <span>Powrót</span>
          </Link>
        ) : null}
        <Link
          href="/kursy"
          className="group flex shrink-0 items-center gap-3 text-slate-900 transition-opacity hover:opacity-95 dark:text-white"
        >
          <div className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 to-secondary/20 shadow-neon-sm ring-1 ring-white/12 transition-transform group-hover:scale-[1.03]">
            <GraduationCap className="relative h-6 w-6 text-sky-50" />
          </div>
          <div className="hidden leading-tight sm:block">
            <span className="block bg-gradient-to-r from-primary via-cyan-200 to-secondary bg-clip-text text-lg font-bold tracking-tight text-transparent">
              StylNauki
            </span>
          </div>
        </Link>

        <div ref={wrapRef} className="relative mx-auto w-full max-w-xl flex-1">
          <div className="pointer-events-none absolute inset-y-0 left-3.5 flex items-center">
            <Search className="h-4 w-4 text-primary/80" />
          </div>
          <input
            type="search"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              if (e.target.value.trim()) setOpen(true);
            }}
            onFocus={onFocus}
            placeholder="Szukaj działów i tematów…"
            className="w-full rounded-2xl border border-primary/35 bg-white py-2.5 pl-11 pr-4 text-sm text-slate-900 shadow-[inset_0_0_20px_rgba(14,165,233,0.06)] outline-none ring-0 transition placeholder:text-slate-400 focus:border-secondary/50 focus:bg-white focus:shadow-[0_0_0_3px_rgba(168,85,247,0.2),inset_0_0_24px_rgba(236,72,153,0.06)] dark:bg-white/[0.04] dark:text-slate-100 dark:placeholder:text-slate-500"
            aria-autocomplete="list"
          />

          <AnimatePresence>
            {showPanel && (
              <motion.div
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.2 }}
                className="absolute left-0 right-0 top-[calc(100%+10px)] max-h-[min(70vh,440px)] overflow-y-auto rounded-2xl border border-slate-200 bg-white/95 shadow-xl ring-1 ring-primary/20 backdrop-blur-2xl dark:border-white/10 dark:bg-slate-950/95 dark:shadow-neon"
              >
                {!hasResults ? (
                  <p className="px-4 py-8 text-center text-sm text-slate-500">
                    Brak wyników dla „{debounced}”
                  </p>
                ) : (
                  <div className="p-2">
                    {dzialy.length > 0 && (
                      <div className="mb-1">
                        <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-[0.2em] text-primary/90">
                          Działy
                        </p>
                        <ul className="space-y-0.5">
                          {dzialy.map((d) => (
                            <li key={`d-${d.id}`}>
                              <Link
                                href={`/dzialy/${d.id}`}
                                onClick={() => setOpen(false)}
                                className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-slate-700 transition hover:bg-primary/10 hover:text-slate-900 dark:text-slate-200 dark:hover:text-white"
                              >
                                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/25">
                                  <FolderOpen className="h-4 w-4 text-primary" />
                                </span>
                                <span className="line-clamp-1">{d.nazwa}</span>
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {tematy.length > 0 && (
                      <div>
                        <p className="px-3 py-2 text-[10px] font-bold uppercase tracking-[0.2em] text-secondary/90">
                          Tematy
                        </p>
                        <ul className="space-y-0.5">
                          {tematy.map((t) => (
                            <li key={`t-${t.id}`}>
                              <Link
                                href={`/tematy/${t.id}`}
                                onClick={() => setOpen(false)}
                                className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-slate-700 transition hover:bg-secondary/10 hover:text-slate-900 dark:text-slate-200 dark:hover:text-white"
                              >
                                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-secondary/15 ring-1 ring-secondary/25">
                                  <BookOpen className="h-4 w-4 text-secondary" />
                                </span>
                                <span className="line-clamp-1">{t.tytul}</span>
                              </Link>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <ThemeToggle />

        {canEdit && (
          <label className="flex shrink-0 cursor-pointer select-none items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-3 py-2 backdrop-blur-sm dark:border-white/[0.08] dark:bg-white/[0.03]">
            <span className="hidden text-xs font-medium text-slate-600 sm:inline dark:text-slate-400">
              Tryb Edycji
            </span>
            <button
              type="button"
              role="switch"
              aria-checked={isAdmin}
              onClick={() => setIsAdmin(!isAdmin)}
              className={`relative h-7 w-12 shrink-0 rounded-full transition-colors ${
                isAdmin
                  ? "bg-gradient-to-r from-primary to-secondary shadow-neon-sm"
                  : "bg-slate-700/80"
              }`}
            >
              <span
                className={`absolute top-1 h-5 w-5 rounded-full bg-white shadow-md transition-all ${
                  isAdmin ? "right-1 left-auto" : "left-1"
                }`}
              />
            </button>
          </label>
        )}

        <UserMenu />
      </div>
    </header>
  );
}
