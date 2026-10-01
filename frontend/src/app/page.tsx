import Link from "next/link";
import { Ear, Eye, GraduationCap, Hand } from "lucide-react";

const STYLE = [
  {
    icon: Eye,
    nazwa: "Wzrokowiec (V)",
    opis: "Obrazy, diagramy i wideo — materiał, który można zobaczyć.",
  },
  {
    icon: Ear,
    nazwa: "Słuchowiec (A)",
    opis: "Nagrania i omówienia — materiał, którego można posłuchać.",
  },
  {
    icon: Hand,
    nazwa: "Kinestetyk (K)",
    opis: "Ćwiczenia i quizy — materiał, który można zrobić samemu.",
  },
];

export default function HomePage() {
  return (
    <main className="relative flex min-h-screen flex-1 flex-col items-center justify-center px-4 py-16 text-slate-900 dark:text-slate-100">
      <div className="mx-auto max-w-4xl text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 to-secondary/20 shadow-neon-sm ring-1 ring-white/12">
          <GraduationCap className="h-9 w-9 text-primary" aria-hidden />
        </div>
        <h1 className="mb-4 bg-gradient-to-r from-primary via-cyan-200 to-secondary bg-clip-text text-5xl font-extrabold tracking-tight text-transparent md:text-6xl">
          StylNauki
        </h1>
        <p className="mx-auto mb-10 max-w-2xl text-lg text-slate-600 md:text-xl dark:text-slate-400">
          Platforma z kursami, która dopasowuje sposób podania materiału do Twojego stylu uczenia się.
        </p>

        <div className="mb-10 grid gap-4 text-left md:grid-cols-3">
          {STYLE.map(({ icon: Icon, nazwa, opis }) => (
            <div
              key={nazwa}
              className="rounded-2xl border border-slate-200 bg-white/80 p-5 shadow-sm dark:border-white/10 dark:bg-slate-900/60"
            >
              <Icon className="mb-3 h-6 w-6 text-primary" aria-hidden />
              <h2 className="mb-1 font-semibold">{nazwa}</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400">{opis}</p>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap items-center justify-center gap-3">
          <Link
            href="/rejestracja"
            className="inline-flex items-center rounded-xl bg-primary px-6 py-3 font-semibold text-primary-foreground shadow-neon-sm transition hover:opacity-90"
          >
            Załóż konto
          </Link>
          <Link
            href="/logowanie"
            className="inline-flex items-center rounded-xl border border-slate-300 bg-white/80 px-6 py-3 font-semibold text-slate-800 transition hover:border-primary/50 dark:border-white/15 dark:bg-white/[0.04] dark:text-slate-100"
          >
            Zaloguj się
          </Link>
        </div>
      </div>
    </main>
  );
}
