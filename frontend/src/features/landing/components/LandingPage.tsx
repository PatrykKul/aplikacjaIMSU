import {
  EyeIcon,
  HandIcon,
  HeadphonesIcon,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";

import { Logo } from "@/shared/layout/Logo";
import { cn } from "@/shared/lib/utils";
import { buttonVariants } from "@/shared/ui/button";

type FormCard = {
  letter: "V" | "A" | "K";
  title: string;
  description: string;
  icon: LucideIcon;
  /** Literal classes, so Tailwind can find them. */
  tone: string;
};

const formCards: FormCard[] = [
  {
    letter: "V",
    title: "Wzrokowo",
    description: "Obrazy, wykresy, schematy i filmy.",
    icon: EyeIcon,
    tone: "bg-form-v-soft text-form-v-foreground",
  },
  {
    letter: "A",
    title: "Słuchowo",
    description: "Nagrania, wyjaśnienia i tekst czytany przez lektora.",
    icon: HeadphonesIcon,
    tone: "bg-form-a-soft text-form-a-foreground",
  },
  {
    letter: "K",
    title: "Przez działanie",
    description: "Ćwiczenia, przykłady i próby.",
    icon: HandIcon,
    tone: "bg-form-k-soft text-form-k-foreground",
  },
];

const steps = [
  {
    title: "Ankieta",
    description:
      "20 krótkich pytań pokazuje, czy jesteś wzrokowcem, słuchowcem czy kinestetykiem – albo trochę każdym.",
  },
  {
    title: "Lekcja pod Twój styl",
    description:
      "Materiały w Twoim stylu są rozwinięte, pozostałe zwinięte – możesz je otworzyć. System zawsze mówi, dlaczego coś widzisz.",
  },
  {
    title: "Quiz i propozycja",
    description:
      "Wyniki quizów zmieniają wagi stylów. Gdy inna forma wyraźnie prowadzi, system proponuje zmianę – przyjmujesz ją albo zostajesz przy swoim.",
  },
];

/** Start page for guests: what IMSU is, how it adapts, where to start. */
export function LandingPage() {
  return (
    <div className="flex min-h-svh flex-col">
      <header className="border-b">
        <div className="grid h-16 grid-cols-[minmax(max-content,1fr)_minmax(0,64rem)_minmax(max-content,1fr)] items-center px-4 sm:px-6">
          <Logo className="justify-self-start" />
          <div />
          <nav
            aria-label="Konto"
            className="flex items-center gap-2 justify-self-end"
          >
            <Link
              href="/login"
              className={cn(buttonVariants({ variant: "ghost" }))}
            >
              Zaloguj się
            </Link>
            <Link
              href="/register"
              className={cn(buttonVariants(), "hidden sm:inline-flex")}
            >
              Załóż konto
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 sm:px-6">
        <section className="grid items-center gap-10 py-16 sm:py-24 lg:grid-cols-[1.2fr_1fr]">
          <div className="space-y-6">
            <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
              Ucz się po swojemu
            </h1>
            <p className="max-w-[55ch] text-lg text-muted-foreground">
              IMSU podaje lekcje w formie, z której najłatwiej się uczysz –
              obrazem, dźwiękiem albo przez działanie. Po każdym quizie
              sprawdza, co naprawdę działa, i podpowiada zmianę stylu. Decyzja
              zawsze należy do Ciebie.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/register"
                className={cn(buttonVariants({ size: "lg" }))}
              >
                Załóż konto
              </Link>
              <Link
                href="/login"
                className={cn(
                  buttonVariants({ variant: "outline", size: "lg" }),
                )}
              >
                Mam już konto
              </Link>
            </div>
          </div>

          <ul
            role="list"
            aria-label="Trzy sposoby uczenia się"
            className="grid gap-3"
          >
            {formCards.map(
              ({ letter, title, description, icon: Icon, tone }) => (
                <li
                  key={letter}
                  className="flex items-center gap-4 rounded-xl bg-card p-4 ring-1 ring-foreground/10"
                >
                  <span
                    aria-hidden="true"
                    className={cn(
                      "flex size-12 shrink-0 items-center justify-center rounded-full",
                      tone,
                    )}
                  >
                    <Icon className="size-6" />
                  </span>
                  <div>
                    <p className="font-medium">
                      {letter} · {title}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {description}
                    </p>
                  </div>
                </li>
              ),
            )}
          </ul>
        </section>

        <section
          aria-labelledby="how-it-works"
          className="space-y-8 border-t py-16"
        >
          <h2 id="how-it-works" className="text-2xl font-semibold">
            Jak to działa
          </h2>
          <ol role="list" className="grid gap-8 sm:grid-cols-3">
            {steps.map((step, index) => (
              <li key={step.title} className="space-y-3">
                <span
                  aria-hidden="true"
                  className="flex size-8 items-center justify-center rounded-full bg-primary text-sm font-semibold text-primary-foreground tabular-nums"
                >
                  {index + 1}
                </span>
                <h3 className="text-lg font-medium">{step.title}</h3>
                <p className="text-muted-foreground">{step.description}</p>
              </li>
            ))}
          </ol>
        </section>

        <section
          aria-labelledby="for-teachers"
          className="mb-16 flex flex-col gap-4 rounded-xl bg-accent p-6 text-accent-foreground sm:flex-row sm:items-center sm:justify-between sm:p-8"
        >
          <div className="space-y-2">
            <h2 id="for-teachers" className="text-xl font-semibold">
              Uczysz innych?
            </h2>
            <p className="max-w-[60ch]">
              Twórz kursy z tekstem, wzorami, obrazami, nagraniami i filmami.
              Oznacz materiały jako V, A lub K, dodaj quiz i przypisz kurs
              swojej klasie.
            </p>
          </div>
          <Link
            href="/register"
            className={cn(
              buttonVariants({ variant: "outline" }),
              "shrink-0 self-start sm:self-center",
            )}
          >
            Załóż konto nauczyciela
          </Link>
        </section>
      </main>

      <footer className="border-t py-6 text-center text-sm text-muted-foreground">
        Projekt zaliczeniowy · Inteligentne multimedialne systemy uczące · UwB
        2026
      </footer>
    </div>
  );
}
