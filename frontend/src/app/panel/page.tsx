"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, Loader2 } from "lucide-react";
import { WynikVak } from "@/components/ankieta/WynikVak";
import { PropozycjaStylu } from "@/components/nauka/PropozycjaStylu";
import { SciezkaView } from "@/components/nauka/SciezkaView";
import { getSciezka } from "@/lib/api";
import { POZIOM_NAZWA, ZRODLO_STYLU_LABEL, nazwaStylu } from "@/lib/labels";
import { BTN_PRIMARY, CARD } from "@/lib/ui";
import { useAuthStore } from "@/store/useAuthStore";

export default function PanelUczniaPage() {
  const user = useAuthStore((s) => s.user);
  const { data: s, isLoading, isError, refetch } = useQuery({
    queryKey: ["sciezka"],
    queryFn: getSciezka,
    staleTime: 0,
  });

  if (isLoading) {
    return (
      <div className="flex flex-1 items-center justify-center p-16">
        <Loader2 className="h-10 w-10 animate-spin text-primary" aria-label="Ładowanie panelu" />
      </div>
    );
  }
  if (isError || !s) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 flex-col items-center justify-center gap-4 p-8 text-center">
        <p className="text-slate-600 dark:text-slate-400">Nie udało się wczytać panelu.</p>
        <button type="button" onClick={() => refetch()} className={BTN_PRIMARY}>
          Spróbuj ponownie
        </button>
      </div>
    );
  }

  const wszystkie = s.kursy.reduce((n, k) => n + k.tematy.length, 0);
  const zaliczone = s.kursy.reduce((n, k) => n + k.zaliczone, 0);

  return (
    <main className="flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-5xl space-y-6">
        <header>
          <h1 className="bg-gradient-to-r from-primary via-cyan-300 to-secondary bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl">
            Cześć, {user?.imie}!
          </h1>
          <p className="mt-1 text-slate-600 dark:text-slate-400">
            Zaliczone tematy: {zaliczone} z {wszystkie}.
          </p>
        </header>

        {s.propozycja_stylu && <PropozycjaStylu propozycja={s.propozycja_stylu} onDecyzja={() => refetch()} />}

        <section className={CARD} data-testid="nastepny-krok">
          <h2 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-500">Twój następny krok</h2>
          {s.nastepny_krok ? (
            <>
              <p className="text-xl font-semibold text-slate-900 dark:text-white">{s.nastepny_krok.tytul}</p>
              <p className="text-sm text-slate-500">{s.nastepny_krok.kurs}</p>
              <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                Dlaczego to widzisz: {s.nastepny_krok.dlaczego}
              </p>
              <Link href={`/tematy/${s.nastepny_krok.temat_id}`} className={`${BTN_PRIMARY} mt-4`}>
                Ucz się dalej
                <ArrowRight className="h-4 w-4" aria-hidden />
              </Link>
            </>
          ) : wszystkie > 0 ? (
            <p className="text-lg font-semibold text-emerald-600 dark:text-emerald-300">
              Wszystkie tematy zaliczone — gratulacje!
            </p>
          ) : (
            <p className="text-slate-600 dark:text-slate-400">Nie ma jeszcze opublikowanych kursów.</p>
          )}
        </section>

        <div className="grid gap-6 md:grid-cols-2">
          <section className={CARD}>
            <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-white">Mój styl uczenia</h2>
            <p className="mb-4 text-sm text-slate-700 dark:text-slate-300" data-testid="panel-styl">
              <strong className="capitalize">{nazwaStylu(s.styl_uczenia)}</strong>
              {s.styl_zrodlo ? ` (${ZRODLO_STYLU_LABEL[s.styl_zrodlo] ?? s.styl_zrodlo})` : ""}
              {s.styl_ankiety && s.styl_ankiety !== s.styl_uczenia ? (
                <> · wynik ankiety: {nazwaStylu(s.styl_ankiety)}</>
              ) : null}
            </p>
            <Link href="/profil" className="text-sm font-semibold text-primary hover:underline">
              Zmień styl lub powtórz ankietę
            </Link>
          </section>

          <section className={CARD}>
            <h2 className="mb-1 text-lg font-semibold text-slate-900 dark:text-white">Jak Ci idzie</h2>
            <p className="mb-4 text-sm text-slate-600 dark:text-slate-400">
              Wagi stylów: start z ankiety, potem +1 za zaliczony quiz i −1 za niezaliczony.
            </p>
            <WynikVak punkty={s.wagi} dominujacy={s.styl_uczenia} />
            <p className="mt-4 text-sm text-slate-700 dark:text-slate-300">
              Poziom materiałów: <strong>{POZIOM_NAZWA[s.poziom]}</strong>
            </p>
            {s.poziom_dlaczego && (
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">{s.poziom_dlaczego}</p>
            )}
          </section>
        </div>

        <section className={CARD}>
          <h2 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">Moja ścieżka</h2>
          <SciezkaView kursy={s.kursy} nastepnyTematId={s.nastepny_krok?.temat_id} />
        </section>
      </div>
    </main>
  );
}
