"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";
import { ArrowLeft, BookOpen, ChevronRight, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { apiFetch } from "@/lib/api";
import { TematLessonView } from "@/components/temat/TematLessonView";
import type { Dzial, Kurs, Temat } from "@/lib/types";
import { useAdminStore } from "@/store/useAdminStore";

type Props = {
  tematId: number;
  initialTemat: Temat;
  initialDzial: Dzial;
  initialKurs: Kurs;
};

export function TematPageClient({
  tematId,
  initialTemat,
  initialDzial,
  initialKurs,
}: Props) {
  const isAdmin = useAdminStore((s) => s.isAdmin);

  const { data: temat, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["temat", tematId],
    queryFn: () => apiFetch<Temat>(`/tematy/${tematId}`),
    enabled: Number.isFinite(tematId),
    initialData: initialTemat,
    staleTime: isAdmin ? 0 : Infinity,
    refetchOnMount: isAdmin,
    refetchOnWindowFocus: isAdmin,
  });

  const { data: dzial } = useQuery({
    queryKey: ["dzial", temat?.dzial_id],
    queryFn: () => apiFetch<Dzial>(`/dzialy/${temat!.dzial_id}`),
    enabled: !!temat?.dzial_id,
    initialData: initialDzial,
    staleTime: isAdmin ? 0 : Infinity,
    refetchOnMount: isAdmin,
    refetchOnWindowFocus: isAdmin,
  });

  const { data: kurs } = useQuery({
    queryKey: ["kurs", dzial?.kurs_id],
    queryFn: () => apiFetch<Kurs>(`/kursy/${dzial!.kurs_id}`),
    enabled: !!dzial?.kurs_id,
    initialData: initialKurs,
    staleTime: isAdmin ? 0 : Infinity,
    refetchOnMount: isAdmin,
    refetchOnWindowFocus: isAdmin,
  });

  useEffect(() => {
    if (isError && error instanceof Error) {
      toast.error("Nie udało się załadować tematu.");
    }
  }, [isError, error]);

  if (!Number.isFinite(tematId)) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-slate-400">
        Nieprawidłowy identyfikator tematu.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-16">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-sm text-slate-500">Ładowanie lekcji…</p>
      </div>
    );
  }

  if (isError || !temat) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 flex-col items-center justify-center gap-6 p-8 text-center">
        <p className="text-slate-400">Nie można wyświetlić tego tematu.</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-xl bg-gradient-to-r from-primary to-secondary px-6 py-2.5 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95"
        >
          Spróbuj ponownie
        </button>
        <Link href="/kursy" className="text-sm text-primary hover:underline">
          Wróć na stronę główną
        </Link>
      </div>
    );
  }

  return (
    <main className="relative flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-4xl">
        <nav className="mb-8 flex flex-wrap items-center gap-2 text-sm text-slate-600 dark:text-slate-500">
          <Link
            href="/kursy"
            className="inline-flex items-center gap-1 transition hover:text-primary"
          >
            <ArrowLeft className="h-4 w-4" />
            Start
          </Link>
          <ChevronRight className="h-4 w-4 shrink-0 opacity-40" />
          {kurs ? (
            <Link
              href={`/kursy/${kurs.id}`}
              className="transition hover:text-slate-200"
            >
              {kurs.nazwa}
            </Link>
          ) : (
            <span className="text-slate-600">…</span>
          )}
          <ChevronRight className="h-4 w-4 shrink-0 opacity-40" />
          {dzial ? (
            <Link
              href={`/dzialy/${dzial.id}`}
              className="transition hover:text-slate-200"
            >
              {dzial.nazwa}
            </Link>
          ) : (
            <span className="text-slate-600">…</span>
          )}
          <ChevronRight className="h-4 w-4 shrink-0 opacity-40" />
          <span className="max-w-[12rem] truncate text-slate-900 dark:bg-gradient-to-r dark:from-slate-200 dark:to-slate-400 dark:bg-clip-text dark:text-transparent md:max-w-none">
            {temat.tytul}
          </span>
        </nav>

        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-10"
        >
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/30 bg-primary/10 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-primary">
            <BookOpen className="h-3.5 w-3.5" />
            Lekcja
          </div>
          <h1 className="bg-gradient-to-r from-primary via-cyan-300 to-secondary bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl lg:text-5xl">
            {temat.tytul}
          </h1>
        </motion.header>

        <TematLessonView
          tematId={tematId}
          isAdmin={isAdmin}
          initialData={initialTemat}
          materialyContext={
            kurs && dzial && temat
              ? {
                  kursNazwa: kurs.nazwa,
                  dzialNazwa: dzial.nazwa,
                  tematNazwa: temat.tytul,
                }
              : undefined
          }
        />
      </div>
    </main>
  );
}
