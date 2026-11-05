"use client";

import { Plus, Trash2 } from "lucide-react";
import type { CwiczenieDane } from "@/lib/types";

type Props = { value: CwiczenieDane; onChange: (v: CwiczenieDane) => void };

const INPUT =
  "w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-white/10 dark:bg-slate-950 dark:text-slate-100";

export const DEFAULT_CWICZENIE: CwiczenieDane = {
  kroki: [{ polecenie: "Pierwszy krok do wykonania", podpowiedz: null }],
};

/** Edytor ćwiczenia „zrób sam": lista kroków z opcjonalnymi podpowiedziami. */
export function CwiczenieEditor({ value, onChange }: Props) {
  const setKrok = (i: number, patch: Partial<CwiczenieDane["kroki"][number]>) =>
    onChange({ kroki: value.kroki.map((k, j) => (j === i ? { ...k, ...patch } : k)) });

  return (
    <div className="mt-3 space-y-3">
      {value.kroki.map((k, i) => (
        <div key={i} className="flex items-start gap-2 rounded-xl border border-slate-200 p-3 dark:border-white/10">
          <span className="mt-1.5 text-xs font-bold text-slate-500">{i + 1}.</span>
          <div className="min-w-0 flex-1 space-y-1.5">
            <input
              className={INPUT}
              value={k.polecenie}
              onChange={(e) => setKrok(i, { polecenie: e.target.value })}
              placeholder="Polecenie"
              aria-label={`Polecenie kroku ${i + 1}`}
            />
            <input
              className={INPUT}
              value={k.podpowiedz ?? ""}
              onChange={(e) => setKrok(i, { podpowiedz: e.target.value || null })}
              placeholder="Podpowiedź (opcjonalnie)"
              aria-label={`Podpowiedź do kroku ${i + 1}`}
            />
          </div>
          <button
            type="button"
            title="Usuń krok"
            disabled={value.kroki.length <= 1}
            onClick={() => onChange({ kroki: value.kroki.filter((_, j) => j !== i) })}
            className="rounded-lg p-1.5 text-slate-500 hover:bg-rose-500/15 hover:text-rose-500 disabled:opacity-30"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={() => onChange({ kroki: [...value.kroki, { polecenie: "", podpowiedz: null }] })}
        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:border-primary/40 dark:border-white/10 dark:text-slate-200"
      >
        <Plus className="h-3.5 w-3.5" />
        Dodaj krok
      </button>
    </div>
  );
}
