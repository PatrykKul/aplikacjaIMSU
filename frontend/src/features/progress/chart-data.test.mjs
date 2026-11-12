// Test of `chart-data.ts` (D62) with Node's test runner, no extra dependencies:
//   node --test src/features/progress/chart-data.test.mjs   (or: npm test)
// The module has type-only imports, so TypeScript's transpiler turns it into
// plain JavaScript, which is loaded from a temporary file.

import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, describe, test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
let dir;
let buildChartData;
let lessonNumbers;

before(async () => {
  const source = readFileSync(path.join(here, "chart-data.ts"), "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2020,
      verbatimModuleSyntax: false,
    },
  });
  dir = mkdtempSync(path.join(tmpdir(), "chart-data-"));
  const file = path.join(dir, "chart-data.mjs");
  writeFileSync(file, outputText);
  ({ buildChartData, lessonNumbers } = await import(pathToFileURL(file).href));
});

after(() => rmSync(dir, { recursive: true, force: true }));

// --- Patryk's path: survey → 2 quizzes in A → manual A → V → back to A ---

const course = { id: 1, title: "Programowanie w Pythonie" };
const at = (minute) => `2026-11-12T10:${String(minute).padStart(2, "0")}:00Z`;
let id = 0;
const entry = (type, data, extra = {}) => ({
  id: ++id,
  type,
  data,
  at: at(id),
  course: null,
  lesson: null,
  ...extra,
});
const quiz = (lesson, before, after) =>
  entry(
    "quiz_attempt",
    {
      draw_id: id,
      form: "A",
      percent: 100,
      passed: true,
      counted: true,
      percentages_before: before,
      percentages_after: after,
      unlocked_lesson: null,
    },
    { course, lesson },
  );

const p0 = { V: 30, A: 50, K: 20 };
const p1 = { V: 26, A: 60, K: 14 };
const p2 = { V: 22, A: 70, K: 8 };

const history = [
  {
    at: at(1),
    percentages: p0,
    style: "A",
    event: entry("survey_completed", {
      points: p0,
      percentages: p0,
      style: "A",
      tie_styles: [],
    }),
  },
  {
    at: at(2),
    percentages: p1,
    style: "A",
    event: quiz({ id: 11, title: "Pętla for" }, p0, p1),
  },
  {
    at: at(3),
    percentages: p2,
    style: "A",
    event: quiz({ id: 12, title: "Funkcja range" }, p1, p2),
  },
  {
    at: at(4),
    percentages: p2,
    style: "V",
    event: entry("manual_style_change", {
      from: "A",
      to: "V",
      cleared_lessons: [],
    }),
  },
  {
    at: at(5),
    percentages: p2,
    style: "A",
    event: entry("style_change_reverted", {
      from: "V",
      to: "A",
      trial_id: 7,
      source: "manual",
      cleared_lessons: [],
    }),
  },
];

describe("buildChartData: survey → 2 quizzes → A → V → A", () => {
  test("points only for the survey and the counted quizzes", () => {
    const data = buildChartData(
      history,
      lessonNumbers([
        { lesson_id: 11, number: 1 },
        { lesson_id: 12, number: 2 },
      ]),
    );
    assert.equal(data.points.length, 3);
    assert.deepEqual(
      data.points.map((point) => point.event.kind),
      ["survey", "quiz", "quiz"],
    );
    assert.deepEqual(
      data.points.map((point) => point.slot),
      [0, 1, 2],
    );
    // "L1 · A", "L2 · A" under the axis
    assert.deepEqual(
      data.points
        .slice(1)
        .map((point) => [point.event.lessonNumber, point.event.form]),
      [
        [1, "A"],
        [2, "A"],
      ],
    );
    assert.deepEqual(data.points[2].percentages, p2);
  });

  test("the change to V is one marker, struck through by the revert", () => {
    const data = buildChartData(history);
    assert.equal(data.markers.length, 1);
    const [marker] = data.markers;
    assert.equal(marker.style, "V");
    assert.equal(marker.reverted, true);
    assert.equal(marker.event.kind, "style");
    assert.equal(marker.event.source, "manual");
    // After the last point: half a step to its right, the axis grows with it
    assert.equal(marker.slot, 2.5);
    assert.equal(data.maxSlot, 2.5);
  });

  test("a table row for every event, style changes without percentages", () => {
    const data = buildChartData(history);
    assert.deepEqual(
      data.rows.map((row) => row.event.kind),
      ["survey", "quiz", "quiz", "style", "revert"],
    );
    assert.deepEqual(
      data.rows.map((row) => row.percentages === null),
      [false, false, false, true, true],
    );
    assert.deepEqual(
      data.rows.map((row) => row.style),
      ["A", "A", "A", "V", "A"],
    );
    assert.equal(data.rows[1].event.lessonTitle, "Pętla for");
    assert.equal(data.rows[1].event.percent, 100);
    assert.equal(data.rows[4].event.style, "A");
  });

  test("lesson number from the journal entry wins over the lookup", () => {
    const withNumber = history.map((point, index) =>
      index === 1
        ? {
            ...point,
            event: {
              ...point.event,
              lesson: { id: 11, title: "Pętla for", number: 4 },
            },
          }
        : point,
    );
    const data = buildChartData(withNumber, new Map([[11, 1]]));
    assert.equal(data.points[1].event.lessonNumber, 4);
    // No number and no lookup: null ("Quiz · A")
    assert.equal(data.points[2].event.lessonNumber, null);
  });
});

describe("buildChartData: other cases", () => {
  test("a change that stays is a plain marker between two quizzes", () => {
    const kept = [
      ...history.slice(0, 4),
      {
        at: at(9),
        percentages: { V: 32, A: 63, K: 5 },
        style: "V",
        event: entry(
          "quiz_attempt",
          {
            draw_id: 99,
            form: "V",
            percent: 80,
            passed: true,
            counted: true,
            percentages_before: p2,
            percentages_after: { V: 32, A: 63, K: 5 },
            unlocked_lesson: null,
          },
          { course, lesson: { id: 13, title: "Listy" } },
        ),
      },
    ];
    const data = buildChartData(kept);
    assert.equal(data.points.length, 4);
    assert.equal(data.markers.length, 1);
    assert.equal(data.markers[0].reverted, false);
    assert.equal(data.markers[0].slot, 2.5);
    assert.equal(data.maxSlot, 3);
  });

  test("two changes between the same points are spread evenly", () => {
    const twice = [
      ...history.slice(0, 4),
      {
        at: at(10),
        percentages: p2,
        style: "K",
        event: entry("proposal_accepted", {
          proposal_id: 3,
          kind: "switch",
          from: "V",
          to: "K",
          cleared_lessons: [],
        }),
      },
    ];
    const data = buildChartData(twice);
    assert.deepEqual(
      data.markers.map((marker) => [
        marker.style,
        marker.slot,
        marker.reverted,
      ]),
      [
        ["V", 2.25, false],
        ["K", 2.5, false],
      ],
    );
    assert.equal(data.markers[1].event.source, "proposal");
  });

  test("older points without an event: a style change keeps the percentages", () => {
    const old = history.map((point) => ({ ...point, event: null }));
    const data = buildChartData(old.slice(0, 4));
    assert.deepEqual(
      data.points.map((point) => point.event.kind),
      ["survey", "other", "other"],
    );
    assert.equal(data.markers.length, 1);
    assert.equal(data.markers[0].style, "V");
    assert.equal(data.markers[0].event.source, null);
  });

  test("survey only: one point in the middle, no markers", () => {
    const data = buildChartData(history.slice(0, 1));
    assert.equal(data.points.length, 1);
    assert.equal(data.maxSlot, 0);
    assert.equal(data.rows.length, 1);
  });
});
