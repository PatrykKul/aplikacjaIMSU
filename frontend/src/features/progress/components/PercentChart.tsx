"use client";

import { useEffect, useId, useRef, useState } from "react";

import { FORMS, type Form } from "@/features/content/types";
import {
  formShort,
  historyAxisLabel,
  historyEventText,
  percentagesText,
  styleMarkerText,
} from "@/features/learning-style/explain";
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

import { buildChartData, type ChartData } from "../chart-data";
import { formatDateTime } from "../format";
import type { HistoryPoint } from "../types";

// Geometry in CSS pixels; the width follows the container
const HEIGHT = 260;
const PAD_TOP = 16;
const PAD_BOTTOM = 36;
const PAD_LEFT = 44;
const LABEL_GAP = 18;
const NARROW = 440;
const TICKS = [0, 25, 50, 75, 100];
/** Room for one label under the axis ("Ankieta", "L12 · K"). */
const AXIS_LABEL_WIDTH = 60;

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

/** Every event: points with their percentages, style changes "bez zmian". */
function ChartTable({ rows }: { rows: ChartData["rows"] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Data</TableHead>
          <TableHead>Zdarzenie</TableHead>
          <TableHead>Styl</TableHead>
          {FORMS.map((form) => (
            <TableHead key={form} className="text-right">
              {form} · {formShort(form).toLowerCase()}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.map((row, index) => {
          const percentages = row.percentages;
          return (
            <TableRow key={`${row.at}-${index}`}>
              <TableCell className="tabular-nums">
                {formatDateTime(row.at)}
              </TableCell>
              <TableCell>{historyEventText(row.event)}</TableCell>
              <TableCell>{row.style ?? "–"}</TableCell>
              {percentages ? (
                FORMS.map((form) => (
                  <TableCell key={form} className="text-right tabular-nums">
                    {percentages[form]}%
                  </TableCell>
                ))
              ) : (
                <TableCell
                  colSpan={FORMS.length}
                  className="text-right text-muted-foreground"
                >
                  bez zmian
                </TableCell>
              )}
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

type PercentChartProps = {
  history: HistoryPoint[];
  /** Lesson id → number, for "L1 · A" when the journal entry has no number. */
  lessonNumbers?: ReadonlyMap<number, number>;
};

/**
 * D62: percentages of V, A and K over time. Points only for the survey and
 * counted quizzes (a line per form: color + dash pattern + letter and name at
 * the end), changes of the style as vertical markers between them, the X axis
 * named by events; then a table of every event.
 */
export function PercentChart({ history, lessonNumbers }: PercentChartProps) {
  const [ref, width] = useWidth<HTMLDivElement>();
  const titleId = useId();

  if (history.length === 0) {
    return (
      <p className="text-muted-foreground">
        Wykres pojawi się po wypełnieniu ankiety.
      </p>
    );
  }

  const { points, markers, rows, maxSlot } = buildChartData(
    history,
    lessonNumbers,
  );
  if (points.length === 0) {
    return <ChartTable rows={rows} />;
  }

  const narrow = width < NARROW;
  const padRight = narrow ? 60 : 132;
  const plotWidth = Math.max(width - PAD_LEFT - padRight, 40);
  const plotHeight = HEIGHT - PAD_TOP - PAD_BOTTOM;
  const x = (slot: number) =>
    PAD_LEFT + (maxSlot === 0 ? plotWidth / 2 : (slot * plotWidth) / maxSlot);
  const y = (value: number) => PAD_TOP + ((100 - value) / 100) * plotHeight;
  const step = maxSlot === 0 ? plotWidth : plotWidth / maxSlot;

  const last = points[points.length - 1];
  const endX = x(maxSlot);
  const endY = spreadLabels(
    {
      V: y(last.percentages.V),
      A: y(last.percentages.A),
      K: y(last.percentages.K),
    },
    PAD_TOP + 4,
    PAD_TOP + plotHeight,
  );

  // Every k-th label under the axis when they would overlap, always the last one
  const every = Math.max(1, Math.ceil(AXIS_LABEL_WIDTH / step));
  const labelled = points.filter(
    (point) =>
      point === last ||
      (point.slot % every === 0 && last.slot - point.slot >= every),
  );
  const anchor = (slot: number) => {
    if (maxSlot === 0) {
      return "middle";
    }
    if (slot === 0) {
      return "start";
    }
    return slot === maxSlot ? "end" : "middle";
  };

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
            {`Procenty form w czasie: ${points.length} punktów (ankieta i policzone quizy), zmiany stylu: ${markers.length}. Teraz: ${percentagesText(last.percentages)}. Dane w tabeli pod wykresem.`}
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

          {/* Changes of the style: a line between points, no point of their own */}
          {markers.map((marker, index) => {
            const mx = x(marker.slot);
            const atEnd = marker.slot >= maxSlot;
            const tx = atEnd ? mx - 4 : mx + 4;
            const ty = PAD_TOP + 2 + (index % 2) * 28;
            const tooltip = [
              marker.reverted
                ? `${historyEventText(marker.event)} – cofnięta przed pierwszą lekcją`
                : historyEventText(marker.event),
              formatDateTime(marker.at),
            ].join("\n");
            return (
              <g key={`marker-${index}`}>
                <title>{tooltip}</title>
                <line
                  x1={mx}
                  x2={mx}
                  y1={PAD_TOP}
                  y2={PAD_TOP + plotHeight}
                  className={
                    marker.reverted
                      ? "stroke-muted-foreground/40"
                      : "stroke-muted-foreground/60"
                  }
                  strokeDasharray={marker.reverted ? "1.5 3" : "3 3"}
                />
                {/* Wide transparent strip, so the tooltip works on hover */}
                <rect
                  x={mx - 6}
                  y={PAD_TOP}
                  width={12}
                  height={plotHeight}
                  fill="transparent"
                />
                <text
                  x={tx}
                  y={ty}
                  textAnchor={atEnd ? "end" : "start"}
                  dominantBaseline="hanging"
                  className="fill-muted-foreground"
                >
                  <tspan
                    style={
                      marker.reverted
                        ? { textDecoration: "line-through" }
                        : undefined
                    }
                  >
                    {styleMarkerText(marker.style)}
                  </tspan>
                  {marker.reverted && (
                    <tspan x={tx} dy="1.2em">
                      cofnięta
                    </tspan>
                  )}
                </text>
              </g>
            );
          })}

          {/* Events under the axis */}
          {labelled.map((point) => (
            <text
              key={`label-${point.slot}`}
              x={x(point.slot)}
              y={HEIGHT - 10}
              textAnchor={anchor(point.slot)}
              className="fill-muted-foreground"
            >
              {historyAxisLabel(point.event)}
            </text>
          ))}

          {/* One line per form; flat after the last point up to "now" */}
          {FORMS.map((form) => {
            const path = points
              .map(
                (point, index) =>
                  `${index === 0 ? "M" : "L"}${x(point.slot).toFixed(1)},${y(point.percentages[form]).toFixed(1)}`,
              )
              .join(" ");
            const lastY = y(last.percentages[form]);
            return (
              <g key={form}>
                {points.length > 1 && (
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
                {endX > x(last.slot) && (
                  <line
                    x1={x(last.slot)}
                    x2={endX}
                    y1={lastY}
                    y2={lastY}
                    className={cn(FORM_STROKE[form], "opacity-40")}
                    strokeWidth={2.5}
                    strokeDasharray={FORM_DASH[form]}
                    strokeLinecap="round"
                  />
                )}
                {points.map((point) => (
                  <circle
                    key={point.slot}
                    cx={x(point.slot)}
                    cy={y(point.percentages[form])}
                    r={3.5}
                    className={cn(FORM_FILL[form], "stroke-background")}
                    strokeWidth={1.5}
                  />
                ))}
                <text
                  x={endX + 10}
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

          {/* Tooltips: a column per point with the event, date and numbers */}
          {points.map((point) => (
            <g key={`hit-${point.slot}`}>
              <title>
                {[
                  `${historyAxisLabel(point.event)}: ${historyEventText(point.event)}`,
                  formatDateTime(point.at),
                  percentagesText(point.percentages),
                ].join("\n")}
              </title>
              <rect
                x={x(point.slot) - Math.min(step, 24) / 2}
                y={PAD_TOP}
                width={Math.min(step, 24)}
                height={plotHeight}
                fill="transparent"
              />
            </g>
          ))}
        </svg>
      </div>
      <figcaption className="text-sm text-muted-foreground">
        Linia ciągła – wzrokowe (V), kreskowana – słuchowe (A), kropkowana –
        kinestetyczne (K). Punkt to stan po ankiecie albo policzonym quizie,
        pionowa linia – zmiana stylu (przekreślona – cofnięta przed pierwszą
        lekcją). Data i godzina są w podpowiedzi i w tabeli.
      </figcaption>
      <ChartTable rows={rows} />
    </figure>
  );
}
