"use client";

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, RotateCcw, UserRound } from "lucide-react";
import { toast } from "sonner";
import { WynikVak } from "@/components/ankieta/WynikVak";
import { getHistoriaAnkiety, getProfil, przywrocStylZAnkiety, ustawStylRecznie } from "@/lib/api";
import { ROLA_LABEL, STYLE, STYL_KOLOR, STYL_NAZWA, STYL_OPIS, nazwaStylu } from "@/lib/labels";
import type { Profil, Styl } from "@/lib/types";
import { useAuthStore } from "@/store/useAuthStore";

const CARD =
  "rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-sm md:p-8 dark:border-white/10 dark:bg-slate-900/80";

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("pl-PL", { dateStyle: "medium", timeStyle: "short" });
}

export default function ProfilPage() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);

  const { data: profil, isLoading } = useQuery({ queryKey: ["profil"], queryFn: getProfil });
  const { data: historia = [] } = useQuery({
    queryKey: ["ankieta-historia"],
    queryFn: getHistoriaAnkiety,
  });

  const onZmiana = (nowy: Profil, komunikat: string) => {
    setUser(nowy.uzytkownik);
    queryClient.setQueryData(["profil"], nowy);
    // Visible blocks depend on the style — refetch materials
    queryClient.invalidateQueries({ queryKey: ["temat"] });
    toast.success(komunikat);
  };
  const onError = (e: unknown) => toast.error(e instanceof Error ? e.message : "Nie udało się zapisać.");

  const ustaw = useMutation({
    mutationFn: (styl: Styl) => ustawStylRecznie(styl),
    onSuccess: (p) => onZmiana(p, "Zmieniono styl uczenia."),
    onError,
  });
  const przywroc = useMutation({
    mutationFn: przywrocStylZAnkiety,
    onSuccess: (p) => onZmiana(p, "Przywrócono styl z ankiety."),
    onError,
  });

  if (isLoading || !profil) {
    return (
      <div className="flex flex-1 items-center justify-center p-16">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Ładowanie profilu" />
      </div>
    );
  }

  const { uzytkownik, wynik_ankiety: wynik } = profil;
  const reczny = uzytkownik.styl_zrodlo === "reczny";
  const busy = ustaw.isPending || przywroc.isPending;

  return (
    <main className="flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-3xl space-y-6">
        <section className={CARD}>
          <div className="flex items-center gap-4">
            <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/15 ring-1 ring-primary/25">
              <UserRound className="h-7 w-7 text-primary" aria-hidden />
            </span>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{uzytkownik.imie}</h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                {uzytkownik.email} · {ROLA_LABEL[uzytkownik.rola]}
              </p>
            </div>
          </div>
        </section>

        <section className={CARD}>
          <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-white">Mój styl uczenia</h2>
          {wynik ? (
            <>
              <p className="mb-5 text-sm text-slate-700 dark:text-slate-300" data-testid="styl-podsumowanie">
                Wynik ankiety: <strong>{nazwaStylu(wynik.styl_dominujacy)}</strong>
                {reczny && (
                  <>
                    {" · "}wybrany ręcznie: <strong>{nazwaStylu(uzytkownik.styl_uczenia)}</strong>
                  </>
                )}
              </p>

              <div className="grid gap-3 sm:grid-cols-3">
                {STYLE.map((s) => {
                  const aktywny = uzytkownik.styl_uczenia === s;
                  return (
                    <button
                      key={s}
                      type="button"
                      disabled={busy}
                      aria-pressed={aktywny}
                      onClick={() => ustaw.mutate(s)}
                      className={`rounded-2xl border p-4 text-left transition disabled:opacity-60 ${
                        aktywny
                          ? STYL_KOLOR[s].chip
                          : "border-slate-200 bg-white hover:border-primary/40 dark:border-white/10 dark:bg-slate-950/40"
                      }`}
                    >
                      <span className={`block text-sm font-bold capitalize ${STYL_KOLOR[s].text}`}>
                        {s} · {STYL_NAZWA[s]}
                      </span>
                      <span className="mt-1 block text-xs text-slate-600 dark:text-slate-400">
                        {STYL_OPIS[s]}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="mt-3 text-xs text-slate-500">
                Ręczna zmiana nie kasuje wyniku ankiety — w każdej chwili możesz do niego wrócić.
              </p>

              <div className="mt-5 flex flex-wrap gap-3">
                {reczny && (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => przywroc.mutate()}
                    className="inline-flex items-center gap-2 rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-primary/40 disabled:opacity-60 dark:border-white/10 dark:text-slate-200"
                  >
                    <RotateCcw className="h-4 w-4" aria-hidden />
                    Wróć do wyniku ankiety
                  </button>
                )}
                <Link
                  href="/ankieta"
                  className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-primary/40 dark:border-white/10 dark:text-slate-200"
                >
                  Wypełnij ankietę ponownie
                </Link>
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Nie masz jeszcze wyniku ankiety.{" "}
              <Link href="/ankieta" className="font-semibold text-primary hover:underline">
                Wypełnij ankietę
              </Link>
              , aby poznać swój styl uczenia.
            </p>
          )}
        </section>

        {wynik && (
          <section className={CARD}>
            <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
              Ostatni wynik ankiety
            </h2>
            <WynikVak
              punkty={{ V: wynik.punkty_v, A: wynik.punkty_a, K: wynik.punkty_k }}
              dominujacy={wynik.styl_dominujacy}
            />
          </section>
        )}

        {historia.length > 1 && (
          <section className={CARD}>
            <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">Historia ankiet</h2>
            <ul className="divide-y divide-slate-200 text-sm dark:divide-white/10">
              {historia.map((w) => (
                <li key={w.id} className="flex flex-wrap items-center justify-between gap-2 py-2.5">
                  <span className="text-slate-600 dark:text-slate-400">{formatDate(w.data)}</span>
                  <span className="font-medium text-slate-900 dark:text-white">
                    {nazwaStylu(w.styl_dominujacy)}
                  </span>
                  <span className="font-mono text-xs text-slate-500">
                    V {w.punkty_v} / A {w.punkty_a} / K {w.punkty_k}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
