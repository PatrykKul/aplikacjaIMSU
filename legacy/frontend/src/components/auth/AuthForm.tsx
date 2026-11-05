"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { GraduationCap, Loader2 } from "lucide-react";
import { login, register } from "@/lib/api";
import { homeFor } from "@/components/auth/AuthGate";
import { useAuthStore } from "@/store/useAuthStore";

type Props = { mode: "logowanie" | "rejestracja" };

const INPUT_CLASS =
  "w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/25 dark:border-white/10 dark:bg-slate-950 dark:text-slate-100";

export function AuthForm({ mode }: Props) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const setSession = useAuthStore((s) => s.setSession);
  const [email, setEmail] = useState("");
  const [imie, setImie] = useState("");
  const [haslo, setHaslo] = useState("");
  const [haslo2, setHaslo2] = useState("");
  const [blad, setBlad] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const isRegister = mode === "rejestracja";

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBlad(null);
    if (isRegister && haslo.length < 8) {
      setBlad("Hasło musi mieć co najmniej 8 znaków.");
      return;
    }
    if (isRegister && haslo !== haslo2) {
      setBlad("Hasła nie są takie same.");
      return;
    }
    setBusy(true);
    try {
      const res = isRegister
        ? await register({ email, imie, haslo })
        : await login({ email, haslo });
      queryClient.clear();
      setSession(res.access_token, res.uzytkownik);
      router.replace(homeFor(res.uzytkownik));
    } catch (err) {
      setBlad(err instanceof Error ? err.message : "Coś poszło nie tak. Spróbuj ponownie.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="flex flex-1 items-center justify-center px-4 py-12">
      <div className="w-full max-w-md rounded-3xl border border-slate-200 bg-white/90 p-8 shadow-xl backdrop-blur dark:border-white/10 dark:bg-slate-900/80">
        <Link href="/" className="mb-6 flex items-center justify-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/25 to-secondary/20 ring-1 ring-primary/20">
            <GraduationCap className="h-6 w-6 text-primary" aria-hidden />
          </span>
          <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-2xl font-bold tracking-tight text-transparent">
            StylNauki
          </span>
        </Link>
        <h1 className="mb-1 text-center text-xl font-semibold text-slate-900 dark:text-white">
          {isRegister ? "Załóż konto" : "Zaloguj się"}
        </h1>
        <p className="mb-6 text-center text-sm text-slate-600 dark:text-slate-400">
          {isRegister
            ? "Po rejestracji wypełnisz krótką ankietę o stylu uczenia się."
            : "Wróć do swoich kursów."}
        </p>

        <form onSubmit={onSubmit} className="space-y-4" noValidate>
          {isRegister && (
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Imię
              <input
                className={`${INPUT_CLASS} mt-1`}
                value={imie}
                onChange={(e) => setImie(e.target.value)}
                autoComplete="given-name"
                maxLength={80}
                required
              />
            </label>
          )}
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            E-mail
            <input
              className={`${INPUT_CLASS} mt-1`}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </label>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
            Hasło
            <input
              className={`${INPUT_CLASS} mt-1`}
              type="password"
              value={haslo}
              onChange={(e) => setHaslo(e.target.value)}
              autoComplete={isRegister ? "new-password" : "current-password"}
              maxLength={72}
              required
            />
          </label>
          {isRegister && (
            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300">
              Powtórz hasło
              <input
                className={`${INPUT_CLASS} mt-1`}
                type="password"
                value={haslo2}
                onChange={(e) => setHaslo2(e.target.value)}
                autoComplete="new-password"
                maxLength={72}
                required
              />
            </label>
          )}

          {blad && (
            <p role="alert" className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-500/40 dark:bg-rose-950/40 dark:text-rose-200">
              {blad}
            </p>
          )}

          <button
            type="submit"
            disabled={busy}
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-4 py-2.5 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95 disabled:opacity-60"
          >
            {busy && <Loader2 className="h-4 w-4 animate-spin" aria-hidden />}
            {isRegister ? "Zarejestruj się" : "Zaloguj się"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
          {isRegister ? "Masz już konto? " : "Nie masz konta? "}
          <Link
            href={isRegister ? "/logowanie" : "/rejestracja"}
            className="font-semibold text-primary hover:underline"
          >
            {isRegister ? "Zaloguj się" : "Zarejestruj się"}
          </Link>
        </p>
      </div>
    </main>
  );
}
