import Link from "next/link";
import { ArrowRight, PartyPopper, RefreshCw } from "lucide-react";
import type { Rekomendacja } from "@/lib/types";

type Props = { rekomendacja: Rekomendacja; zaliczony: boolean };

/** Co dalej po quizie + krótkie „dlaczego to widzisz". */
export function RekomendacjaCard({ rekomendacja: r, zaliczony }: Props) {
  const href =
    r.typ === "nastepny" && r.temat_id
      ? `/tematy/${r.temat_id}`
      : r.typ === "powtorka" && r.temat_id && r.styl
        ? `/tematy/${r.temat_id}?styl=${r.styl}`
        : null;

  return (
    <div
      className={`rounded-2xl border p-5 ${
        zaliczony
          ? "border-emerald-400/60 bg-emerald-50 dark:bg-emerald-950/20"
          : "border-sky-400/60 bg-sky-50 dark:bg-sky-950/20"
      }`}
      data-testid="rekomendacja"
    >
      <div className="flex items-start gap-3">
        {zaliczony ? (
          <PartyPopper className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" aria-hidden />
        ) : (
          <RefreshCw className="mt-0.5 h-5 w-5 shrink-0 text-sky-500" aria-hidden />
        )}
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-slate-900 dark:text-white">{r.tytul}</p>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Dlaczego to widzisz: {r.dlaczego}
          </p>
          {href && (
            <Link
              href={href}
              className="mt-4 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-primary to-secondary px-4 py-2 text-sm font-semibold text-white shadow-neon-sm transition hover:opacity-95"
            >
              {r.typ === "nastepny" ? "Przejdź do następnego tematu" : "Spróbuj inaczej"}
              <ArrowRight className="h-4 w-4" aria-hidden />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
