import { ArrowDown } from "lucide-react";

type Props = { tresc: string };

/**
 * Prosty diagram przepływu z tekstu: pierwsza linia = tytuł, kolejne = kroki,
 * linia zaczynająca się od "?" = decyzja.
 */
export function DiagramBlock({ tresc }: Props) {
  const linie = tresc
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  if (linie.length === 0) return null;
  const [tytul, ...kroki] = linie;
  const czysty = (t: string) => t.replace(/`/g, "");

  return (
    <figure className="mx-auto max-w-md">
      <figcaption className="mb-4 text-center text-sm font-semibold text-slate-800 dark:text-slate-100">
        {czysty(tytul)}
      </figcaption>
      <ol className="flex flex-col items-center">
        {kroki.map((krok, i) => {
          const decyzja = krok.startsWith("?");
          const tekst = czysty(decyzja ? krok.slice(1).trim() : krok);
          return (
            <li key={i} className="flex w-full flex-col items-center">
              {i > 0 && <ArrowDown className="my-1.5 h-5 w-5 text-sky-500" aria-hidden />}
              <div
                className={
                  decyzja
                    ? "w-full rounded-2xl border-2 border-dashed border-amber-400 bg-amber-50 px-4 py-3 text-center text-sm font-semibold text-amber-900 dark:bg-amber-950/30 dark:text-amber-100"
                    : "w-full rounded-2xl border border-sky-300 bg-sky-50 px-4 py-3 text-center text-sm text-slate-800 dark:border-sky-500/40 dark:bg-sky-950/30 dark:text-slate-100"
                }
              >
                {tekst}
              </div>
            </li>
          );
        })}
      </ol>
    </figure>
  );
}
