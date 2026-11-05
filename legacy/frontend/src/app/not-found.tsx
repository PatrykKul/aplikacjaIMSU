import Link from "next/link";

export default function NotFound() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 px-4 py-24 text-center">
      <p className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-6xl font-extrabold text-transparent">
        404
      </p>
      <h1 className="text-xl font-semibold text-slate-900 dark:text-white">Nie ma takiej strony</h1>
      <p className="max-w-md text-sm text-slate-600 dark:text-slate-400">
        Adres jest nieprawidłowy albo strona została usunięta.
      </p>
      <Link
        href="/"
        className="rounded-xl bg-gradient-to-r from-primary to-secondary px-5 py-2.5 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95"
      >
        Wróć na stronę główną
      </Link>
    </main>
  );
}
