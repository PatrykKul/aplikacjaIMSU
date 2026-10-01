"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createRoot, type Root } from "react-dom/client";
import { getFontEmbedCSS, toBlob } from "html-to-image";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ChevronDown,
  Copy,
  Eye,
  GripVertical,
  ImageIcon,
  Loader2,
  Pencil,
  Sparkles,
  Trash2,
} from "lucide-react";
import { AnimatePresence, motion, Reorder, useDragControls } from "framer-motion";
import { useTheme } from "next-themes";
import { toast } from "sonner";
import type { UploadImageContext } from "@/lib/api";
import {
  apiFetch,
  createBlok,
  deleteBlok,
  generujBlokiAI,
  reorderBloki,
  updateBlok,
  uploadImage,
} from "@/lib/api";
import { cn } from "@/lib/cn";
import { MathMarkdown } from "@/components/MathMarkdown";
import type { Blok, BlokTyp, Temat } from "@/lib/types";

type Props = {
  tematId: number;
  isAdmin: boolean;
  /** Dane z SSG — przy `!isAdmin` React Query nie odpala zapytania na starcie. */
  initialData: Temat;
  /** Wymagane do wgrywania obrazków (ścieżka w public/kursy-materialy). */
  materialyContext?: UploadImageContext;
};

const DEFAULT_TRESC: Record<BlokTyp, string> = {
  teoria: "Treść bloku teoretycznego (Markdown / LaTeX).",
  przyklad: "Treść przykładu.",
  uwaga: "Ważna uwaga.",
  zadanie: "Treść zadania.",
  wideo:
    "<!-- Wklej tutaj kod iframe z YouTube lub Vimeo (np. przycisk Udostępnij → Osadź). -->",
};

const ADD_ACTIONS: { typ: BlokTyp; label: string }[] = [
  { typ: "teoria", label: "Teoria" },
  { typ: "przyklad", label: "Przykład" },
  { typ: "uwaga", label: "Uwaga" },
  { typ: "zadanie", label: "Zadanie" },
  { typ: "wideo", label: "Wideo" },
];

function sortBloki(b: Blok[]): Blok[] {
  return [...b].sort((a, b) => a.kolejnosc - b.kolejnosc);
}

function sanitizeVideoEmbedHtml(html: string): string {
  const withoutScripts = html.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "");
  const iframeMatch = withoutScripts.match(/<iframe[\s\S]*?<\/iframe>/i);
  if (!iframeMatch) return "";

  // Keep only iframe embed; drop inline JS handlers.
  return iframeMatch[0].replace(/\son\w+="[^"]*"/gi, "");
}

function BlockIllustration({ url }: { url?: string | null }) {
  if (!url) return null;
  return (
    <img
      src={url}
      alt="Ilustracja do bloku"
      className="mx-auto mb-4 w-full max-w-lg rounded-2xl border border-slate-200 object-contain dark:border-slate-800"
    />
  );
}

function BlockInsertGap({
  onPick,
  disabled,
}: {
  onPick: (typ: BlokTyp) => void;
  disabled?: boolean;
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative flex items-center gap-3 py-2">
      <div className="h-px min-h-[1px] flex-1 bg-gradient-to-r from-transparent via-cyan-500/20 to-transparent" />
      <div className="relative shrink-0">
        <button
          type="button"
          disabled={disabled}
          onClick={() => setOpen((o) => !o)}
          className="rounded-full border border-slate-300 bg-white/95 px-2.5 py-0.5 text-sm font-medium text-slate-700 shadow-[0_0_12px_rgba(14,165,233,0.12)] transition hover:border-primary/50 hover:text-slate-900 disabled:opacity-40 dark:border-white/15 dark:bg-slate-950/90 dark:text-slate-300 dark:hover:text-white"
        >
          +
        </button>
        {open && (
          <div
            role="menu"
            className="absolute left-1/2 top-full z-30 mt-1 flex min-w-[10rem] -translate-x-1/2 flex-col gap-0.5 rounded-xl border border-slate-200 bg-white/95 p-1.5 shadow-xl backdrop-blur-md dark:border-white/10 dark:bg-slate-950/95"
          >
            {ADD_ACTIONS.map((a) => (
              <button
                key={a.typ}
                type="button"
                className="rounded-lg px-3 py-2 text-left text-xs font-medium text-slate-700 transition hover:bg-primary/15 hover:text-slate-900 dark:text-slate-200 dark:hover:text-white"
                onClick={() => {
                  onPick(a.typ);
                  setOpen(false);
                }}
              >
                {a.label}
              </button>
            ))}
          </div>
        )}
      </div>
      <div className="h-px min-h-[1px] flex-1 bg-gradient-to-l from-transparent via-cyan-500/20 to-transparent" />
    </div>
  );
}

function DraggableBlockChrome({
  blok,
  showTopGap,
  bottomInsertIndex,
  onInsertAt,
  insertBusy,
  children,
}: {
  blok: Blok;
  showTopGap: boolean;
  bottomInsertIndex: number;
  onInsertAt: (index: number, typ: BlokTyp) => void;
  insertBusy: boolean;
  children: React.ReactNode;
}) {
  const controls = useDragControls();

  return (
    <Reorder.Item
      value={blok}
      dragListener={false}
      dragControls={controls}
      className="list-none w-full"
    >
      {showTopGap && (
        <BlockInsertGap
          disabled={insertBusy}
          onPick={(typ) => onInsertAt(0, typ)}
        />
      )}
      <div className="flex gap-3">
        <button
          type="button"
          aria-label="Przeciągnij blok"
          className="mt-1 shrink-0 cursor-grab touch-none rounded-lg p-1.5 text-slate-500 transition hover:bg-slate-200 hover:text-slate-700 active:cursor-grabbing dark:hover:bg-white/5 dark:hover:text-slate-300"
          onPointerDown={(e) => controls.start(e)}
        >
          <GripVertical className="h-5 w-5" />
        </button>
        <div className="min-w-0 flex-1">{children}</div>
      </div>
      <BlockInsertGap
        disabled={insertBusy}
        onPick={(typ) => onInsertAt(bottomInsertIndex, typ)}
      />
    </Reorder.Item>
  );
}

/** Statyczny widok bloku do zrzutu PNG (bez Framer Motion); zadanie zawsze z pełną odpowiedzią i rozwiązaniem. */
function BlockSnapshotForExport({ blok: b }: { blok: Blok }) {
  const illustration =
    b.image_url ? (
      <img
        src={b.image_url}
        alt=""
        className="mb-4 w-full max-w-lg mx-auto rounded-2xl border border-slate-200 object-contain"
      />
    ) : null;

  if (b.typ === "teoria") {
    return (
      <div
        className="box-border w-[min(720px,92vw)] p-8 shadow-sm"
        style={{ backgroundColor: "#ffffff", color: "#0f172a" }}
      >
        {illustration}
        <MathMarkdown variant="light" exportSnapshot>
          {b.tresc}
        </MathMarkdown>
      </div>
    );
  }

  if (b.typ === "przyklad") {
    return (
      <div
        className="box-border w-[min(720px,92vw)] overflow-hidden rounded-2xl border p-8 shadow-sm"
        style={{
          borderColor: "#a5f3fc",
          background: "linear-gradient(to bottom right, #f0f9ff, #ffffff)",
          color: "#0f172a",
        }}
      >
        <div
          className="mb-3 text-xs font-bold uppercase tracking-widest"
          style={{ color: "#155e75" }}
        >
          Przykład
        </div>
        {illustration}
        <MathMarkdown variant="light" exportSnapshot>
          {b.tresc}
        </MathMarkdown>
      </div>
    );
  }

  if (b.typ === "uwaga") {
    return (
      <div
        className="box-border w-[min(720px,92vw)] rounded-2xl border-2 p-8 shadow-sm"
        style={{
          borderColor: "#fcd34d",
          backgroundColor: "#fffbeb",
          color: "#0f172a",
        }}
      >
        <div
          className="mb-3 text-xs font-bold uppercase tracking-widest"
          style={{ color: "#78350f" }}
        >
          Uwaga
        </div>
        {illustration}
        <MathMarkdown variant="light" exportSnapshot>
          {b.tresc}
        </MathMarkdown>
      </div>
    );
  }

  if (b.typ === "wideo") {
    const safeEmbedHtml = sanitizeVideoEmbedHtml(b.tresc);
    return (
      <div
        className="box-border w-[min(720px,92vw)] overflow-hidden rounded-2xl border p-6 shadow-sm"
        style={{ borderColor: "#e2e8f0", backgroundColor: "#ffffff" }}
      >
        <div
          className="mb-3 text-xs font-bold uppercase tracking-widest text-slate-500"
        >
          Wideo
        </div>
        <div
          className="relative aspect-video w-full overflow-hidden rounded-xl bg-slate-100 [&_iframe]:absolute [&_iframe]:inset-0 [&_iframe]:h-full [&_iframe]:w-full [&_iframe]:max-w-full [&_iframe]:border-0"
          dangerouslySetInnerHTML={{ __html: safeEmbedHtml }}
        />
      </div>
    );
  }

  return (
    <div
      className="box-border w-[min(720px,92vw)] overflow-hidden rounded-2xl border shadow-sm"
      style={{ borderColor: "#e2e8f0", backgroundColor: "#ffffff", color: "#0f172a" }}
    >
      <div
        className="border-b px-6 py-6 md:px-8"
        style={{ borderColor: "#f1f5f9" }}
      >
        {illustration}
        <MathMarkdown variant="light" exportSnapshot>
          {b.tresc}
        </MathMarkdown>
        {b.odpowiedz ? (
          <div
            className="mt-4 rounded-xl border px-4 py-3"
            style={{
              borderColor: "#6ee7b7",
              backgroundColor: "#ecfdf5",
            }}
          >
            <div
              className="mb-2 text-xs font-bold uppercase tracking-wide"
              style={{ color: "#064e3b" }}
            >
              Odpowiedź
            </div>
            <MathMarkdown variant="light" exportSnapshot>
              {b.odpowiedz}
            </MathMarkdown>
          </div>
        ) : null}
      </div>
      <div className="px-6 pb-6 pt-2 md:px-8">
        <div
          className="rounded-xl border p-4"
          style={{
            borderColor: "#c4b5fd",
            backgroundColor: "#f5f3ff",
          }}
        >
          <div
            className="mb-2 text-xs font-bold uppercase tracking-wide"
            style={{ color: "#4c1d95" }}
          >
            Rozwiązanie
          </div>
          <MathMarkdown variant="light" exportSnapshot>
            {b.rozwiazanie?.trim() ? b.rozwiazanie : "_Brak rozwiązania._"}
          </MathMarkdown>
        </div>
      </div>
    </div>
  );
}

async function copyBlockAsImage(blok: Blok) {
  const tid = toast.loading("Tworzenie obrazu…");
  const host = document.createElement("div");
  host.setAttribute("aria-hidden", "true");
  host.style.cssText =
    "position:fixed;left:-10000px;top:0;width:800px;z-index:0;pointer-events:none;overflow:visible;";
  document.body.appendChild(host);
  let root: Root | null = null;
  try {
    root = createRoot(host);
    root.render(<BlockSnapshotForExport blok={blok} />);
    await document.fonts.ready;
    await new Promise<void>((resolve) => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          setTimeout(resolve, 420);
        });
      });
    });
    const target = host.firstElementChild as HTMLElement | null;
    if (!target) throw new Error("Brak treści do zrzutu.");

    // KaTeX: osadź @font-face w SVG, inaczej wzory „rozsypują się” (fonty nie ładują się w zrzucie).
    let fontEmbedCSS: string | undefined;
    try {
      fontEmbedCSS = await getFontEmbedCSS(target);
    } catch {
      fontEmbedCSS = undefined;
    }

    const blob = await toBlob(target, {
      backgroundColor: "#ffffff",
      pixelRatio: 2,
      cacheBust: true,
      ...(fontEmbedCSS ? { fontEmbedCSS } : {}),
    });
    if (!blob) throw new Error("Nie udało się utworzyć obrazu PNG.");

    if (
      typeof ClipboardItem === "undefined" ||
      !navigator.clipboard?.write
    ) {
      throw new Error(
        "Ta przeglądarka nie obsługuje kopiowania obrazów do schowka (Clipboard API)."
      );
    }

    await navigator.clipboard.write([
      new ClipboardItem({ "image/png": blob }),
    ]);
    toast.success("Skopiowano obraz do schowka", { id: tid });
  } catch (e) {
    toast.error(e instanceof Error ? e.message : "Błąd kopiowania.", {
      id: tid,
    });
  } finally {
    root?.unmount();
    host.remove();
  }
}

export function TematLessonView({
  tematId,
  isAdmin,
  initialData,
  materialyContext,
}: Props) {
  const { resolvedTheme } = useTheme();
  const markdownVariant = resolvedTheme === "dark" ? "dark" : "light";
  const queryClient = useQueryClient();
  const [ordered, setOrdered] = useState<Blok[]>([]);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draftTresc, setDraftTresc] = useState("");
  const [draftOdp, setDraftOdp] = useState("");
  const [draftRozw, setDraftRozw] = useState("");
  const [draftImageUrl, setDraftImageUrl] = useState<string | null>(null);
  const [imageUploading, setImageUploading] = useState(false);
  const [insertBusy, setInsertBusy] = useState(false);
  const imageInputRef = useRef<HTMLInputElement>(null);
  const uploadBlokIdRef = useRef<number | null>(null);
  const [savingEdit, setSavingEdit] = useState(false);
  const [openAnswers, setOpenAnswers] = useState<Record<number, boolean>>({});
  const [openSolutions, setOpenSolutions] = useState<Record<number, boolean>>(
    {}
  );
  const [aiLoading, setAiLoading] = useState(false);

  const { data: temat, isLoading, refetch } = useQuery({
    queryKey: ["temat", tematId],
    queryFn: () => apiFetch<Temat>(`/tematy/${tematId}`),
    enabled: Number.isFinite(tematId),
    initialData,
    staleTime: isAdmin ? 0 : Infinity,
    refetchOnMount: isAdmin,
    refetchOnWindowFocus: isAdmin,
  });

  useEffect(() => {
    if (temat?.bloki) {
      setOrdered(sortBloki(temat.bloki));
    } else {
      setOrdered([]);
    }
  }, [temat]);

  const invalidate = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["temat", tematId] });
  }, [queryClient, tematId]);

  const onReorder = async (next: Blok[]) => {
    const prev = ordered;
    setOrdered(next);
    try {
      await reorderBloki(
        tematId,
        next.map((b) => b.id)
      );
      toast.success("Kolejność zapisana.");
      invalidate();
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Nie udało się zapisać.");
      setOrdered(prev);
    }
  };

  const addBlokAtIndex = useCallback(
    async (index: number, typ: BlokTyp) => {
      setInsertBusy(true);
      try {
        const created = await createBlok(tematId, {
          typ,
          tresc: DEFAULT_TRESC[typ],
        });
        const ids = ordered.map((b) => b.id);
        ids.splice(index, 0, created.id);
        await reorderBloki(tematId, ids);
        toast.success("Dodano blok.");
        invalidate();
        await refetch();
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Błąd dodawania.");
      } finally {
        setInsertBusy(false);
      }
    },
    [invalidate, ordered, refetch, tematId]
  );

  const startEdit = (b: Blok) => {
    setEditingId(b.id);
    setDraftTresc(b.tresc);
    setDraftOdp(b.odpowiedz ?? "");
    setDraftRozw(b.rozwiazanie ?? "");
    setDraftImageUrl(b.image_url ?? null);
  };

  const triggerImagePick = (blokId: number) => {
    if (!materialyContext) {
      toast.error("Brak kontekstu kursu — odśwież stronę.");
      return;
    }
    uploadBlokIdRef.current = blokId;
    imageInputRef.current?.click();
  };

  const onPickImage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    const blokId = uploadBlokIdRef.current ?? editingId;
    uploadBlokIdRef.current = null;
    if (!file || blokId == null || !materialyContext) return;
    setImageUploading(true);
    try {
      const { image_url } = await uploadImage(file, materialyContext);
      await updateBlok(blokId, { image_url });
      if (editingId === blokId) setDraftImageUrl(image_url);
      toast.success("Obrazek zapisany.");
      invalidate();
      await refetch();
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Nie udało się wgrać obrazka."
      );
    } finally {
      setImageUploading(false);
    }
  };

  const removeBlockImage = async () => {
    if (editingId == null) return;
    try {
      await updateBlok(editingId, { image_url: null });
      setDraftImageUrl(null);
      toast.success("Obrazek usunięty.");
      invalidate();
      await refetch();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Błąd.");
    }
  };

  const saveEdit = async () => {
    if (editingId == null) return;
    setSavingEdit(true);
    try {
      await updateBlok(editingId, {
        tresc: draftTresc,
        odpowiedz: draftOdp.trim() || null,
        rozwiazanie: draftRozw.trim() || null,
      });
      toast.success("Zapisano.");
      setEditingId(null);
      invalidate();
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Błąd zapisu.");
    } finally {
      setSavingEdit(false);
    }
  };

  const onDelete = async (b: Blok) => {
    if (!window.confirm("Usunąć ten blok?")) return;
    try {
      await deleteBlok(b.id);
      toast.success("Blok usunięty.");
      invalidate();
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Błąd.");
    }
  };

  const addBlok = async (typ: BlokTyp) => {
    try {
      await createBlok(tematId, {
        typ,
        tresc: DEFAULT_TRESC[typ],
      });
      toast.success("Dodano blok.");
      invalidate();
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Błąd.");
    }
  };

  const onGenerujAi = async () => {
    if (
      !window.confirm(
        "Wygenerować całą lekcję przez AI? Obecne bloki zostaną zastąpione."
      )
    ) {
      return;
    }
    const tid = toast.loading("Generowanie lekcji…");
    setAiLoading(true);
    try {
      await generujBlokiAI(tematId);
      toast.success("Lekcja wygenerowana.", { id: tid });
      invalidate();
      await refetch();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Błąd AI.", { id: tid });
    } finally {
      setAiLoading(false);
    }
  };

  const toggleAns = (id: number) =>
    setOpenAnswers((p) => ({ ...p, [id]: !p[id] }));
  const toggleSol = (id: number) =>
    setOpenSolutions((p) => ({ ...p, [id]: !p[id] }));

  if (!Number.isFinite(tematId)) return null;

  if (isLoading || !temat) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
      </div>
    );
  }

  function renderBlockInner(
    b: Blok,
    opts: { showAdminChrome: boolean }
  ) {
    const isEdit = editingId === b.id;
    const { showAdminChrome } = opts;

    const blockToolbar = !isEdit && (
      <div className="absolute right-2 top-2 z-20 flex flex-row-reverse items-center gap-0.5">
        <button
          type="button"
          title="Kopiuj jako obraz na tablicę (wklej w Miro: Ctrl+V)"
          onClick={(e) => {
            e.stopPropagation();
            void copyBlockAsImage(b);
          }}
          className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-200 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-white"
        >
          <Copy className="h-4 w-4" />
        </button>
        {showAdminChrome ? (
          <>
            <button
              type="button"
              title="Edytuj treść"
              onClick={(e) => {
                e.stopPropagation();
                startEdit(b);
              }}
              className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-200 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-white"
            >
              <Pencil className="h-4 w-4" />
            </button>
            {b.typ !== "wideo" ? (
              <button
                type="button"
                title="Dodaj zdjęcie"
                disabled={imageUploading}
                onClick={(e) => {
                  e.stopPropagation();
                  triggerImagePick(b.id);
                }}
                className="rounded-lg p-2 text-slate-500 transition hover:bg-primary/15 hover:text-primary disabled:opacity-50"
              >
                {imageUploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ImageIcon className="h-4 w-4" />
                )}
              </button>
            ) : null}
            <button
              type="button"
              title="Usuń blok"
              onClick={(e) => {
                e.stopPropagation();
                void onDelete(b);
              }}
              className="rounded-lg p-2 text-slate-500 transition hover:bg-rose-500/15 hover:text-rose-200"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          </>
        ) : null}
      </div>
    );

    if (isEdit) {
      return (
        <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white/90 p-5 dark:border-white/10 dark:bg-slate-900/80">
          {b.typ === "wideo" ? (
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Wklej poniżej kod osadzenia (iframe) z YouTube lub Vimeo.
            </p>
          ) : null}
          <textarea
            value={draftTresc}
            onChange={(e) => setDraftTresc(e.target.value)}
            rows={b.typ === "wideo" ? 12 : 8}
            placeholder={
              b.typ === "wideo"
                ? 'np. <iframe width="560" height="315" src="https://www.youtube.com/embed/..." ...></iframe>'
                : undefined
            }
            className="mt-2 w-full resize-y rounded-xl border border-slate-300 bg-white px-3 py-2 font-mono text-sm text-slate-900 dark:border-white/10 dark:bg-slate-950 dark:text-slate-100"
          />
          <input
            ref={imageInputRef}
            type="file"
            accept="image/*"
            className="sr-only"
            aria-hidden
            tabIndex={-1}
            onChange={onPickImage}
          />
          {b.typ !== "wideo" ? (
            <div className="mt-4 space-y-3">
              <button
                type="button"
                disabled={imageUploading}
                onClick={() => {
                  if (!materialyContext) {
                    toast.error("Brak kontekstu kursu.");
                    return;
                  }
                  uploadBlokIdRef.current = editingId;
                  imageInputRef.current?.click();
                }}
                className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-primary/40 hover:text-slate-900 disabled:opacity-50 dark:border-white/15 dark:bg-white/[0.04] dark:text-slate-200 dark:hover:text-white"
              >
                {imageUploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <ImageIcon className="h-4 w-4 text-primary" />
                )}
                Dodaj obrazek
              </button>
              {draftImageUrl ? (
                <div className="relative inline-block max-w-full">
                  <button
                    type="button"
                    title="Usuń obrazek"
                    onClick={removeBlockImage}
                    className="absolute right-2 top-2 z-10 rounded-lg border border-slate-200 bg-white/95 p-1.5 text-rose-500 shadow-lg transition hover:bg-rose-100 hover:text-rose-700 dark:border-white/10 dark:bg-slate-950/90 dark:text-rose-300 dark:hover:bg-rose-500/20 dark:hover:text-rose-100"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                  <img
                    src={draftImageUrl}
                    alt=""
                    className="max-h-48 max-w-full rounded-2xl border border-slate-300 object-contain dark:border-slate-700"
                  />
                </div>
              ) : null}
            </div>
          ) : null}
          {b.typ === "zadanie" && (
            <>
              <input
                value={draftOdp}
                onChange={(e) => setDraftOdp(e.target.value)}
                placeholder="Odpowiedź"
                className="mt-3 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-white/10 dark:bg-slate-950 dark:text-white"
              />
              <textarea
                value={draftRozw}
                onChange={(e) => setDraftRozw(e.target.value)}
                placeholder="Rozwiązanie"
                rows={4}
                className="mt-2 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 dark:border-white/10 dark:bg-slate-950 dark:text-white"
              />
            </>
          )}
          <div className="mt-3 flex gap-2">
            <button
              type="button"
              onClick={saveEdit}
              disabled={savingEdit}
              className="rounded-xl bg-gradient-to-r from-primary to-secondary px-4 py-2 text-sm font-semibold text-white"
            >
              {savingEdit ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Zapisz"
              )}
            </button>
            <button
              type="button"
              onClick={() => setEditingId(null)}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm text-slate-600 dark:border-white/10 dark:text-slate-400"
            >
              Anuluj
            </button>
          </div>
        </div>
      );
    }

    if (b.typ === "wideo") {
      const safeEmbedHtml = sanitizeVideoEmbedHtml(b.tresc);
      return (
        <div className="relative w-full max-w-full rounded-2xl border border-slate-200 bg-white/90 p-4 md:p-6 dark:border-white/[0.08] dark:bg-slate-950/50">
          {blockToolbar}
          <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-slate-600 dark:text-slate-400">
            <span aria-hidden>▶</span>
            Wideo
          </div>
          <div
            className="relative aspect-video w-full max-w-full overflow-hidden rounded-2xl bg-black/30 shadow-[0_0_32px_rgba(0,0,0,0.25)] [&_iframe]:absolute [&_iframe]:inset-0 [&_iframe]:h-full [&_iframe]:w-full [&_iframe]:max-w-full [&_iframe]:border-0"
            dangerouslySetInnerHTML={{ __html: safeEmbedHtml }}
          />
        </div>
      );
    }

    if (b.typ === "teoria") {
      return (
        <div className="relative rounded-2xl bg-white/90 p-6 md:p-8 dark:bg-slate-950/50">
          {blockToolbar}
          <BlockIllustration url={b.image_url} />
          <MathMarkdown variant={markdownVariant}>{b.tresc}</MathMarkdown>
        </div>
      );
    }

    if (b.typ === "przyklad") {
      return (
        <div className="relative overflow-hidden rounded-2xl border border-primary/25 bg-white/90 p-6 shadow-[0_0_40px_rgba(168,85,247,0.12)] md:p-8 dark:border-primary/20 dark:bg-slate-950/40">
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-br from-sky-300/30 via-blue-200/20 to-transparent blur-2xl dark:from-sky-600/15 dark:via-blue-600/10"
            aria-hidden
          />
          {blockToolbar}
          <div className="relative">
            <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-cyan-700 dark:text-cyan-300/95">
              <span aria-hidden>💡</span>
              Przykład
            </div>
            <BlockIllustration url={b.image_url} />
            <MathMarkdown variant={markdownVariant}>{b.tresc}</MathMarkdown>
          </div>
        </div>
      );
    }

    if (b.typ === "uwaga") {
      return (
        <div className="relative">
          {blockToolbar}
          <div
            className={cn(
              "rounded-2xl border-2 border-amber-400/60 bg-amber-100/80 p-6 md:p-8 dark:border-amber-400/50 dark:bg-amber-950/15",
              "shadow-[0_0_28px_rgba(251,191,36,0.18)]"
            )}
          >
            <div className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-amber-800 dark:text-amber-200/95">
              <span aria-hidden>⚠️</span>
              Uwaga
            </div>
            <BlockIllustration url={b.image_url} />
            <MathMarkdown variant={markdownVariant}>{b.tresc}</MathMarkdown>
          </div>
        </div>
      );
    }

    return (
      <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-gradient-to-br from-white to-slate-100 dark:border-white/[0.08] dark:from-slate-900/90 dark:to-slate-950/95">
        {blockToolbar}
        <div className="border-b border-slate-200 px-5 py-5 md:px-7 dark:border-white/[0.06]">
          <BlockIllustration url={b.image_url} />
          <MathMarkdown variant={markdownVariant}>{b.tresc}</MathMarkdown>
          {b.odpowiedz ? (
            <div className="mt-4">
              <button
                type="button"
                onClick={() => toggleAns(b.id)}
                className="flex w-full items-center justify-between gap-3 rounded-xl border border-secondary/30 bg-secondary/10 px-4 py-3 text-left text-sm font-semibold text-slate-800 dark:bg-secondary/5 dark:text-slate-200"
              >
                <span className="flex items-center gap-2">
                  <Eye className="h-5 w-5 text-secondary" />
                  Pokaż odpowiedź
                </span>
                <motion.span
                  animate={{ rotate: openAnswers[b.id] ? 180 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <ChevronDown className="h-5 w-5 text-slate-500 dark:text-slate-400" />
                </motion.span>
              </button>
              <AnimatePresence initial={false}>
                {openAnswers[b.id] && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-3 rounded-xl border border-secondary/25 bg-secondary/5 px-4 py-3">
                      <MathMarkdown variant={markdownVariant}>{b.odpowiedz}</MathMarkdown>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : null}
        </div>
        <div className="px-5 pb-5 pt-2 md:px-7">
          <button
            type="button"
            onClick={() => toggleSol(b.id)}
            className="flex w-full items-center justify-between gap-3 rounded-xl border border-primary/35 bg-gradient-to-r from-primary/15 to-secondary/10 px-4 py-3 text-sm font-semibold text-slate-900 dark:text-white"
          >
            <span className="flex items-center gap-2">
              <Eye className="h-5 w-5 text-primary" />
              Pokaż rozwiązanie
            </span>
            <motion.span
              animate={{ rotate: openSolutions[b.id] ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="h-5 w-5 text-slate-500 dark:text-slate-400" />
            </motion.span>
          </button>
          <AnimatePresence initial={false}>
            {openSolutions[b.id] && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="mt-4 rounded-xl border border-primary/20 bg-white/80 p-4 dark:bg-slate-950/60">
                  <MathMarkdown variant={markdownVariant}>
                    {b.rozwiazanie?.trim()
                      ? b.rozwiazanie
                      : "_Brak rozwiązania._"}
                  </MathMarkdown>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <input
        ref={imageInputRef}
        type="file"
        accept="image/*"
        className="sr-only"
        aria-hidden
        tabIndex={-1}
        onChange={onPickImage}
      />

      {isAdmin && (
        <div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-center">
          <div className="flex flex-wrap gap-2">
            {ADD_ACTIONS.map((a) => (
              <button
                key={a.typ}
                type="button"
                onClick={() => addBlok(a.typ)}
                className="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 transition hover:border-primary/40 hover:text-slate-900 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300 dark:hover:text-white"
              >
                + {a.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={onGenerujAi}
            disabled={aiLoading}
            className="inline-flex items-center gap-2 rounded-2xl border border-secondary/40 bg-gradient-to-r from-secondary/25 via-primary/20 to-primary/30 px-5 py-2.5 text-sm font-bold text-slate-900 dark:text-white disabled:opacity-50"
          >
            {aiLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Sparkles className="h-4 w-4 text-amber-200" />
            )}
            Generuj lekcję (AI)
          </button>
        </div>
      )}

      {ordered.length === 0 && (
        <p className="rounded-2xl border border-dashed border-slate-300 bg-white/70 py-16 text-center text-slate-600 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-500">
          Brak treści w tej lekcji.
          {isAdmin && " Dodaj blok lub wygeneruj AI."}
        </p>
      )}

      {isAdmin && ordered.length === 0 && (
        <BlockInsertGap
          disabled={insertBusy}
          onPick={(typ) => addBlokAtIndex(0, typ)}
        />
      )}

      {isAdmin ? (
        <Reorder.Group
          axis="y"
          values={ordered}
          onReorder={onReorder}
          className="flex flex-col gap-0"
        >
          {ordered.map((b, i) => (
            <DraggableBlockChrome
              key={b.id}
              blok={b}
              showTopGap={i === 0}
              bottomInsertIndex={i + 1}
              onInsertAt={addBlokAtIndex}
              insertBusy={insertBusy}
            >
              {renderBlockInner(b, { showAdminChrome: true })}
            </DraggableBlockChrome>
          ))}
        </Reorder.Group>
      ) : (
        <div className="flex flex-col gap-6">
          {sortBloki(ordered).map((b) => (
            <div key={b.id}>{renderBlockInner(b, { showAdminChrome: false })}</div>
          ))}
        </div>
      )}
    </div>
  );
}
