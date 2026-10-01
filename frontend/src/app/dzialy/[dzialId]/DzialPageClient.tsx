"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  BookMarked,
  ChevronRight,
  FolderOpen,
  GripVertical,
  Loader2,
  Pencil,
  Plus,
  Trash2,
} from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  arrayMove,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { apiFetch, authFetch, getApiBase, reorderTematy } from "@/lib/api";
import type { Dzial, Kurs, TematSummary } from "@/lib/types";
import { InlineFieldModal } from "@/components/modals/InlineFieldModal";
import { useAdminStore } from "@/store/useAdminStore";

type Props = {
  dzialId: number;
};

function TematCardBody({
  temat,
  dragHandle,
  isDragging = false,
}: {
  temat: TematSummary;
  dragHandle?: ReactNode;
  isDragging?: boolean;
}) {
  return (
    <div
      className={`group flex items-start gap-4 rounded-2xl border border-slate-200 bg-white/85 p-5 pr-14 shadow-card transition hover:border-primary/35 hover:shadow-neon-sm dark:border-white/[0.07] dark:bg-slate-900/45 ${
        isDragging ? "ring-2 ring-primary/50 shadow-2xl" : ""
      }`}
    >
      {dragHandle}
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-secondary/15 ring-1 ring-primary/25">
        <BookMarked className="h-5 w-5 text-primary" />
      </div>
      <div className="min-w-0 flex-1">
        <h3 className="font-semibold text-slate-900 transition group-hover:text-primary dark:text-white">
          {temat.tytul}
        </h3>
        <p className="mt-1 text-sm text-slate-500">Lekcja w formie bloków</p>
      </div>
      <ChevronRight className="mt-1 h-5 w-5 shrink-0 text-slate-600 transition group-hover:translate-x-0.5 group-hover:text-primary" />
    </div>
  );
}

function SortableTematItem({
  temat,
  isAdmin,
  onEdit,
  onDelete,
}: {
  temat: TematSummary;
  isAdmin: boolean;
  onEdit: (t: TematSummary) => void;
  onDelete: (t: TematSummary) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: temat.id, disabled: !isAdmin });

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={`relative ${isDragging ? "z-20 opacity-[0.85]" : ""}`}
    >
      <Link href={`/tematy/${temat.id}`} className="block">
        <TematCardBody
          temat={temat}
          isDragging={isDragging}
          dragHandle={
            isAdmin ? (
              <button
                ref={setActivatorNodeRef}
                type="button"
                className="rounded-lg border border-slate-300 bg-white/90 p-1.5 text-slate-500 shadow-sm transition hover:bg-slate-100 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:bg-slate-800"
                aria-label="Przeciągnij temat"
                title="Przeciągnij temat"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                {...attributes}
                {...listeners}
              >
                <GripVertical className="h-4 w-4" />
              </button>
            ) : undefined
          }
        />
      </Link>
      {isAdmin && (
        <div className="absolute right-3 top-3 z-10 flex gap-0.5">
          <button
            type="button"
            title="Edytuj temat"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onEdit(temat);
            }}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-200 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-white"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            type="button"
            title="Usuń temat"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDelete(temat);
            }}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-rose-500/15 hover:text-rose-200"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}

export function DzialPageClient({
  dzialId,
}: Props) {
  const queryClient = useQueryClient();
  const isAdmin = useAdminStore((s) => s.isAdmin);

  const [tematModal, setTematModal] = useState<"create" | "edit" | null>(null);
  const [editingTemat, setEditingTemat] = useState<TematSummary | null>(null);
  const [tematTytul, setTematTytul] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [orderedTematy, setOrderedTematy] = useState<TematSummary[]>(
    []
  );
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const { data: dzial, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dzial", dzialId],
    queryFn: () => apiFetch<Dzial>(`/dzialy/${dzialId}`),
    enabled: Number.isFinite(dzialId),
    staleTime: isAdmin ? 0 : 30_000,
    refetchOnWindowFocus: isAdmin,
  });

  const { data: kurs } = useQuery({
    queryKey: ["kurs", dzial?.kurs_id],
    queryFn: () => apiFetch<Kurs>(`/kursy/${dzial!.kurs_id}`),
    enabled: !!dzial?.kurs_id,
    staleTime: isAdmin ? 0 : 30_000,
    refetchOnWindowFocus: isAdmin,
  });

  useEffect(() => {
    if (isError && error instanceof Error) {
      toast.error("Nie udało się załadować działu.");
    }
  }, [isError, error]);

  const invalidateDzial = () => {
    queryClient.invalidateQueries({ queryKey: ["dzial", dzialId] });
    if (dzial?.kurs_id) {
      queryClient.invalidateQueries({ queryKey: ["kurs", dzial.kurs_id] });
    }
  };

  useEffect(() => {
    setOrderedTematy(dzial?.tematy ?? []);
  }, [dzial?.tematy]);

  const openCreateTemat = () => {
    setEditingTemat(null);
    setTematTytul("");
    setTematModal("create");
  };

  const openEditTemat = (t: TematSummary) => {
    setEditingTemat(t);
    setTematTytul(t.tytul);
    setTematModal("edit");
  };

  const onSubmitTemat = async (e: React.FormEvent) => {
    e.preventDefault();
    const api = getApiBase();
    setSubmitting(true);
    try {
      if (tematModal === "create") {
        const res = await authFetch(`${api}/dzialy/${dzialId}/tematy`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tytul: tematTytul }),
        });
        if (!res.ok) throw new Error(await res.text());
        toast.success("Temat dodany.");
      } else if (tematModal === "edit" && editingTemat) {
        const res = await authFetch(`${api}/tematy/${editingTemat.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ tytul: tematTytul }),
        });
        if (!res.ok) throw new Error(await res.text());
        toast.success("Temat zaktualizowany.");
      }
      setTematModal(null);
      setEditingTemat(null);
      invalidateDzial();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Błąd zapisu.");
    } finally {
      setSubmitting(false);
    }
  };

  const onDeleteTemat = async (t: TematSummary) => {
    if (!window.confirm(`Usunąć temat „${t.tytul}”?`)) return;
    const api = getApiBase();
    try {
      const res = await authFetch(`${api}/tematy/${t.id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      toast.success("Temat usunięty.");
      invalidateDzial();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Nie udało się usunąć.");
    }
  };

  const onDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = orderedTematy.findIndex((t) => t.id === active.id);
    const newIndex = orderedTematy.findIndex((t) => t.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;
    const prev = orderedTematy;
    const next = arrayMove(orderedTematy, oldIndex, newIndex);
    setOrderedTematy(next);
    try {
      await reorderTematy(dzialId, next.map((t) => t.id));
      invalidateDzial();
    } catch (err) {
      setOrderedTematy(prev);
      toast.error(
        err instanceof Error ? err.message : "Nie udało się zapisać kolejności tematów."
      );
    }
  };

  if (!Number.isFinite(dzialId)) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-slate-400">
        Nieprawidłowy identyfikator działu.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-16">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-sm text-slate-500">Ładowanie działu…</p>
      </div>
    );
  }

  if (isError || !dzial) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 flex-col items-center justify-center gap-6 p-8 text-center">
        <p className="text-slate-400">Nie można wyświetlić tego działu.</p>
        <button
          type="button"
          onClick={() => refetch()}
          className="rounded-xl bg-gradient-to-r from-primary to-secondary px-6 py-2.5 text-sm font-semibold text-white shadow-neon-sm"
        >
          Spróbuj ponownie
        </button>
        <Link href="/kursy" className="text-sm text-primary hover:underline">
          Wróć na stronę główną
        </Link>
      </div>
    );
  }

  const tematy = orderedTematy;

  return (
    <main className="flex-1 px-4 py-10 md:px-8">
      <div className="mx-auto max-w-6xl">
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
            <span className="animate-pulse text-slate-600">…</span>
          )}
          <ChevronRight className="h-4 w-4 shrink-0 opacity-40" />
          <span className="text-slate-900 dark:bg-gradient-to-r dark:from-slate-200 dark:to-slate-400 dark:bg-clip-text dark:text-transparent">
            {dzial.nazwa}
          </span>
        </nav>

        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative mb-12 overflow-hidden rounded-3xl border border-slate-200 bg-white/80 p-8 shadow-card backdrop-blur-md md:p-10 dark:border-white/10 dark:bg-slate-900/45"
        >
          <div className="pointer-events-none absolute -left-20 top-0 h-56 w-56 rounded-full bg-secondary/25 blur-[90px]" />
          <div className="pointer-events-none absolute -right-10 bottom-0 h-40 w-40 rounded-full bg-primary/20 blur-[70px]" />
          <div className="relative flex flex-col gap-4">
            <div className="flex items-center gap-3 text-primary">
              <FolderOpen className="h-9 w-9" />
              <span className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
                Dział
              </span>
            </div>
            <h1 className="bg-gradient-to-r from-primary via-cyan-200 to-secondary bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl lg:text-5xl">
              {dzial.nazwa}
            </h1>
            {kurs && (
              <Link
                href={`/kursy/${kurs.id}`}
                className="inline-flex w-fit items-center gap-2 text-sm text-slate-500 transition hover:text-primary"
              >
                <ArrowLeft className="h-4 w-4 rotate-180" />
                Wróć do kursu: {kurs.nazwa}
              </Link>
            )}
          </div>
        </motion.header>

        <h2 className="mb-6 flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white">
          <BookMarked className="h-5 w-5 text-secondary" />
          Tematy lekcyjne
        </h2>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={isAdmin ? onDragEnd : undefined}
        >
          <SortableContext items={tematy.map((t) => t.id)} strategy={verticalListSortingStrategy}>
            <div className="flex flex-col gap-4">
              {tematy.map((temat) => (
                <SortableTematItem
                  key={temat.id}
                  temat={temat}
                  isAdmin={isAdmin}
                  onEdit={openEditTemat}
                  onDelete={onDeleteTemat}
                />
              ))}

              {isAdmin && (
                <motion.button
                  type="button"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  onClick={openCreateTemat}
                  className="flex min-h-[120px] flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-slate-300 bg-white/60 text-slate-600 transition hover:border-primary/45 hover:bg-primary/5 hover:text-primary dark:border-slate-600/80 dark:bg-slate-900/25 dark:text-slate-500"
                >
                  <Plus className="h-7 w-7" />
                  <span className="text-sm font-semibold">Dodaj nowy temat</span>
                </motion.button>
              )}
            </div>
          </SortableContext>
        </DndContext>

        {tematy.length === 0 && !isAdmin && (
          <p className="rounded-2xl border border-dashed border-slate-300 py-16 text-center text-slate-500 dark:border-slate-700">
            Brak tematów w tym dziale.
          </p>
        )}
      </div>

      <InlineFieldModal
        open={tematModal !== null}
        title={tematModal === "edit" ? "Edytuj temat" : "Nowy temat"}
        label="Tytuł tematu"
        value={tematTytul}
        onChange={setTematTytul}
        onClose={() => {
          setTematModal(null);
          setEditingTemat(null);
        }}
        onSubmit={onSubmitTemat}
        submitting={submitting}
        submitLabel={tematModal === "edit" ? "Zapisz" : "Dodaj temat"}
      />
    </main>
  );
}
