/**
 * D62: the history of the profile as chart points, style markers and table
 * rows. Pure functions with type-only imports (tested by `chart-data.test.mjs`);
 * the Polish words come from `learning-style/explain.ts`.
 */
import type { Form } from "@/features/content/types";

import type {
  HistoryPoint,
  JournalEntry,
  LessonProgress,
  Percentages,
} from "./types";

/** What added a point of the history, reduced to what the chart needs. */
export type HistoryEvent =
  | { kind: "survey" }
  | {
      kind: "quiz";
      lessonNumber: number | null;
      lessonTitle: string | null;
      form: Form;
      percent: number;
    }
  /** Tie of the survey resolved: the first style, percentages unchanged. */
  | { kind: "tie"; style: Form }
  | { kind: "style"; style: Form; source: "manual" | "proposal" | null }
  /** R7a: the last change undone before its first lesson; `style` = back to. */
  | { kind: "revert"; style: Form }
  /** An older point without its event. */
  | { kind: "other" };

/** Survey or counted quiz: a point on every line. */
export type ChartPoint = {
  /** Position on the X axis: points are 0, 1, 2…; markers sit between them. */
  slot: number;
  at: string;
  percentages: Percentages;
  style: Form | null;
  event: HistoryEvent;
};

/** A change of the style: a vertical line, no point of its own. */
export type StyleMarker = {
  slot: number;
  at: string;
  style: Form;
  event: HistoryEvent;
  /** Undone before the first lesson (struck through, "cofnięta"). */
  reverted: boolean;
};

export type HistoryRow = {
  at: string;
  style: Form | null;
  event: HistoryEvent;
  /** null = the event did not change the percentages ("bez zmian"). */
  percentages: Percentages | null;
};

export type ChartData = {
  points: ChartPoint[];
  markers: StyleMarker[];
  rows: HistoryRow[];
  /** Last slot of the axis (a marker after the last point extends it). */
  maxSlot: number;
};

/** Lesson id → number from the results table ("L1 · A" under the axis). */
export function lessonNumbers(
  lessons: Pick<LessonProgress, "lesson_id" | "number">[],
): Map<number, number> {
  const numbers = new Map<number, number>();
  for (const lesson of lessons) {
    if (lesson.number !== null) {
      numbers.set(lesson.lesson_id, lesson.number);
    }
  }
  return numbers;
}

/** Event types that add a point; the others only change the style. */
const POINT_KINDS: HistoryEvent["kind"][] = ["survey", "quiz", "other"];

function samePercentages(a: Percentages, b: Percentages): boolean {
  return a.V === b.V && a.A === b.A && a.K === b.K;
}

/**
 * The event behind one point. `lessonNumbers` (lesson id → number) fills in
 * the number when the journal entry names the lesson by id and title only.
 */
export function describeEvent(
  entry: JournalEntry | null,
  point: HistoryPoint,
  previous: HistoryPoint | null,
  lessonNumbers: ReadonlyMap<number, number> = new Map(),
): HistoryEvent {
  if (!entry) {
    // Older data: a change of the style keeps the percentages
    if (
      previous &&
      point.style !== null &&
      point.style !== previous.style &&
      samePercentages(point.percentages, previous.percentages)
    ) {
      return { kind: "style", style: point.style, source: null };
    }
    return previous ? { kind: "other" } : { kind: "survey" };
  }
  switch (entry.type) {
    case "survey_completed":
      return { kind: "survey" };
    case "quiz_attempt": {
      const lesson = entry.lesson;
      return {
        kind: "quiz",
        lessonNumber:
          lesson?.number ??
          (lesson ? lessonNumbers.get(lesson.id) : null) ??
          null,
        lessonTitle: lesson?.title ?? null,
        form: entry.data.form,
        percent: entry.data.percent,
      };
    }
    case "tie_resolved":
      return { kind: "tie", style: entry.data.style };
    case "manual_style_change":
      return { kind: "style", style: entry.data.to, source: "manual" };
    case "proposal_accepted":
      return { kind: "style", style: entry.data.to, source: "proposal" };
    case "style_change_reverted":
      return { kind: "revert", style: point.style ?? entry.data.to };
    default:
      return { kind: "other" };
  }
}

/**
 * Points for the survey and counted quizzes; style changes as markers spread
 * evenly between the two points around them (or after the last point).
 * A revert strikes through the change it undoes instead of adding a marker.
 */
export function buildChartData(
  history: HistoryPoint[],
  lessonNumbers: ReadonlyMap<number, number> = new Map(),
): ChartData {
  const points: ChartPoint[] = [];
  const markers: StyleMarker[] = [];
  const rows: HistoryRow[] = [];
  // Markers since the last point; their slots are known at the next point
  let pending: StyleMarker[] = [];

  const place = (from: number, span: number) => {
    pending.forEach((marker, index) => {
      marker.slot = from + (span * (index + 1)) / (pending.length + 1);
    });
    pending = [];
  };

  history.forEach((point, index) => {
    const previous = index > 0 ? history[index - 1] : null;
    const event = describeEvent(point.event, point, previous, lessonNumbers);

    if (POINT_KINDS.includes(event.kind)) {
      const slot = points.length;
      if (slot > 0) {
        place(slot - 1, 1);
      }
      points.push({
        slot,
        at: point.at,
        percentages: point.percentages,
        style: point.style,
        event,
      });
      rows.push({
        at: point.at,
        style: point.style,
        event,
        percentages: point.percentages,
      });
      return;
    }

    rows.push({ at: point.at, style: point.style, event, percentages: null });
    if (event.kind === "revert") {
      // R7a: the undone change is the latest one still in force
      const undone = [...markers].reverse().find((marker) => !marker.reverted);
      if (undone) {
        undone.reverted = true;
        return;
      }
    }
    const style =
      event.kind === "style" || event.kind === "tie" || event.kind === "revert"
        ? event.style
        : null;
    if (style) {
      const marker: StyleMarker = {
        slot: 0,
        at: point.at,
        style,
        event,
        reverted: false,
      };
      markers.push(marker);
      pending.push(marker);
    }
  });

  // Markers after the last point: half a step to its right
  const last = Math.max(points.length - 1, 0);
  const trailing = pending.length > 0;
  place(last, 0.5 * (trailing ? (pending.length + 1) / pending.length : 1));

  return {
    points,
    markers,
    rows,
    maxSlot: trailing ? last + 0.5 : last,
  };
}
