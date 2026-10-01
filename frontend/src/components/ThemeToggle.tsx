"use client";

import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setMounted(true);
  }, []);

  const isDark = mounted ? resolvedTheme === "dark" : false;
  const nextTheme = isDark ? "light" : "dark";
  const label = isDark ? "Przełącz na jasny motyw" : "Przełącz na ciemny motyw";

  return (
    <button
      type="button"
      onClick={() => setTheme(nextTheme)}
      className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-300/70 bg-white/90 text-slate-700 transition hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/70 dark:border-white/[0.08] dark:bg-white/[0.03] dark:text-slate-200 dark:hover:bg-white/[0.08]"
      aria-label={label}
      title={label}
      suppressHydrationWarning
    >
      {isDark ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
    </button>
  );
}
