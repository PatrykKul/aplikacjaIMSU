"use client";

import { Loader2, X } from "lucide-react";
import { motion } from "framer-motion";

type Props = {
  open: boolean;
  title: string;
  submitLabel: string;
  nazwa: string;
  opis: string;
  isPublished: boolean;
  onNazwaChange: (v: string) => void;
  onOpisChange: (v: string) => void;
  onIsPublishedChange: (v: boolean) => void;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  submitting: boolean;
};

export function KursModal({
  open,
  title,
  submitLabel,
  nazwa,
  opis,
  isPublished,
  onNazwaChange,
  onOpisChange,
  onIsPublishedChange,
  onClose,
  onSubmit,
  submitting,
}: Props) {
  if (!open) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.96, y: 12 }}
        animate={{ scale: 1, y: 0 }}
        className="relative w-full max-w-md rounded-2xl border border-white/[0.1] bg-slate-900 p-6 shadow-2xl"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1 text-slate-500 transition hover:bg-white/[0.06] hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>
        <h3 className="mb-6 text-xl font-bold text-white">{title}</h3>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm text-slate-400">Nazwa</label>
            <input
              required
              value={nazwa}
              onChange={(e) => onNazwaChange(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-slate-950 px-4 py-2.5 text-white outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/40"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-slate-400">Opis</label>
            <textarea
              required
              value={opis}
              onChange={(e) => onOpisChange(e.target.value)}
              rows={4}
              className="w-full resize-none rounded-xl border border-white/10 bg-slate-950 px-4 py-2.5 text-white outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/40"
            />
          </div>
          <label className="flex items-center justify-between gap-3 rounded-xl border border-white/10 bg-slate-950 px-4 py-3">
            <span className="text-sm text-slate-300">Opublikowany (widoczny na produkcji)</span>
            <input
              type="checkbox"
              checked={isPublished}
              onChange={(e) => onIsPublishedChange(e.target.checked)}
              className="h-4 w-4 accent-primary"
            />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary py-3 font-semibold text-white disabled:opacity-50"
          >
            {submitting ? <Loader2 className="h-5 w-5 animate-spin" /> : submitLabel}
          </button>
        </form>
      </motion.div>
    </motion.div>
  );
}
