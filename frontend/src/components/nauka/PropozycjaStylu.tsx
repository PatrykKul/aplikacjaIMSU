"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Lightbulb, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { odpowiedzNaPropozycje } from "@/lib/api";
import { STYL_NAZWA } from "@/lib/labels";
import type { PropozycjaStylu as Propozycja } from "@/lib/types";
import { useAuthStore } from "@/store/useAuthStore";

type Props = {
  propozycja: Propozycja;
  /** Called after the student accepted or declined. */
  onDecyzja?: () => void;
};

/** „Lepiej Ci idzie z materiałami … – przełączyć?" — decyduje uczeń. */
export function PropozycjaStylu({ propozycja, onDecyzja }: Props) {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);

  const decyzja = useMutation({
    mutationFn: (akceptuj: boolean) => odpowiedzNaPropozycje(propozycja.styl, akceptuj),
    onSuccess: (profil, akceptuj) => {
      setUser(profil.uzytkownik);
      queryClient.setQueryData(["profil"], profil);
      queryClient.invalidateQueries({ queryKey: ["sciezka"] });
      if (akceptuj) {
        queryClient.invalidateQueries({ queryKey: ["temat"] });
        toast.success(`Przełączono na styl: ${STYL_NAZWA[propozycja.styl]}.`);
      } else {
        toast.success("Zostajesz przy obecnym stylu.");
      }
      onDecyzja?.();
    },
    onError: (e) => {
      toast.error(e instanceof Error ? e.message : "Nie udało się zapisać decyzji.");
      queryClient.invalidateQueries({ queryKey: ["sciezka"] });
      onDecyzja?.();
    },
  });

  return (
    <div
      className="rounded-2xl border border-amber-400/60 bg-amber-50 p-5 dark:bg-amber-950/20"
      data-testid="propozycja-stylu"
    >
      <div className="flex items-start gap-3">
        <Lightbulb className="mt-0.5 h-5 w-5 shrink-0 text-amber-500" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-slate-900 dark:text-white">{propozycja.komunikat}</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Dlaczego to widzisz: {propozycja.dlaczego}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={decyzja.isPending}
              onClick={() => decyzja.mutate(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-400 disabled:opacity-60"
            >
              {decyzja.isPending && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
              Tak, przełącz na styl: {STYL_NAZWA[propozycja.styl]}
            </button>
            <button
              type="button"
              disabled={decyzja.isPending}
              onClick={() => decyzja.mutate(false)}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 transition hover:border-slate-400 disabled:opacity-60 dark:border-white/10 dark:text-slate-200"
            >
              Nie, zostaję przy swoim
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
