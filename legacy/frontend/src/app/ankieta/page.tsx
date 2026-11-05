"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, ClipboardList, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { getPytaniaAnkiety, wyslijAnkiete } from "@/lib/api";
import { useAuthStore } from "@/store/useAuthStore";

export default function AnkietaPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [index, setIndex] = useState(0);
  // pytanie_id -> odpowiedz_id
  const [wybory, setWybory] = useState<Record<number, number>>({});

  const { data: pytania, isLoading, isError, refetch } = useQuery({
    queryKey: ["ankieta-pytania"],
    queryFn: getPytaniaAnkiety,
  });

  const wyslij = useMutation({
    mutationFn: () =>
      wyslijAnkiete(
        Object.entries(wybory).map(([pytanieId, odpowiedzId]) => ({
          pytanie_id: Number(pytanieId),
          odpowiedz_id: odpowiedzId,
        }))
      ),
    onSuccess: (profil) => {
      // New style changes which blocks are visible — drop cached materials
      queryClient.clear();
      setUser(profil.uzytkownik);
      router.replace("/ankieta/wynik");
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Nie udało się zapisać ankiety."),
  });

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center p-16">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Ładowanie ankiety" />
      </div>
    );
  }

  if (isError || !pytania) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
        <p className="text-slate-600 dark:text-slate-400">Nie udało się wczytać ankiety.</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-xl bg-gradient-to-r from-primary to-secondary px-6 py-2.5 text-sm font-semibold text-white"
        >
          Spróbuj ponownie
        </button>
      </div>
    );
  }

  if (pytania.length === 0) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 items-center justify-center p-8 text-center text-slate-600 dark:text-slate-400">
        Ankieta nie ma jeszcze pytań. Poproś nauczyciela o jej przygotowanie.
      </div>
    );
  }

  const pytanie = pytania[index];
  const odpowiedziane = Object.keys(wybory).length;
  const ostatnie = index === pytania.length - 1;
  const wybrana = wybory[pytanie.id];
  const komplet = odpowiedziane === pytania.length;

  const wybierz = (odpowiedzId: number) => {
    setWybory((p) => ({ ...p, [pytanie.id]: odpowiedzId }));
  };

  return (
    <main className="flex flex-1 items-start justify-center px-4 py-10 md:py-16">
      <div className="w-full max-w-2xl">
        <div className="mb-6 flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/15 ring-1 ring-primary/25">
            <ClipboardList className="h-6 w-6 text-primary" aria-hidden />
          </span>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Ankieta stylu uczenia się</h1>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {user?.ankieta_wypelniona
                ? "Wypełniasz ankietę ponownie — nowy wynik zastąpi Twój obecny styl."
                : "Wybierz odpowiedź, która najlepiej do Ciebie pasuje. Nie ma złych odpowiedzi."}
            </p>
          </div>
        </div>

        <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-600 dark:text-slate-400">
          <span>
            Pytanie {index + 1} z {pytania.length}
          </span>
          <span>Odpowiedzi: {odpowiedziane}</span>
        </div>
        <div
          className="mb-6 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={pytania.length}
          aria-valuenow={odpowiedziane}
        >
          <div
            className="h-full rounded-full bg-gradient-to-r from-primary to-secondary transition-all"
            style={{ width: `${(odpowiedziane / pytania.length) * 100}%` }}
          />
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white/90 p-6 shadow-lg md:p-8 dark:border-white/10 dark:bg-slate-900/80">
          <fieldset>
            <legend className="mb-5 text-lg font-semibold text-slate-900 dark:text-white">
              {pytanie.tresc}
            </legend>
            <div className="space-y-3">
              {pytanie.odpowiedzi.map((o) => {
                const zaznaczona = wybrana === o.id;
                return (
                  <label
                    key={o.id}
                    className={`flex cursor-pointer items-center gap-3 rounded-2xl border px-4 py-3 text-sm transition ${
                      zaznaczona
                        ? "border-primary bg-primary/10 text-slate-900 dark:text-white"
                        : "border-slate-200 bg-white text-slate-700 hover:border-primary/40 dark:border-white/10 dark:bg-slate-950/40 dark:text-slate-200"
                    }`}
                  >
                    <input
                      type="radio"
                      name={`pytanie-${pytanie.id}`}
                      className="sr-only"
                      checked={zaznaczona}
                      onChange={() => wybierz(o.id)}
                    />
                    <span
                      aria-hidden
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                        zaznaczona ? "border-primary bg-primary text-white" : "border-slate-400"
                      }`}
                    >
                      {zaznaczona && <Check className="h-3 w-3" />}
                    </span>
                    {o.tresc}
                  </label>
                );
              })}
            </div>
          </fieldset>

          <div className="mt-8 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => setIndex((i) => Math.max(0, i - 1))}
              disabled={index === 0}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-primary/40 disabled:opacity-40 dark:border-white/10 dark:text-slate-300"
            >
              <ArrowLeft className="h-4 w-4" aria-hidden />
              Wstecz
            </button>
            {ostatnie ? (
              <button
                type="button"
                onClick={() => wyslij.mutate()}
                disabled={!komplet || wyslij.isPending}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-5 py-2 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95 disabled:opacity-50"
              >
                {wyslij.isPending && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
                Zakończ i zobacz wynik
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setIndex((i) => Math.min(pytania.length - 1, i + 1))}
                disabled={wybrana === undefined}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-5 py-2 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95 disabled:opacity-50"
              >
                Dalej
                <ArrowRight className="h-4 w-4" aria-hidden />
              </button>
            )}
          </div>
          {ostatnie && !komplet && (
            <p className="mt-3 text-right text-xs text-slate-500">
              Odpowiedz na wszystkie pytania, aby zakończyć ankietę.
            </p>
          )}
        </div>
      </div>
    </main>
  );
}
