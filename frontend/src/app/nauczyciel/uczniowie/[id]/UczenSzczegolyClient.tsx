"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Loader2 } from "lucide-react";
import { WynikVak } from "@/components/ankieta/WynikVak";
import { SciezkaView } from "@/components/nauka/SciezkaView";
import { getUczen } from "@/lib/api";
import { POZIOM_NAZWA, ZDARZENIE_LABEL, ZRODLO_STYLU_LABEL, nazwaStylu } from "@/lib/labels";
import type { ZdarzenieNauki } from "@/lib/types";
import { CARD, TD, TH, formatDate } from "@/lib/ui";

function szczegolyZdarzenia(z: ZdarzenieNauki): string {
  if (z.typ === "wynik_quizu") return `${z.wartosc}%`;
  if (z.typ === "czas_w_temacie" && z.czas_s != null) {
    return z.czas_s >= 60 ? `${Math.round(z.czas_s / 60)} min` : `${z.czas_s} s`;
  }
  return "";
}

export function UczenSzczegolyClient({ uczenId }: { uczenId: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["uczen", uczenId],
    queryFn: () => getUczen(uczenId),
    staleTime: 0,
  });

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center p-16">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Ładowanie ucznia" />
      </div>
    );
  }
  if (isError || !data) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
        <p className="text-slate-600 dark:text-slate-400">Nie znaleziono ucznia.</p>
        <Link href="/nauczyciel" className="font-semibold text-primary hover:underline">
          Wróć do listy uczniów
        </Link>
      </div>
    );
  }

  const { uczen, sciezka, historia_ankiet, zdarzenia } = data;

  return (
    <main className="flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <Link
          href="/nauczyciel"
          className="inline-flex items-center gap-1 text-sm text-slate-600 transition hover:text-primary dark:text-slate-400"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Uczniowie
        </Link>

        <header>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{uczen.imie}</h1>
          <p className="text-sm text-slate-600 dark:text-slate-400">{uczen.email}</p>
        </header>

        {!uczen.ankieta_wypelniona ? (
          <section className={CARD}>
            <p className="text-slate-600 dark:text-slate-400">
              Ten uczeń nie wypełnił jeszcze ankiety stylu uczenia, więc nie ma dostępu do materiałów.
            </p>
          </section>
        ) : (
          <>
            <div className="grid gap-6 md:grid-cols-2">
              <section className={CARD}>
                <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-white">Styl uczenia</h2>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500">Wynik ankiety</dt>
                    <dd className="text-right font-medium text-slate-900 dark:text-white">
                      {nazwaStylu(uczen.styl_ankiety)}
                      {uczen.punkty_ankiety && (
                        <span className="block font-mono text-xs font-normal text-slate-500">
                          V {uczen.punkty_ankiety.V} / A {uczen.punkty_ankiety.A} / K {uczen.punkty_ankiety.K}
                        </span>
                      )}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500">Aktualny styl</dt>
                    <dd className="text-right font-medium text-slate-900 dark:text-white">
                      {nazwaStylu(uczen.styl_uczenia)}
                      {uczen.styl_zrodlo && (
                        <span className="block text-xs font-normal text-slate-500">
                          {ZRODLO_STYLU_LABEL[uczen.styl_zrodlo] ?? uczen.styl_zrodlo}
                        </span>
                      )}
                    </dd>
                  </div>
                  <div className="flex justify-between gap-4">
                    <dt className="text-slate-500">Poziom materiałów</dt>
                    <dd className="text-right font-medium text-slate-900 dark:text-white">
                      {POZIOM_NAZWA[sciezka.poziom]}
                    </dd>
                  </div>
                </dl>
                {sciezka.propozycja_stylu && (
                  <p className="mt-4 rounded-xl bg-amber-100/70 px-3 py-2 text-xs text-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
                    System zaproponował uczniowi zmianę stylu na: {nazwaStylu(sciezka.propozycja_stylu.styl)} (
                    {sciezka.propozycja_stylu.dlaczego})
                  </p>
                )}
              </section>
              <section className={CARD}>
                <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-white">
                  Wagi stylów po quizach
                </h2>
                <WynikVak punkty={sciezka.wagi} dominujacy={uczen.styl_uczenia} />
              </section>
            </div>

            <section className={CARD}>
              <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-white">Ścieżka ucznia</h2>
              {sciezka.nastepny_krok && (
                <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
                  Następny krok: <strong>{sciezka.nastepny_krok.tytul}</strong> — {sciezka.nastepny_krok.dlaczego}
                </p>
              )}
              <SciezkaView kursy={sciezka.kursy} nastepnyTematId={sciezka.nastepny_krok?.temat_id} linki={false} />
            </section>

            {historia_ankiet.length > 0 && (
              <section className={CARD}>
                <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-white">Historia ankiet</h2>
                <ul className="divide-y divide-slate-200 text-sm dark:divide-white/10">
                  {historia_ankiet.map((w) => (
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

            <section className={CARD}>
              <h2 className="mb-3 text-lg font-semibold text-slate-900 dark:text-white">Ostatnia aktywność</h2>
              {zdarzenia.length === 0 ? (
                <p className="text-sm text-slate-500">Brak zdarzeń nauki.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[560px] border-collapse">
                    <thead>
                      <tr className="border-b border-slate-200 dark:border-white/10">
                        <th className={TH}>Kiedy</th>
                        <th className={TH}>Zdarzenie</th>
                        <th className={TH}>Temat</th>
                        <th className={TH}>Styl</th>
                        <th className={TH}>Szczegóły</th>
                      </tr>
                    </thead>
                    <tbody>
                      {zdarzenia.map((z, i) => (
                        <tr key={i} className="border-b border-slate-100 last:border-0 dark:border-white/5">
                          <td className={TD}>{formatDate(z.data)}</td>
                          <td className={TD}>{ZDARZENIE_LABEL[z.typ] ?? z.typ}</td>
                          <td className={TD}>{z.temat}</td>
                          <td className={TD}>{z.styl ?? "—"}</td>
                          <td className={`${TD} font-mono`}>{szczegolyZdarzenia(z)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
