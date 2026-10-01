"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  ChevronRight,
  FolderKanban,
  GripVertical,
  GraduationCap,
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
import { apiFetch, getApiBase, reorderDzialy } from "@/lib/api";
import type { Dzial, Kurs } from "@/lib/types";
import { InlineFieldModal } from "@/components/modals/InlineFieldModal";
import { useAdminStore } from "@/store/useAdminStore";

type Props = {
  kursId: number;
  initialKurs: Kurs;
};

function DzialCardBody({
  dzial,
  dragHandle,
  isDragging = false,
}: {
  dzial: Dzial;
  dragHandle?: ReactNode;
  isDragging?: boolean;
}) {
  return (
    <div
      className={`group relative h-full overflow-hidden rounded-2xl border border-slate-200 bg-white/85 p-6 shadow-card transition hover:border-primary/40 hover:shadow-neon-sm dark:border-white/[0.08] dark:bg-slate-900/50 ${
        isDragging ? "ring-2 ring-primary/50 shadow-2xl" : ""
      }`}
    >
      <div className="absolute -right-8 -top-8 h-28 w-28 rounded-full bg-primary/20 blur-3xl transition group-hover:bg-primary/35" />
      {dragHandle ? <div className="absolute left-3 top-3 z-10">{dragHandle}</div> : null}
      <div className="relative">
        <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 to-secondary/20 ring-1 ring-primary/30 transition group-hover:scale-105">
          <FolderKanban className="h-7 w-7 text-primary" />
        </div>
        <h3 className="text-xl font-semibold text-slate-900 transition group-hover:text-primary dark:text-white">
          {dzial.nazwa}
        </h3>
        <p className="mt-3 flex items-center text-sm font-medium text-primary/90 opacity-0 transition group-hover:opacity-100">
          Otwórz dział
          <ChevronRight className="ml-1 h-4 w-4" />
        </p>
      </div>
    </div>
  );
}

function SortableDzialItem({
  dzial,
  isAdmin,
  onEdit,
  onDelete,
}: {
  dzial: Dzial;
  isAdmin: boolean;
  onEdit: (d: Dzial) => void;
  onDelete: (d: Dzial) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: dzial.id, disabled: !isAdmin });

  return (
    <div
      ref={setNodeRef}
      style={{ transform: CSS.Transform.toString(transform), transition }}
      className={`relative ${isDragging ? "z-20 opacity-90 scale-[1.01]" : ""}`}
    >
      <Link href={`/dzialy/${dzial.id}`} className="block h-full">
        <DzialCardBody
          dzial={dzial}
          isDragging={isDragging}
          dragHandle={
            isAdmin ? (
              <button
                ref={setActivatorNodeRef}
                type="button"
                className="rounded-lg border border-slate-300 bg-white/90 p-1.5 text-slate-500 shadow-sm transition hover:bg-slate-100 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:bg-slate-800"
                aria-label="Przeciągnij dział"
                title="Przeciągnij dział"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                {...attributes}
                {...listeners}
              >
                <GripVertical className="h-4 w-4" />
              </button>
            ) : null
          }
        />
      </Link>
      {isAdmin && (
        <div className="absolute right-3 top-3 z-10 flex gap-0.5">
          <button
            type="button"
            title="Edytuj dział"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onEdit(dzial);
            }}
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-200 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-white"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            type="button"
            title="Usuń dział"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onDelete(dzial);
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

export function KursDetailClient({ kursId, initialKurs }: Props) {
  const queryClient = useQueryClient();
  const isAdmin = useAdminStore((s) => s.isAdmin);

  const [dzialModal, setDzialModal] = useState<"create" | "edit" | null>(null);
  const [editingDzial, setEditingDzial] = useState<Dzial | null>(null);
  const [dzialNazwa, setDzialNazwa] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [orderedDzialy, setOrderedDzialy] = useState<Dzial[]>(initialKurs.dzialy ?? []);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["kurs", kursId],
    queryFn: () => apiFetch<Kurs>(`/kursy/${kursId}`),
    enabled: Number.isFinite(kursId),
    initialData: initialKurs,
    staleTime: isAdmin ? 0 : Infinity,
    refetchOnMount: isAdmin,
    refetchOnWindowFocus: isAdmin,
  });

  useEffect(() => {
    if (isError && error instanceof Error) {
      toast.error("Nie udało się załadować kursu.");
    }
  }, [isError, error]);

  const invalidateKurs = () => {
    queryClient.invalidateQueries({ queryKey: ["kurs", kursId] });
  };

  useEffect(() => {
    setOrderedDzialy(data?.dzialy ?? []);
  }, [data?.dzialy]);

  const openCreateDzial = () => {
    setEditingDzial(null);
    setDzialNazwa("");
    setDzialModal("create");
  };

  const openEditDzial = (d: Dzial) => {
    setEditingDzial(d);
    setDzialNazwa(d.nazwa);
    setDzialModal("edit");
  };

  const onSubmitDzial = async (e: React.FormEvent) => {
    e.preventDefault();
    const api = getApiBase();
    setSubmitting(true);
    try {
      if (dzialModal === "create") {
        const res = await fetch(`${api}/kursy/${kursId}/dzialy`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nazwa: dzialNazwa }),
        });
        if (!res.ok) throw new Error(await res.text());
        toast.success("Dział dodany.");
      } else if (dzialModal === "edit" && editingDzial) {
        const res = await fetch(`${api}/dzialy/${editingDzial.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nazwa: dzialNazwa }),
        });
        if (!res.ok) throw new Error(await res.text());
        toast.success("Dział zaktualizowany.");
      }
      setDzialModal(null);
      setEditingDzial(null);
      invalidateKurs();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Błąd zapisu.");
    } finally {
      setSubmitting(false);
    }
  };

  const onDeleteDzial = async (d: Dzial) => {
    if (!window.confirm(`Usunąć dział „${d.nazwa}” wraz z tematami?`)) return;
    const api = getApiBase();
    try {
      const res = await fetch(`${api}/dzialy/${d.id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(await res.text());
      toast.success("Dział usunięty.");
      invalidateKurs();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Nie udało się usunąć.");
    }
  };

  const onDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = orderedDzialy.findIndex((d) => d.id === active.id);
    const newIndex = orderedDzialy.findIndex((d) => d.id === over.id);
    if (oldIndex < 0 || newIndex < 0) return;

    const prev = orderedDzialy;
    const next = arrayMove(orderedDzialy, oldIndex, newIndex);
    setOrderedDzialy(next);
    try {
      await reorderDzialy(kursId, next.map((d) => d.id));
      invalidateKurs();
    } catch (err) {
      setOrderedDzialy(prev);
      toast.error(
        err instanceof Error ? err.message : "Nie udało się zapisać kolejności działów."
      );
    }
  };

  if (!Number.isFinite(kursId)) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-slate-400">
        Nieprawidłowy identyfikator kursu.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-16">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="text-sm text-slate-500">Ładowanie kursu…</p>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="mx-auto flex max-w-lg flex-1 flex-col items-center justify-center gap-6 p-8 text-center">
        <p className="text-slate-400">Nie można wyświetlić tego kursu.</p>
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

  const dzialy = orderedDzialy;

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
          <span className="text-slate-900 dark:bg-gradient-to-r dark:from-slate-200 dark:to-slate-400 dark:bg-clip-text dark:text-transparent">
            {data.nazwa}
          </span>
        </nav>

        <motion.header
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative mb-12 overflow-hidden rounded-3xl border border-slate-200 bg-white/80 p-8 shadow-card backdrop-blur-md md:p-12 dark:border-white/10 dark:bg-slate-900/40"
        >
          <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-primary/30 blur-[100px]" />
          <div className="pointer-events-none absolute bottom-0 left-1/4 h-48 w-48 rounded-full bg-secondary/20 blur-[80px]" />
          <div className="relative">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-primary/25 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-wider text-primary">
              <GraduationCap className="h-3.5 w-3.5" />
              Kurs
            </div>
            <h1 className="bg-gradient-to-r from-primary via-cyan-200 to-secondary bg-clip-text text-3xl font-bold tracking-tight text-transparent md:text-4xl lg:text-5xl">
              {data.nazwa}
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-slate-700 dark:text-slate-400">
              {data.opis}
            </p>
          </div>
        </motion.header>

        <h2 className="mb-6 flex items-center gap-2 text-lg font-bold text-slate-900 dark:text-white">
          <FolderKanban className="h-5 w-5 text-primary" />
          Działy
        </h2>

        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={isAdmin ? onDragEnd : undefined}
        >
          <SortableContext items={dzialy.map((d) => d.id)} strategy={verticalListSortingStrategy}>
            <div className="flex flex-col gap-4">
              {dzialy.map((dzial) => (
                <SortableDzialItem
                  key={dzial.id}
                  dzial={dzial}
                  isAdmin={isAdmin}
                  onEdit={openEditDzial}
                  onDelete={onDeleteDzial}
                />
              ))}

              {isAdmin && (
                <motion.button
                  type="button"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: dzialy.length * 0.05 }}
                  onClick={openCreateDzial}
                  className="flex min-h-[120px] flex-col items-center justify-center gap-2 rounded-2xl border-2 border-dashed border-slate-300 bg-white/60 text-slate-600 transition hover:border-primary/45 hover:bg-primary/5 hover:text-primary dark:border-slate-600/80 dark:bg-slate-900/25 dark:text-slate-500"
                >
                  <Plus className="h-8 w-8" />
                  <span className="text-sm font-semibold">Dodaj nowy dział</span>
                </motion.button>
              )}
            </div>
          </SortableContext>
        </DndContext>

        {dzialy.length === 0 && !isAdmin && (
          <p className="rounded-2xl border border-dashed border-slate-300 py-16 text-center text-slate-500 dark:border-slate-700">
            Brak działów w tym kursie.
          </p>
        )}
      </div>

      <InlineFieldModal
        open={dzialModal !== null}
        title={dzialModal === "edit" ? "Edytuj dział" : "Nowy dział"}
        label="Nazwa działu"
        value={dzialNazwa}
        onChange={setDzialNazwa}
        onClose={() => {
          setDzialModal(null);
          setEditingDzial(null);
        }}
        onSubmit={onSubmitDzial}
        submitting={submitting}
        submitLabel={dzialModal === "edit" ? "Zapisz" : "Dodaj dział"}
      />
    </main>
  );
}
