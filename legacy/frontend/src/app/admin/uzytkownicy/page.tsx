"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { getUzytkownicy, zmienAktywnosc, zmienRole } from "@/lib/api";
import { ROLA_LABEL, nazwaStylu } from "@/lib/labels";
import type { Rola, Uzytkownik } from "@/lib/types";
import { BTN_PRIMARY, BTN_SECONDARY, CARD, TD, TH, formatDate } from "@/lib/ui";
import { useAuthStore } from "@/store/useAuthStore";

const ROLE: Rola[] = ["uczen", "nauczyciel", "admin"];

export default function AdminUzytkownicyPage() {
  const queryClient = useQueryClient();
  const ja = useAuthStore((s) => s.user);

  const { data: uzytkownicy, isLoading, isError, refetch } = useQuery({
    queryKey: ["uzytkownicy"],
    queryFn: getUzytkownicy,
    staleTime: 0,
  });

  const podmien = (u: Uzytkownik) =>
    queryClient.setQueryData<Uzytkownik[]>(["uzytkownicy"], (lista) =>
      lista?.map((x) => (x.id === u.id ? u : x))
    );
  const onError = (e: unknown) => toast.error(e instanceof Error ? e.message : "Nie udało się zapisać.");

  const rola = useMutation({
    mutationFn: ({ id, rola }: { id: number; rola: Rola }) => zmienRole(id, rola),
    onSuccess: (u) => {
      podmien(u);
      toast.success(`${u.imie}: rola zmieniona na „${ROLA_LABEL[u.rola]}”.`);
    },
    onError,
  });

  const aktywnosc = useMutation({
    mutationFn: ({ id, aktywny }: { id: number; aktywny: boolean }) => zmienAktywnosc(id, aktywny),
    onSuccess: (u) => {
      podmien(u);
      toast.success(u.aktywny ? `${u.imie}: konto odblokowane.` : `${u.imie}: konto zablokowane.`);
    },
    onError,
  });

  const busy = rola.isPending || aktywnosc.isPending;

  return (
    <main className="flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="bg-gradient-to-r from-primary via-cyan-300 to-secondary bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl">
            Panel administratora
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-400">Użytkownicy, role i blokowanie kont.</p>
        </header>

        <section className={CARD}>
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-white">
            <ShieldCheck className="h-5 w-5 text-primary" aria-hidden />
            Użytkownicy{uzytkownicy ? ` (${uzytkownicy.length})` : ""}
          </h2>
          {isLoading ? (
            <div className="flex justify-center p-10">
              <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Ładowanie użytkowników" />
            </div>
          ) : isError || !uzytkownicy ? (
            <div className="flex flex-col items-center gap-3 p-6 text-center">
              <p className="text-slate-600 dark:text-slate-400">Nie udało się wczytać użytkowników.</p>
              <button type="button" onClick={() => refetch()} className={BTN_PRIMARY}>
                Spróbuj ponownie
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-white/10">
                    <th className={TH}>Użytkownik</th>
                    <th className={TH}>Rola</th>
                    <th className={TH}>Styl uczenia</th>
                    <th className={TH}>Konto od</th>
                    <th className={TH}>Status</th>
                    <th className={TH}>
                      <span className="sr-only">Akcje</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {uzytkownicy.map((u) => {
                    const toJa = u.id === ja?.id;
                    return (
                      <tr key={u.id} className="border-b border-slate-100 last:border-0 dark:border-white/5">
                        <td className={TD}>
                          <span className="font-semibold text-slate-900 dark:text-white">{u.imie}</span>
                          {toJa && <span className="ml-2 text-xs text-primary">(to Ty)</span>}
                          <span className="block text-xs text-slate-500">{u.email}</span>
                        </td>
                        <td className={TD}>
                          <select
                            value={u.rola}
                            disabled={toJa || busy}
                            aria-label={`Rola użytkownika ${u.imie}`}
                            title={toJa ? "Nie można zmienić własnej roli" : undefined}
                            onChange={(e) => rola.mutate({ id: u.id, rola: e.target.value as Rola })}
                            className="rounded-lg border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-900 disabled:opacity-60 dark:border-white/10 dark:bg-slate-950 dark:text-slate-100"
                          >
                            {ROLE.map((r) => (
                              <option key={r} value={r}>
                                {ROLA_LABEL[r]}
                              </option>
                            ))}
                          </select>
                        </td>
                        <td className={TD}>
                          {u.rola !== "uczen" ? (
                            "—"
                          ) : u.ankieta_wypelniona ? (
                            nazwaStylu(u.styl_uczenia)
                          ) : (
                            <span className="text-xs text-amber-600 dark:text-amber-300">bez ankiety</span>
                          )}
                        </td>
                        <td className={TD}>{formatDate(u.utworzono)}</td>
                        <td className={TD}>
                          <span
                            className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold ${
                              u.aktywny
                                ? "border-emerald-400/50 bg-emerald-500/10 text-emerald-700 dark:text-emerald-200"
                                : "border-rose-400/50 bg-rose-500/10 text-rose-700 dark:text-rose-200"
                            }`}
                          >
                            {u.aktywny ? "aktywne" : "zablokowane"}
                          </span>
                        </td>
                        <td className={`${TD} text-right`}>
                          {!toJa && (
                            <button
                              type="button"
                              disabled={busy}
                              onClick={() => aktywnosc.mutate({ id: u.id, aktywny: !u.aktywny })}
                              className={`${BTN_SECONDARY} !px-3 !py-1.5 text-xs`}
                            >
                              {u.aktywny ? "Zablokuj" : "Odblokuj"}
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
