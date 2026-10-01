"use client";

import Link from "next/link";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { getPytaniaDoEdycji, usunPytanie, zapiszPytanie } from "@/lib/api";
import { STYLE, STYL_KOLOR, STYL_NAZWA } from "@/lib/labels";
import type { PytanieAnkietyEdycja, PytanieAnkietyPayload, Styl } from "@/lib/types";
import { BTN_PRIMARY, BTN_SECONDARY, CARD, INPUT } from "@/lib/ui";

type Draft = { id: number | null; tresc: string; aktywne: boolean; odpowiedzi: Record<Styl, string> };

const PUSTY: Draft = { id: null, tresc: "", aktywne: true, odpowiedzi: { V: "", A: "", K: "" } };

function doDraftu(p: PytanieAnkietyEdycja): Draft {
  const odpowiedzi = { V: "", A: "", K: "" };
  for (const o of p.odpowiedzi) odpowiedzi[o.styl] = o.tresc;
  return { id: p.id, tresc: p.tresc, aktywne: p.aktywne, odpowiedzi };
}

export default function EdycjaAnkietyPage() {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<Draft | null>(null);

  const { data: pytania, isLoading } = useQuery({
    queryKey: ["ankieta-edycja"],
    queryFn: getPytaniaDoEdycji,
    staleTime: 0,
  });

  const odswiez = () => {
    queryClient.invalidateQueries({ queryKey: ["ankieta-edycja"] });
    queryClient.invalidateQueries({ queryKey: ["ankieta-pytania"] });
  };
  const onError = (e: unknown) => toast.error(e instanceof Error ? e.message : "Nie udało się zapisać.");

  const zapisz = useMutation({
    mutationFn: (d: Draft) => {
      const dane: PytanieAnkietyPayload = {
        tresc: d.tresc,
        aktywne: d.aktywne,
        // Exactly one answer per style
        odpowiedzi: STYLE.map((s) => ({ styl: s, tresc: d.odpowiedzi[s] })),
      };
      return zapiszPytanie(d.id, dane);
    },
    onSuccess: () => {
      toast.success("Pytanie zapisane.");
      setDraft(null);
      odswiez();
    },
    onError,
  });

  const usun = useMutation({
    mutationFn: (id: number) => usunPytanie(id),
    onSuccess: () => {
      toast.success("Pytanie usunięte.");
      odswiez();
    },
    onError,
  });

  const kompletny =
    !!draft && draft.tresc.trim() !== "" && STYLE.every((s) => draft.odpowiedzi[s].trim() !== "");
  const aktywne = pytania?.filter((p) => p.aktywne).length ?? 0;

  return (
    <main className="flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-4xl space-y-6">
        <Link
          href="/nauczyciel"
          className="inline-flex items-center gap-1 text-sm text-slate-600 transition hover:text-primary dark:text-slate-400"
        >
          <ArrowLeft className="h-4 w-4" aria-hidden />
          Panel nauczyciela
        </Link>
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Ankieta VAK</h1>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
              Każde pytanie ma po jednej odpowiedzi dla wzrokowca, słuchowca i kinestetyka. Aktywnych pytań:{" "}
              {aktywne}.
            </p>
          </div>
          {!draft && (
            <button type="button" className={BTN_PRIMARY} onClick={() => setDraft(PUSTY)}>
              <Plus className="h-4 w-4" aria-hidden />
              Dodaj pytanie
            </button>
          )}
        </header>

        {draft && (
          <form
            className={CARD}
            onSubmit={(e) => {
              e.preventDefault();
              if (kompletny) zapisz.mutate(draft);
            }}
          >
            <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
              {draft.id === null ? "Nowe pytanie" : "Edycja pytania"}
            </h2>
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Treść pytania
              <input
                className={`${INPUT} mt-1`}
                value={draft.tresc}
                maxLength={500}
                onChange={(e) => setDraft({ ...draft, tresc: e.target.value })}
              />
            </label>
            <div className="mt-4 space-y-3">
              {STYLE.map((s) => (
                <label key={s} className="block text-sm font-medium text-slate-700 dark:text-slate-300">
                  <span className={STYL_KOLOR[s].text}>
                    Odpowiedź {s} · {STYL_NAZWA[s]}
                  </span>
                  <input
                    className={`${INPUT} mt-1`}
                    value={draft.odpowiedzi[s]}
                    maxLength={500}
                    onChange={(e) =>
                      setDraft({ ...draft, odpowiedzi: { ...draft.odpowiedzi, [s]: e.target.value } })
                    }
                  />
                </label>
              ))}
            </div>
            <label className="mt-4 flex items-center gap-2 text-sm text-slate-700 dark:text-slate-300">
              <input
                type="checkbox"
                checked={draft.aktywne}
                onChange={(e) => setDraft({ ...draft, aktywne: e.target.checked })}
                className="h-4 w-4 accent-sky-500"
              />
              Pytanie aktywne (pokazywane w ankiecie)
            </label>
            <div className="mt-6 flex gap-3">
              <button type="submit" className={BTN_PRIMARY} disabled={!kompletny || zapisz.isPending}>
                {zapisz.isPending && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
                Zapisz pytanie
              </button>
              <button type="button" className={BTN_SECONDARY} onClick={() => setDraft(null)}>
                Anuluj
              </button>
            </div>
          </form>
        )}

        {isLoading ? (
          <div className="flex justify-center p-10">
            <Loader2 className="h-8 w-8 animate-spin text-primary" aria-label="Ładowanie pytań" />
          </div>
        ) : !pytania || pytania.length === 0 ? (
          <p className={`${CARD} text-sm text-slate-500`}>Ankieta nie ma jeszcze pytań.</p>
        ) : (
          <ol className="space-y-3">
            {pytania.map((p, i) => (
              <li key={p.id} className={`${CARD} !p-5 ${p.aktywne ? "" : "opacity-60"}`}>
                <div className="flex items-start gap-3">
                  <span className="mt-0.5 text-sm font-bold text-slate-500">{i + 1}.</span>
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-slate-900 dark:text-white">
                      {p.tresc}
                      {!p.aktywne && (
                        <span className="ml-2 rounded-full border border-slate-400/50 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider text-slate-500">
                          wyłączone
                        </span>
                      )}
                    </p>
                    <ul className="mt-2 space-y-1 text-sm text-slate-700 dark:text-slate-300">
                      {STYLE.map((s) => (
                        <li key={s} className="flex gap-2">
                          <span className={`w-5 shrink-0 font-bold ${STYL_KOLOR[s].text}`}>{s}</span>
                          <span>{p.odpowiedzi.find((o) => o.styl === s)?.tresc}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  <button
                    type="button"
                    title="Edytuj pytanie"
                    onClick={() => {
                      setDraft(doDraftu(p));
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-200 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-white"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    title="Usuń pytanie"
                    disabled={usun.isPending}
                    onClick={() => {
                      if (window.confirm("Usunąć to pytanie z ankiety?")) usun.mutate(p.id);
                    }}
                    className="rounded-lg p-2 text-slate-500 transition hover:bg-rose-500/15 hover:text-rose-500"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </li>
            ))}
          </ol>
        )}
      </div>
    </main>
  );
}
