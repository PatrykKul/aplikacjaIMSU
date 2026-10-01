"use client";

import { useState } from "react";
import { CheckCircle2, Loader2, RotateCcw, XCircle } from "lucide-react";
import { toast } from "sonner";
import { MathMarkdown } from "@/components/MathMarkdown";
import { sprawdzQuiz } from "@/lib/api";
import type { QuizDane, QuizWynik, Styl } from "@/lib/types";

type Props = {
  blokId: number;
  dane: QuizDane;
  variant: "dark" | "light";
  /** Style in which the student went through the topic (sent with the answers). */
  styl?: Styl | null;
  onResult?: (wynik: QuizWynik) => void;
};

/** Quiz jednokrotnego wyboru; odpowiedzi ocenia serwer (klucz nie trafia do przeglądarki ucznia). */
export function QuizBlock({ blokId, dane, variant, styl, onResult }: Props) {
  const pytania = dane.pytania;
  const [wybory, setWybory] = useState<(number | null)[]>(() => pytania.map(() => null));
  const [wynik, setWynik] = useState<QuizWynik | null>(null);
  const [busy, setBusy] = useState(false);
  const komplet = wybory.every((w) => w !== null);

  const sprawdz = async () => {
    setBusy(true);
    try {
      const w = await sprawdzQuiz(blokId, wybory, styl);
      setWynik(w);
      onResult?.(w);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Nie udało się sprawdzić quizu.");
    } finally {
      setBusy(false);
    }
  };

  const odNowa = () => {
    setWybory(pytania.map(() => null));
    setWynik(null);
  };

  return (
    <div>
      <ol className="space-y-5">
        {pytania.map((p, i) => (
          <li key={i}>
            <fieldset disabled={!!wynik}>
              <legend className="mb-2 flex items-start gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                <span className="shrink-0">{i + 1}.</span>
                <span className="min-w-0 flex-1">
                  <MathMarkdown variant={variant}>{p.tresc}</MathMarkdown>
                </span>
                {wynik &&
                  (wynik.trafienia[i] ? (
                    <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" aria-label="dobrze" />
                  ) : (
                    <XCircle className="h-5 w-5 shrink-0 text-rose-500" aria-label="źle" />
                  ))}
              </legend>
              <div className="space-y-2">
                {p.odpowiedzi.map((o, j) => {
                  const zaznaczona = wybory[i] === j;
                  const poprawna = wynik?.poprawne_odpowiedzi[i] === j;
                  let klasy =
                    "border-slate-200 bg-white text-slate-700 hover:border-primary/40 dark:border-white/10 dark:bg-slate-950/40 dark:text-slate-200";
                  if (wynik && poprawna) {
                    klasy = "border-emerald-400 bg-emerald-50 text-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-100";
                  } else if (wynik && zaznaczona) {
                    klasy = "border-rose-400 bg-rose-50 text-rose-900 dark:bg-rose-950/30 dark:text-rose-100";
                  } else if (zaznaczona) {
                    klasy = "border-primary bg-primary/10 text-slate-900 dark:text-white";
                  }
                  return (
                    <label
                      key={j}
                      className={`flex cursor-pointer items-center gap-3 rounded-xl border px-3 py-2 text-sm transition ${klasy}`}
                    >
                      <input
                        type="radio"
                        name={`quiz-${blokId}-${i}`}
                        checked={zaznaczona}
                        onChange={() => setWybory((w) => w.map((x, k) => (k === i ? j : x)))}
                        className="h-4 w-4 accent-sky-500"
                      />
                      <span>{o}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
          </li>
        ))}
      </ol>

      {wynik ? (
        <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-slate-950/40">
          <p className="text-sm font-semibold text-slate-900 dark:text-white" data-testid="quiz-wynik">
            Twój wynik: {wynik.poprawne} / {wynik.liczba_pytan} ({wynik.procent}%)
          </p>
          <button
            type="button"
            onClick={odNowa}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-primary/40 dark:border-white/10 dark:text-slate-200"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden />
            Spróbuj ponownie
          </button>
        </div>
      ) : (
        <div className="mt-5 flex items-center gap-3">
          <button
            type="button"
            onClick={sprawdz}
            disabled={!komplet || busy}
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-5 py-2 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95 disabled:opacity-50"
          >
            {busy && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
            Sprawdź odpowiedzi
          </button>
          {!komplet && <span className="text-xs text-slate-500">Odpowiedz na wszystkie pytania.</span>}
        </div>
      )}
    </div>
  );
}
