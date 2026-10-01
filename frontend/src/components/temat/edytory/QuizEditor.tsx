"use client";

import { Plus, Trash2 } from "lucide-react";
import type { QuizDane } from "@/lib/types";

type Props = { value: QuizDane; onChange: (v: QuizDane) => void };

const INPUT =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-white/10 dark:bg-slate-950 dark:text-slate-100";

export const DEFAULT_QUIZ: QuizDane = {
  pytania: [{ tresc: "Treść pytania", odpowiedzi: ["Odpowiedź A", "Odpowiedź B"], poprawna: 0 }],
};

/** Edytor quizu: pytania, odpowiedzi i zaznaczenie poprawnej. */
export function QuizEditor({ value, onChange }: Props) {
  const setPytanie = (i: number, patch: Partial<QuizDane["pytania"][number]>) =>
    onChange({ pytania: value.pytania.map((p, k) => (k === i ? { ...p, ...patch } : p)) });

  return (
    <div className="mt-3 space-y-4">
      {value.pytania.map((p, i) => {
        const poprawna = p.poprawna ?? 0;
        return (
        <div key={i} className="rounded-xl border border-slate-200 p-3 dark:border-white/10">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-xs font-bold text-slate-500">{i + 1}.</span>
            <input
              className={INPUT}
              value={p.tresc}
              onChange={(e) => setPytanie(i, { tresc: e.target.value })}
              placeholder="Treść pytania"
              aria-label={`Treść pytania ${i + 1}`}
            />
            <button
              type="button"
              title="Usuń pytanie"
              disabled={value.pytania.length <= 1}
              onClick={() => onChange({ pytania: value.pytania.filter((_, k) => k !== i) })}
              className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-500/15 hover:text-rose-500 disabled:opacity-30"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </div>
          <div className="space-y-1.5 pl-5">
            {p.odpowiedzi.map((o, j) => (
              <div key={j} className="flex items-center gap-2">
                <input
                  type="radio"
                  name={`quiz-edytor-${i}`}
                  checked={poprawna === j}
                  onChange={() => setPytanie(i, { poprawna: j })}
                  title="Poprawna odpowiedź"
                  aria-label={`Odpowiedź ${j + 1} jest poprawna`}
                  className="h-4 w-4 accent-emerald-500"
                />
                <input
                  className={INPUT}
                  value={o}
                  onChange={(e) =>
                    setPytanie(i, { odpowiedzi: p.odpowiedzi.map((x, k) => (k === j ? e.target.value : x)) })
                  }
                  placeholder={`Odpowiedź ${j + 1}`}
                  aria-label={`Odpowiedź ${j + 1} do pytania ${i + 1}`}
                />
                <button
                  type="button"
                  title="Usuń odpowiedź"
                  disabled={p.odpowiedzi.length <= 2}
                  onClick={() =>
                    setPytanie(i, {
                      odpowiedzi: p.odpowiedzi.filter((_, k) => k !== j),
                      poprawna: poprawna === j ? 0 : poprawna > j ? poprawna - 1 : poprawna,
                    })
                  }
                  className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-500/15 hover:text-rose-500 disabled:opacity-30"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
            {p.odpowiedzi.length < 6 && (
              <button
                type="button"
                onClick={() => setPytanie(i, { odpowiedzi: [...p.odpowiedzi, ""] })}
                className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                <Plus className="h-3.5 w-3.5" />
                Dodaj odpowiedź
              </button>
            )}
          </div>
        </div>
        );
      })}
      <button
        type="button"
        onClick={() => onChange({ pytania: [...value.pytania, { tresc: "", odpowiedzi: ["", ""], poprawna: 0 }] })}
        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-primary/40 dark:border-white/10 dark:text-slate-200"
      >
        <Plus className="h-3.5 w-3.5" />
        Dodaj pytanie
      </button>
      <p className="text-xs text-slate-500">Zaznacz kółko przy poprawnej odpowiedzi.</p>
    </div>
  );
}
