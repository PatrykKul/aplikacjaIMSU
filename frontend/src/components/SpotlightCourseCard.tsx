"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import type { ReactNode } from "react";
import { ArrowRight, GraduationCap, Pencil, Trash2 } from "lucide-react";
import { motion } from "framer-motion";
import type { Kurs } from "@/lib/types";

type Props = {
  kurs: Kurs;
  index: number;
  isAdmin?: boolean;
  onEdit?: (kurs: Kurs) => void;
  onDelete?: (kurs: Kurs) => void;
  dragHandle?: ReactNode;
  className?: string;
};

export function SpotlightCourseCard({
  kurs,
  index,
  isAdmin,
  onEdit,
  onDelete,
  dragHandle,
  className,
}: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const [glow, setGlow] = useState({ x: 50, y: 50 });

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    setGlow({
      x: ((e.clientX - r.left) / r.width) * 100,
      y: ((e.clientY - r.top) / r.height) * 100,
    });
  };

  const onLeave = () => setGlow({ x: 50, y: 50 });

  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08 }}
      className={className ?? "relative w-full"}
    >
      <Link href={`/kursy/${kurs.id}`} className="block w-full">
        <div
          ref={ref}
          onMouseMove={onMove}
          onMouseLeave={onLeave}
          className="group relative h-64 w-full overflow-hidden rounded-3xl border border-slate-200 bg-white/95 transition hover:border-slate-300 hover:bg-slate-50 dark:border-white/[0.08] dark:bg-slate-900/40 dark:hover:border-primary/35"
        >
          <div
            className="pointer-events-none absolute inset-0 hidden opacity-60 transition-opacity group-hover:opacity-100 dark:block"
            style={{
              background: `radial-gradient(520px circle at ${glow.x}% ${glow.y}%, rgba(168,85,247,0.18), transparent 45%)`,
            }}
          />
          <div className="pointer-events-none absolute -right-16 top-1/2 hidden h-72 w-72 -translate-y-1/2 rounded-full bg-primary/35 blur-[80px] dark:block" />
          <div className="pointer-events-none absolute bottom-0 right-0 hidden h-40 w-64 rounded-full bg-secondary/20 blur-[60px] dark:block" />

          <div className="relative z-10 flex h-full flex-col justify-between p-8 md:flex-row md:items-center md:gap-8 md:p-10">
            {dragHandle ? <div className="absolute left-4 top-4 z-20">{dragHandle}</div> : null}
            <div className="flex min-w-0 flex-1 items-start gap-5">
              <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-slate-100 ring-1 ring-slate-200 dark:bg-gradient-to-br dark:from-slate-700/70 dark:to-slate-800/80 dark:ring-white/10">
                <GraduationCap className="h-8 w-8 text-primary dark:text-slate-300" />
              </div>
              <div className="min-w-0">
                <h2 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl lg:text-4xl dark:text-white">
                  {kurs.nazwa}
                </h2>
                <p className="mt-3 line-clamp-2 max-w-2xl text-base leading-relaxed text-slate-600 md:text-lg dark:text-slate-400">
                  {kurs.opis}
                </p>
              </div>
            </div>
            <div className="flex shrink-0 items-center gap-2 self-end font-semibold text-primary md:self-center">
              <span className="text-sm uppercase tracking-wider opacity-80 transition group-hover:opacity-100">
                Otwórz kurs
              </span>
              <ArrowRight className="h-5 w-5 transition group-hover:translate-x-1" />
            </div>
          </div>
        </div>
      </Link>

      {isAdmin && (onEdit || onDelete) && (
        <div
          className="pointer-events-none absolute right-4 top-4 z-20 flex gap-1"
          aria-hidden={false}
        >
          {onEdit && (
            <button
              type="button"
              title="Edytuj kurs"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onEdit(kurs);
              }}
              className="pointer-events-auto rounded-lg p-2 text-slate-500 transition hover:bg-slate-200 hover:text-slate-900 dark:hover:bg-white/10 dark:hover:text-white"
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              title="Usuń kurs"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete(kurs);
              }}
              className="pointer-events-auto rounded-lg p-2 text-slate-500 transition hover:bg-rose-500/15 hover:text-rose-200"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </motion.div>
  );
}
