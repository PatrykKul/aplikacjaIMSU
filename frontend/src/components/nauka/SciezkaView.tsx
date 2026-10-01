import Link from "next/link";
import { CheckCircle2, Circle, CircleDot } from "lucide-react";
import type { SciezkaKurs } from "@/lib/types";

type Props = {
  kursy: SciezkaKurs[];
  /** Topic the student should take next (highlighted). */
  nastepnyTematId?: number | null;
  /** Student view links to the topics; the teacher's read-only view does not. */
  linki?: boolean;
};

/** Ścieżka nauki: kursy z paskiem postępu i listą tematów ze statusem. */
export function SciezkaView({ kursy, nastepnyTematId, linki = true }: Props) {
  if (kursy.length === 0) {
    return <p className="text-sm text-slate-500">Brak opublikowanych kursów.</p>;
  }

  return (
    <div className="space-y-6">
      {kursy.map((kurs) => {
        const procent = Math.round((kurs.zaliczone / Math.max(1, kurs.tematy.length)) * 100);
        return (
          <section key={kurs.id}>
            <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
              <h3 className="font-semibold text-slate-900 dark:text-white">{kurs.nazwa}</h3>
              <span className="text-sm text-slate-600 dark:text-slate-400">
                {kurs.zaliczone} / {kurs.tematy.length} tematów ({procent}%)
              </span>
            </div>
            <div
              className="mb-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
              role="progressbar"
              aria-valuemin={0}
              aria-valuemax={kurs.tematy.length}
              aria-valuenow={kurs.zaliczone}
              aria-label={`Postęp w kursie ${kurs.nazwa}`}
            >
              <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${procent}%` }} />
            </div>
            <ol className="divide-y divide-slate-200 rounded-2xl border border-slate-200 dark:divide-white/10 dark:border-white/10">
              {kurs.tematy.map((t) => {
                const nastepny = t.id === nastepnyTematId;
                const status = t.zaliczony ? (
                  <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" aria-label="zaliczony" />
                ) : nastepny ? (
                  <CircleDot className="h-5 w-5 shrink-0 text-primary" aria-label="następny" />
                ) : (
                  <Circle className="h-5 w-5 shrink-0 text-slate-400" aria-label="niezaliczony" />
                );
                const tresc = (
                  <>
                    {status}
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium text-slate-900 dark:text-white">
                        {t.tytul}
                      </span>
                      <span className="block text-xs text-slate-500">{t.dzial}</span>
                    </span>
                    <span className="shrink-0 text-right text-xs text-slate-600 dark:text-slate-400">
                      {t.liczba_prob > 0 ? (
                        <>
                          najlepszy wynik: <strong>{t.najlepszy_wynik}%</strong>
                          <span className="block text-slate-500">prób: {t.liczba_prob}</span>
                        </>
                      ) : t.zaliczony ? (
                        "ukończony"
                      ) : nastepny ? (
                        <span className="font-semibold text-primary">następny</span>
                      ) : (
                        "nie zaczęty"
                      )}
                    </span>
                  </>
                );
                const klasy = `flex items-center gap-3 px-4 py-3 ${nastepny ? "bg-primary/5" : ""}`;
                return (
                  <li key={t.id}>
                    {linki ? (
                      <Link
                        href={`/tematy/${t.id}`}
                        className={`${klasy} transition hover:bg-slate-100 dark:hover:bg-white/5`}
                      >
                        {tresc}
                      </Link>
                    ) : (
                      <div className={klasy}>{tresc}</div>
                    )}
                  </li>
                );
              })}
            </ol>
          </section>
        );
      })}
    </div>
  );
}
