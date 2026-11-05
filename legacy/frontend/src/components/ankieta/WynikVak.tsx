import { STYLE, STYL_KOLOR, STYL_NAZWA, styleZ } from "@/lib/labels";
import type { Styl } from "@/lib/types";

type Props = {
  punkty: Record<Styl, number>;
  /** Styles highlighted as dominant, e.g. "V" or "VA". */
  dominujacy?: string | null;
};

/** Three horizontal bars: V / A / K points. */
export function WynikVak({ punkty, dominujacy }: Props) {
  const max = Math.max(1, ...STYLE.map((s) => punkty[s]));
  const wyroznione = styleZ(dominujacy);

  return (
    <ul className="space-y-3">
      {STYLE.map((s) => (
        <li key={s}>
          <div className="mb-1 flex items-baseline justify-between text-sm">
            <span
              className={
                wyroznione.includes(s)
                  ? `font-bold ${STYL_KOLOR[s].text}`
                  : "font-medium text-slate-700 dark:text-slate-300"
              }
            >
              {s} · {STYL_NAZWA[s]}
            </span>
            <span className="font-mono text-sm tabular-nums text-slate-600 dark:text-slate-400">
              {punkty[s]}
            </span>
          </div>
          <div
            className="h-3 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800"
            role="img"
            aria-label={`${STYL_NAZWA[s]}: ${punkty[s]}`}
          >
            <div
              className={`h-full rounded-full transition-all ${STYL_KOLOR[s].bar}`}
              style={{ width: `${(punkty[s] / max) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}
