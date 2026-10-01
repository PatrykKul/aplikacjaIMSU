"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Loader2, Sparkles } from "lucide-react";
import { WynikVak } from "@/components/ankieta/WynikVak";
import { getProfil } from "@/lib/api";
import { STYL_OPIS, nazwaStylu, styleZ } from "@/lib/labels";

export default function WynikAnkietyPage() {
  const { data: profil, isLoading } = useQuery({ queryKey: ["profil"], queryFn: getProfil });

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center p-16">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Ładowanie wyniku" />
      </div>
    );
  }

  const wynik = profil?.wynik_ankiety;
  if (!wynik) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
        <p className="text-slate-600 dark:text-slate-400">Nie masz jeszcze wyniku ankiety.</p>
        <Link href="/ankieta" className="font-semibold text-primary hover:underline">
          Wypełnij ankietę
        </Link>
      </div>
    );
  }

  const style = styleZ(wynik.styl_dominujacy);

  return (
    <main className="flex flex-1 items-start justify-center px-4 py-10 md:py-16">
      <div className="w-full max-w-2xl rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-lg md:p-10 dark:border-white/10 dark:bg-slate-900/80">
        <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-primary">
          <Sparkles className="h-3.5 w-3.5" aria-hidden />
          Twój wynik
        </div>
        <h1 className="mb-2 text-3xl font-bold text-slate-900 dark:text-white">
          {style.length === 1 ? "Jesteś: " : "Twój styl to "}
          <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
            {nazwaStylu(wynik.styl_dominujacy)}
          </span>
        </h1>
        <p className="mb-6 font-mono text-sm text-slate-600 dark:text-slate-400">
          V {wynik.punkty_v} / A {wynik.punkty_a} / K {wynik.punkty_k}
        </p>

        <WynikVak
          punkty={{ V: wynik.punkty_v, A: wynik.punkty_a, K: wynik.punkty_k }}
          dominujacy={wynik.styl_dominujacy}
        />

        <ul className="mt-6 space-y-2 text-sm text-slate-700 dark:text-slate-300">
          {style.map((s) => (
            <li key={s}>{STYL_OPIS[s]}</li>
          ))}
        </ul>
        <p className="mt-4 text-sm text-slate-600 dark:text-slate-400">
          Materiały w kursach będą dobierane do tego stylu. Jeśli wynik do Ciebie nie pasuje, możesz
          zmienić styl w profilu.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/kursy"
            className="rounded-xl bg-gradient-to-r from-primary to-secondary px-5 py-2.5 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95"
          >
            Przejdź do kursów
          </Link>
          <Link
            href="/profil"
            className="rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-primary/40 dark:border-white/10 dark:text-slate-200"
          >
            Mój styl uczenia
          </Link>
        </div>
      </div>
    </main>
  );
}
