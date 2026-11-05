"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { BookOpen, ClipboardList, Loader2, Users } from "lucide-react";
import { getUczniowie } from "@/lib/api";
import { STYL_KOLOR, ZRODLO_STYLU_LABEL, nazwaStylu, styleZ } from "@/lib/labels";
import type { Uczen } from "@/lib/types";
import { BTN_PRIMARY, CARD, TD, TH, formatDate } from "@/lib/ui";

function StylChip({ styl }: { styl: string | null }) {
  const lista = styleZ(styl);
  if (lista.length === 0) return <span className="text-slate-400">—</span>;
  const klasy = lista.length === 1 ? STYL_KOLOR[lista[0]].chip : "border-slate-400/50 bg-slate-500/10";
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-semibold ${klasy}`}>
      {nazwaStylu(styl)}
    </span>
  );
}

function AktualnyStyl({ u }: { u: Uczen }) {
  if (!u.ankieta_wypelniona) return <span className="text-slate-400">—</span>;
  return (
    <span className="flex flex-col items-start gap-0.5">
      <StylChip styl={u.styl_uczenia} />
      {u.styl_zrodlo && u.styl_zrodlo !== "ankieta" ? (
        <span className="text-xs text-slate-500">{ZRODLO_STYLU_LABEL[u.styl_zrodlo]}</span>
      ) : null}
    </span>
  );
}

export default function PanelNauczycielaPage() {
  const { data: uczniowie, isLoading, isError, refetch } = useQuery({
    queryKey: ["uczniowie"],
    queryFn: getUczniowie,
    staleTime: 0,
  });

  return (
    <main className="flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-6xl space-y-6">
        <header>
          <h1 className="bg-gradient-to-r from-primary via-cyan-300 to-secondary bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl">
            Panel nauczyciela
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-400">
            Kursy, ankieta stylu uczenia i postępy uczniów.
          </p>
        </header>

        <div className="grid gap-4 sm:grid-cols-2">
          <Link href="/kursy" className={`${CARD} transition hover:border-primary/40`}>
            <BookOpen className="mb-3 h-6 w-6 text-primary" aria-hidden />
            <h2 className="font-semibold text-slate-900 dark:text-white">Kursy i materiały</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Włącz „Tryb Edycji”, aby dodawać bloki dla stylów V / A / K i podglądać temat oczami ucznia.
            </p>
          </Link>
          <Link href="/nauczyciel/ankieta" className={`${CARD} transition hover:border-primary/40`}>
            <ClipboardList className="mb-3 h-6 w-6 text-primary" aria-hidden />
            <h2 className="font-semibold text-slate-900 dark:text-white">Ankieta VAK</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Pytania ankiety stylu uczenia: dodawanie, edycja, wyłączanie.
            </p>
          </Link>
        </div>

        <section className={CARD}>
          <h2 className="mb-4 flex items-center gap-2 text-lg font-semibold text-slate-900 dark:text-white">
            <Users className="h-5 w-5 text-primary" aria-hidden />
            Uczniowie
          </h2>
          {isLoading ? (
            <div className="flex justify-center p-10">
              <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Ładowanie uczniów" />
            </div>
          ) : isError || !uczniowie ? (
            <div className="flex flex-col items-center gap-3 p-6 text-center">
              <p className="text-slate-600 dark:text-slate-400">Nie udało się wczytać listy uczniów.</p>
              <button type="button" onClick={() => refetch()} className={BTN_PRIMARY}>
                Spróbuj ponownie
              </button>
            </div>
          ) : uczniowie.length === 0 ? (
            <p className="text-sm text-slate-500">Nie ma jeszcze żadnych uczniów.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[720px] border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-white/10">
                    <th className={TH}>Uczeń</th>
                    <th className={TH}>Wynik ankiety</th>
                    <th className={TH}>Aktualny styl</th>
                    <th className={TH}>Wagi V / A / K</th>
                    <th className={TH}>Zaliczone tematy</th>
                    <th className={TH}>Ostatnia aktywność</th>
                  </tr>
                </thead>
                <tbody>
                  {uczniowie.map((u) => (
                    <tr key={u.id} className="border-b border-slate-100 last:border-0 dark:border-white/5">
                      <td className={TD}>
                        <Link
                          href={`/nauczyciel/uczniowie/${u.id}`}
                          className="font-semibold text-slate-900 hover:text-primary dark:text-white"
                        >
                          {u.imie}
                        </Link>
                        <span className="block text-xs text-slate-500">{u.email}</span>
                      </td>
                      <td className={TD}>
                        {u.ankieta_wypelniona ? (
                          <span className="flex flex-col items-start gap-0.5">
                            <StylChip styl={u.styl_ankiety} />
                            {u.punkty_ankiety && (
                              <span className="font-mono text-xs text-slate-500">
                                V {u.punkty_ankiety.V} / A {u.punkty_ankiety.A} / K {u.punkty_ankiety.K}
                              </span>
                            )}
                          </span>
                        ) : (
                          <span className="text-xs font-medium text-amber-600 dark:text-amber-300">
                            ankieta niewypełniona
                          </span>
                        )}
                      </td>
                      <td className={TD}>
                        <AktualnyStyl u={u} />
                      </td>
                      <td className={`${TD} whitespace-nowrap font-mono`}>
                        {u.ankieta_wypelniona ? `${u.wagi.V} / ${u.wagi.A} / ${u.wagi.K}` : "—"}
                      </td>
                      <td className={TD}>
                        {u.zaliczone_tematy}
                        <span className="text-xs text-slate-500"> · prób: {u.liczba_prob}</span>
                      </td>
                      <td className={TD}>{formatDate(u.ostatnia_aktywnosc)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
