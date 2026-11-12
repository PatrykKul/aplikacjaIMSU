"use client";

import { useEffect, useId, useRef, useState } from "react";

import { FORMS, type Form } from "@/features/content/types";
import { formShort, percentagesText } from "@/features/learning-style/explain";
import {
  FORM_DASH,
  FORM_FILL,
  FORM_STROKE,
  FORM_TEXT_FILL,
} from "@/features/learning-style/form-tones";
import { cn } from "@/shared/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/ui/table";

import { formatDateTime, formatShortDate } from "../format";
import type { HistoryPoint } from "../types";

// Geometry in CSS pixels; the width follows the container
const HEIGHT = 260;
const PAD_TOP = 16;
const PAD_BOTTOM = 32;
const PAD_LEFT = 44;
const LABEL_GAP = 18;
const NARROW = 440;
const TICKS = [0, 25, 50, 75, 100];

function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(640);
  useEffect(() => {
    const element = ref.current;
    if (!element) {
      return;
    }
    const observer = new ResizeObserver(([entry]) => {
      setWidth(Math.round(entry.contentRect.width));
    });
    observer.observe(element);
    return () => observer.disconnect();
  }, []);
  return [ref, width] as const;
}

/** End labels must not overlap: push them apart by at least LABEL_GAP. */
function spreadLabels(
  ys: Record<Form, number>,
  min: number,
  max: number,
): Record<Form, number> {
  const order = [...FORMS].sort((a, b) => ys[a] - ys[b]);
  const placed = order.map((form) => ys[form]);
  for (let i = 1; i < placed.length; i++) {
    placed[i] = Math.max(placed[i], placed[i - 1] + LABEL_GAP);
  }
  placed[placed.length - 1] = Math.min(placed[placed.length - 1], max);
  for (let i = placed.length - 2; i >= 0; i--) {
    placed[i] = Math.min(placed[i], placed[i + 1] - LABEL_GAP);
  }
  placed[0] = Math.max(placed[0], min);
  const result = { ...ys };
  order.forEach((form, i) => {
    result[form] = placed[i];
  });
  return result;
}

function ChartTable({ history }: { history: HistoryPoint[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Data</TableHead>
          <TableHead>Styl</TableHead>
          {FORMS.map((form) => (
            <TableHead key={form} className="text-right">
              {form} · {formShort(form).toLowerCase()}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {history.map((point, index) => (
          <TableRow key={`${point.at}-${index}`}>
            <TableCell className="tabular-nums">
              {formatDateTime(point.at)}
            </TableCell>
            <TableCell>{point.style ?? "–"}</TableCell>
            {FORMS.map((form) => (
              <TableCell key={form} className="text-right tabular-nums">
                {point.percentages[form]}%
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

/**
 * Percentages of V, A and K over time: one point per change of the profile,
 * a line per form (color + dash pattern + letter and name at the end),
 * then a table of the same data.
 */
export function PercentChart({ history }: { history: HistoryPoint[] }) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const titleId = useId();

  if (history.length === 0) {
    return (
      <p className="text-muted-foreground">
        Wykres pojawi się po wypełnieniu ankiety.
      </p>
    );
  }

  const narrow = width < NARROW;
  const padRight = narrow ? 60 : 132;
  const plotWidth = Math.max(width - PAD_LEFT - padRight, 40);
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const count = history.length;
  const x = (index: number) =>
    PAD_LEFT +
    (count === 1 ? plotWidth / 2 : (index * plotWidth) / (count - 1));
  const y = (value: number) => PAD_TOP + ((100 - value) / 100) * plotHeight;

  const last = history[count - 1];
  const endY = spreadLabels(
    {
      V: y(last.percentages.V),
      A: y(last.percentages.A),
      K: y(last.percentages.K),
    },
    PAD_TOP + 4,
    PAD_TOP + plotHeight,
  );

  // Points where the active style changed
  const styleChanges = history
    .map((point, index) => ({ point, index }))
    .filter(
      ({ point, index }) =>
        index > 0 &&
        point.style !== null &&
        point.style !== history[index - 1].style,
    );

  const dateIndexes =
    count === 1
      ? [0]
      : narrow || count === 2
        ? [0, count - 1]
        : [0, Math.floor((count - 1) / 2), count - 1];

  return (
    <figure className="space-y-4">
      <div ref={ref} className="w-full">
        <svg
          width={width}
          height={HEIGHT}
          viewBox={`0 0 ${width} ${HEIGHT}`}
          role="img"
          aria-labelledby={titleId}
          className="block max-w-full overflow-visible text-xs"
        >
          <title id={titleId}>
            {`Procenty form w czasie, ${count} punktów. Teraz: ${percentagesText(last.percentages)}. Dane w tabeli pod wykresem.`}
          </title>

          {/* Axis 0-100% */}
          {TICKS.map((tick) => (
            <g key={tick}>
              <line
                x1={PAD_LEFT}
                x2={PAD_LEFT + plotWidth}
                y1={y(tick)}
                y2={y(tick)}
                className={cn(
                  "stroke-border",
                  tick === 0 && "stroke-muted-foreground/60",
                )}
                strokeWidth={1}
              />
              <text
                x={PAD_LEFT - 8}
                y={y(tick)}
                textAnchor="end"
                dominantBaseline="middle"
                className="fill-muted-foreground tabular-nums"
              >
                {tick}%
              </text>
            </g>
          ))}

          {/* Changes of the style */}
          {styleChanges.map(({ point, index }) => (
            <g key={`style-${index}`}>
              <line
                x1={x(index)}
                x2={x(index)}
                y1={PAD_TOP}
                y2={PAD_TOP + plotHeight}
                className="stroke-muted-foreground/50"
                strokeDasharray="3 3"
              />
              <text
                x={x(index) + 4}
                y={PAD_TOP + 2}
                dominantBaseline="hanging"
                className="fill-muted-foreground"
              >
                styl {point.style}
              </text>
            </g>
          ))}

          {/* Dates under the axis */}
          {dateIndexes.map((index) => (
            <text
              key={`date-${index}`}
              x={x(index)}
              y={HEIGHT - 8}
              textAnchor={
                count === 1
                  ? "middle"
                  : index === 0
                    ? "start"
                    : index === count - 1
                      ? "end"
                      : "middle"
              }
              className="fill-muted-foreground"
            >
              {formatShortDate(history[index].at)}
            </text>
          ))}

          {/* One line per form */}
          {FORMS.map((form) => {
            const path = history
              .map(
                (point, index) =>
                  `${index === 0 ? "M" : "L"}${x(index).toFixed(1)},${y(point.percentages[form]).toFixed(1)}`,
              )
              .join(" ");
            return (
              <g key={form}>
                {count > 1 && (
                  <path
                    d={path}
                    fill="none"
                    className={FORM_STROKE[form]}
                    strokeWidth={2.5}
                    strokeDasharray={FORM_DASH[form]}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                )}
                {history.map((point, index) => (
                  <circle
                    key={index}
                    cx={x(index)}
                    cy={y(point.percentages[form])}
                    r={3.5}
                    className={cn(FORM_FILL[form], "stroke-background")}
                    strokeWidth={1.5}
                  />
                ))}
                <text
                  x={x(count - 1) + 10}
                  y={endY[form]}
                  dominantBaseline="middle"
                  className={cn(FORM_TEXT_FILL[form], "text-[13px]")}
                >
                  <tspan fontWeight={600}>{form}</tspan>
                  {!narrow && <tspan> {formShort(form).toLowerCase()}</tspan>}
                  <tspan className="tabular-nums">
                    {" "}
                    {last.percentages[form]}%
                  </tspan>
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      <figcaption className="text-sm text-muted-foreground">
        Linia ciągła – wzrokowe (V), kreskowana – słuchowe (A), kropkowana –
        kinestetyczne (K). Punkt to stan po ankiecie, quizie albo zmianie stylu.
      </figcaption>
      <ChartTable history={history} />
    </figure>
  );
}
