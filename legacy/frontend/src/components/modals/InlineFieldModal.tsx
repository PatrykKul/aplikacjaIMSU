"use client";

import { Loader2, X } from "lucide-react";
import { motion } from "framer-motion";

type Props = {
  open: boolean;
  title: string;
  label: string;
  value: string;
  onChange: (v: string) => void;
  onClose: () => void;
  onSubmit: (e: React.FormEvent) => void;
  submitting: boolean;
  submitLabel?: string;
  placeholder?: string;
};

export function InlineFieldModal({
  open,
  title,
  label,
  value,
  onChange,
  onClose,
  onSubmit,
  submitting,
  submitLabel = "Zapisz",
  placeholder,
}: Props) {
  if (!open) return null;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm"
    >
      <motion.div
        initial={{ scale: 0.96 }}
        animate={{ scale: 1 }}
        className="relative w-full max-w-md rounded-2xl border border-white/[0.1] bg-slate-900 p-6 shadow-2xl"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 text-slate-500 hover:text-white"
        >
          <X className="h-5 w-5" />
        </button>
        <h3 className="mb-4 text-lg font-bold text-white">{title}</h3>
        <form onSubmit={onSubmit} className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm text-slate-400">{label}</label>
            <input
              required
              value={value}
              onChange={(e) => onChange(e.target.value)}
              placeholder={placeholder}
              className="w-full rounded-xl border border-white/10 bg-slate-950 px-4 py-2.5 text-white outline-none focus:border-primary/50"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-gradient-to-r from-primary to-secondary py-2.5 font-semibold text-white disabled:opacity-50"
          >
            {submitting ? <Loader2 className="mx-auto h-5 w-5 animate-spin" /> : submitLabel}
          </button>
        </form>
      </motion.div>
    </motion.div>
  );
}
