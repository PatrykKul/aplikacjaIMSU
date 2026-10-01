"use client";

import { useEffect, useState } from "react";
import { Loader2, Plus, GripVertical } from "lucide-react";
import { motion } from "framer-motion";
import { toast } from "sonner";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
import {
  createKurs,
  deleteKurs,
  getKursy,
  reorderKursy,
  type KursPayload,
  updateKurs,
} from "@/lib/api";
import type { Kurs } from "@/lib/types";
import { SpotlightCourseCard } from "@/components/SpotlightCourseCard";
import { KursModal } from "@/components/modals/KursModal";
import { useAdminStore } from "@/store/useAdminStore";

const API_TIMEOUT_USER_MSG =
  "Serwer nie odpowiada w wyznaczonym czasie. Uruchom backend (np. uvicorn na porcie 8000), zrestartuj go albo sprawdź, czy plik bazy SQLite nie jest zablokowany przez inny program.";

function SortableKursItem({
  kurs,
  index,
  isAdmin,
  onEdit,
  onDelete,
}: {
  kurs: Kurs;
  index: number;
  isAdmin: boolean;
  onEdit?: (kurs: Kurs) => void;
  onDelete?: (kurs: Kurs) => void;
}) {
  const {
    attributes,
    listeners,
    setNodeRef,
    setActivatorNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: kurs.id,
    disabled: !isAdmin,
  });

  return (
    <div
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
        opacity: isDragging ? 0.85 : 1,
      }}
      className={isDragging ? "z-20" : undefined}
    >
      <SpotlightCourseCard
        kurs={kurs}
        index={index}
        isAdmin={isAdmin}
        onEdit={onEdit}
        onDelete={onDelete}
        dragHandle={
          isAdmin ? (
            <button
              ref={setActivatorNodeRef}
              type="button"
              className="rounded-lg border border-slate-300 bg-white/90 p-1.5 text-slate-500 shadow-sm transition hover:bg-slate-100 dark:border-white/10 dark:bg-slate-900/70 dark:text-slate-300 dark:hover:bg-slate-800"
              aria-label="Przeciągnij kurs"
              title="Przeciągnij kurs"
              {...attributes}
              {...listeners}
            >
              <GripVertical className="h-4 w-4" />
            </button>
          ) : null
        }
      />
    </div>
  );
}

export function KursyListClient() {
  const isAdmin = useAdminStore((s) => s.isAdmin);
  const queryClient = useQueryClient();
  const [modal, setModal] = useState<"create" | "edit" | null>(null);
  const [editing, setEditing] = useState<Kurs | null>(null);
  const [nazwa, setNazwa] = useState("");
  const [opis, setOpis] = useState("");
  const [isPublished, setIsPublished] = useState(false);
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const kursyQuery = useQuery({
    queryKey: ["kursy"],
    queryFn: getKursy,
    staleTime: isAdmin ? 0 : 30_000,
  });
  const { refetch } = kursyQuery;
  const [kursy, setKursy] = useState<Kurs[]>(kursyQuery.data ?? []);

  useEffect(() => {
    if (kursyQuery.data) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setKursy(kursyQuery.data);
    }
  }, [kursyQuery.data]);

  useEffect(() => {
    if (!isAdmin) return;
    // Po przełączeniu edit mode wymuszamy świeży odczyt z API,
    // żeby modal zawsze miał aktualne `is_published` z bazy.
    void refetch();
  }, [isAdmin, refetch]);

  const createMutation = useMutation({
    mutationFn: (payload: KursPayload) => createKurs(payload),
    onSuccess: () => {
      toast.success("Kurs dodany.");
      queryClient.invalidateQueries({ queryKey: ["kursy"] });
      closeModal();
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Operacja nie powiodła się.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: KursPayload }) =>
      updateKurs(id, payload),
    onSuccess: () => {
      toast.success("Kurs zaktualizowany.");
      queryClient.invalidateQueries({ queryKey: ["kursy"] });
      closeModal();
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Operacja nie powiodła się.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (kursId: number) => deleteKurs(kursId),
    onSuccess: () => {
      toast.success("Kurs usunięty.");
      queryClient.invalidateQueries({ queryKey: ["kursy"] });
    },
    onError: (err) => {
      toast.error(err instanceof Error ? err.message : "Nie udało się usunąć.");
    },
  });

  const reorderMutation = useMutation({
    mutationFn: (ids: number[]) => reorderKursy(ids),
    onMutate: async (ids) => {
      await queryClient.cancelQueries({ queryKey: ["kursy"] });
      const previous = queryClient.getQueryData<Kurs[]>(["kursy"]) ?? [];
      const byId = new Map(previous.map((k) => [k.id, k]));
      const optimistic = ids.map((id) => byId.get(id)).filter((k): k is Kurs => Boolean(k));
      queryClient.setQueryData<Kurs[]>(["kursy"], optimistic);
      setKursy(optimistic);
      return { previous };
    },
    onError: (err, _vars, ctx) => {
      queryClient.setQueryData(["kursy"], ctx?.previous ?? []);
      setKursy(ctx?.previous ?? []);
      toast.error(
        err instanceof Error ? err.message : "Nie udało się zapisać kolejności kursów."
      );
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(["kursy"], updated);
      setKursy(updated);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["kursy"] });
    },
  });

  const openCreate = () => {
    setEditing(null);
    setNazwa("");
    setOpis("");
    setIsPublished(false);
    setModal("create");
  };

  const openEdit = (k: Kurs) => {
    setEditing(k);
    setNazwa(k.nazwa);
    setOpis(k.opis);
    setIsPublished(k.is_published ?? false);
    setModal("edit");
  };

  const closeModal = () => {
    setModal(null);
    setEditing(null);
  };

  const onSubmitKurs = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: KursPayload = { nazwa, opis, is_published: isPublished };
    if (modal === "create") {
      await createMutation.mutateAsync(payload);
    } else if (modal === "edit" && editing) {
      await updateMutation.mutateAsync({ id: editing.id, payload });
    }
  };

  const onDeleteKurs = async (k: Kurs) => {
    if (!window.confirm(`Usunąć kurs „${k.nazwa}” wraz z całą zawartością?`)) return;
    await deleteMutation.mutateAsync(k.id);
  };

  const onDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;
    const oldIndex = kursy.findIndex((k) => k.id === Number(active.id));
    const newIndex = kursy.findIndex((k) => k.id === Number(over.id));
    if (oldIndex < 0 || newIndex < 0) return;
    const next = arrayMove(kursy, oldIndex, newIndex);
    await reorderMutation.mutateAsync(next.map((k) => k.id));
  };

  return (
    <main className="relative min-h-screen flex-1 px-4 py-10 text-slate-900 md:px-8 md:py-16 dark:text-slate-100">
      <div className="mx-auto mb-12 max-w-5xl text-center md:mb-16 md:text-left">
        <motion.h1
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-4 bg-gradient-to-r from-primary via-cyan-200 to-secondary bg-clip-text text-4xl font-extrabold tracking-tight text-transparent md:text-5xl"
        >
          StylNauki
        </motion.h1>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="text-lg text-slate-600 md:text-xl dark:text-slate-400"
        >
          Wybierz kurs, aby przejść do działów i lekcji.
        </motion.p>
      </div>

      {kursyQuery.isLoading ? (
        <div className="flex min-h-[40vh] items-center justify-center">
          <Loader2 className="size-12 animate-spin text-primary" />
        </div>
      ) : kursyQuery.isError ? (
        <div className="mx-auto flex max-w-lg flex-col items-center gap-4 rounded-2xl border border-amber-500/30 bg-amber-100/60 px-6 py-10 text-center dark:bg-amber-500/5">
          <p className="text-sm text-amber-900 dark:text-amber-100/90">
            {kursyQuery.error instanceof Error && kursyQuery.error.name === "AbortError"
              ? API_TIMEOUT_USER_MSG
              : "Nie udało się połączyć z serwerem."}
          </p>
          <button
            type="button"
            onClick={() => kursyQuery.refetch()}
            className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
          >
            Spróbuj ponownie
          </button>
        </div>
      ) : (
        <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={isAdmin ? onDragEnd : undefined}
          >
            <SortableContext items={kursy.map((k) => k.id)} strategy={verticalListSortingStrategy}>
              {kursy.map((kurs, index) => (
                <SortableKursItem
                  key={kurs.id}
                  kurs={kurs}
                  index={index}
                  isAdmin={isAdmin}
                  onEdit={isAdmin ? openEdit : undefined}
                  onDelete={isAdmin ? onDeleteKurs : undefined}
                />
              ))}
            </SortableContext>
          </DndContext>

          {isAdmin && (
            <motion.button
              type="button"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: kursy.length * 0.06 }}
              onClick={openCreate}
              className="group flex min-h-[7rem] w-full items-center justify-center gap-3 rounded-3xl border-2 border-dashed border-slate-300 bg-white/50 text-slate-600 transition hover:border-primary/50 hover:bg-primary/5 hover:text-primary hover:shadow-[0_0_32px_rgba(168,85,247,0.12)] dark:border-slate-600/80 dark:bg-slate-900/20 dark:text-slate-500"
            >
              <Plus className="h-6 w-6 transition group-hover:scale-110" />
              <span className="text-lg font-semibold tracking-tight">
                Dodaj nowy kurs
              </span>
            </motion.button>
          )}

          {kursy.length === 0 && !isAdmin && (
            <p className="rounded-2xl border border-dashed border-slate-300 py-20 text-center text-slate-500 dark:border-slate-700">
              Brak opublikowanych kursów.
            </p>
          )}
        </div>
      )}

      <KursModal
        open={modal !== null}
        title={modal === "edit" ? "Edytuj kurs" : "Nowy kurs"}
        submitLabel={modal === "edit" ? "Zapisz" : "Utwórz kurs"}
        nazwa={nazwa}
        opis={opis}
        onNazwaChange={setNazwa}
        onOpisChange={setOpis}
        isPublished={isPublished}
        onIsPublishedChange={setIsPublished}
        onClose={closeModal}
        onSubmit={onSubmitKurs}
        submitting={createMutation.isPending || updateMutation.isPending}
      />
    </main>
  );
}
