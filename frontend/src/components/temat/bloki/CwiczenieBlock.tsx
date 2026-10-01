"use client";

import { useState } from "react";
import { Check, Lightbulb, RotateCcw } from "lucide-react";
import { MathMarkdown } from "@/components/MathMarkdown";
import type { CwiczenieDane } from "@/lib/types";

type Props = {
  dane: CwiczenieDane;
  variant: "dark" | "light";
  /** Called once when the last step is marked as done. */
  onComplete?: () => void;
};

/** Zadanie „zrób sam": kroki odsłaniane po kolei, każdy z opcjonalną podpowiedzią. */
export function CwiczenieBlock({ dane, variant, onComplete }: Props) {
  const kroki = dane.kroki;
  const [zrobione, setZrobione] = useState(0);
  const [podpowiedz, setPodpowiedz] = useState(false);
  const koniec = zrobione >= kroki.length;

  const dalej = () => {
    const nastepny = zrobione + 1;
    setZrobione(nastepny);
    setPodpowiedz(false);
    if (nastepny === kroki.length) onComplete?.();
  };

  return (
    <div>
      <div className="mb-3 flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-400">
        <span>
          Krok {Math.min(zrobione + 1, kroki.length)} z {kroki.length}
        </span>
        {zrobione > 0 && (
          <button
            type="button"
            onClick={() => {
              setZrobione(0);
              setPodpowiedz(false);
            }}
            className="inline-flex items-center gap-1 hover:text-slate-900 dark:hover:text-white"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden />
            Od nowa
          </button>
        )}
      </div>
      <div className="mb-4 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all"
          style={{ width: `${(zrobione / kroki.length) * 100}%` }}
        />
      </div>

      <ol className="space-y-2">
        {kroki.slice(0, Math.min(zrobione + 1, kroki.length)).map((krok, i) => {
          const gotowy = i < zrobione;
          return (
            <li
              key={i}
              className={`rounded-xl border px-4 py-3 text-sm ${
                gotowy
                  ? "border-emerald-300/60 bg-emerald-50/70 text-slate-600 dark:border-emerald-500/30 dark:bg-emerald-950/20 dark:text-slate-400"
                  : "border-emerald-400 bg-white text-slate-900 dark:border-emerald-400/60 dark:bg-slate-950/50 dark:text-slate-100"
              }`}
            >
              <div className="flex items-start gap-3">
                <span
                  className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
                    gotowy ? "bg-emerald-500 text-white" : "border border-emerald-500 text-emerald-600"
                  }`}
                >
                  {gotowy ? <Check className="h-3 w-3" aria-label="zrobione" /> : i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <MathMarkdown variant={variant}>{krok.polecenie}</MathMarkdown>
                  {!gotowy && (
                    <div className="mt-3 flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        onClick={dalej}
                        className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-emerald-500"
                      >
                        <Check className="h-3.5 w-3.5" aria-hidden />
                        Zrobione
                      </button>
                      {krok.podpowiedz && (
                        <button
                          type="button"
                          onClick={() => setPodpowiedz((p) => !p)}
                          aria-expanded={podpowiedz}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-amber-400/60 px-3 py-1.5 text-xs font-semibold text-amber-700 transition hover:bg-amber-500/10 dark:text-amber-200"
                        >
                          <Lightbulb className="h-3.5 w-3.5" aria-hidden />
                          {podpowiedz ? "Ukryj podpowiedź" : "Podpowiedź"}
                        </button>
                      )}
                    </div>
                  )}
                  {!gotowy && podpowiedz && krok.podpowiedz && (
                    <p className="mt-2 rounded-lg bg-amber-100/70 px-3 py-2 text-xs text-amber-900 dark:bg-amber-950/30 dark:text-amber-100">
                      {krok.podpowiedz}
                    </p>
                  )}
                </div>
              </div>
            </li>
          );
        })}
      </ol>

      {koniec && (
        <p className="mt-4 rounded-xl border border-emerald-400/60 bg-emerald-500/10 px-4 py-3 text-sm font-semibold text-emerald-700 dark:text-emerald-200">
          Ćwiczenie ukończone — dobra robota!
        </p>
      )}
    </div>
  );
}
