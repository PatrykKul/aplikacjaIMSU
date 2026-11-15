// Test of `journal-data.ts` (stage 10, point 10) with Node's test runner:
//   node --test src/features/progress/journal-data.test.mjs   (or: npm test)
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
let cancelledTrials;

before(async () => {
  const source = readFileSync(path.join(here, "journal-data.ts"), "utf8");
  const { outputText } = ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2020,
    },
  });
  dir = mkdtempSync(path.join(tmpdir(), "journal-data-"));
  const file = path.join(dir, "journal-data.mjs");
  writeFileSync(file, outputText);
  ({ cancelledTrials } = await import(pathToFileURL(file).href));
});

after(() => rmSync(dir, { recursive: true, force: true }));

let id = 0;
const entry = (type, data) => ({
  id: ++id,
  type,
  data,
  at: `2026-11-15T10:${String(id).padStart(2, "0")}:00Z`,
  course: null,
  lesson: null,
});
const started = (trialId, replaced = null) =>
  entry("trial_started", {
    trial_id: trialId,
    from: "A",
    to: "V",
    source: "manual",
    before_average: 100,
    replaced_trial_id: replaced,
  });
const reverted = (trialId) =>
  entry("style_change_reverted", {
    from: "V",
    to: "A",
    trial_id: trialId,
    source: "manual",
    cleared_lessons: [],
  });

describe("cancelledTrials", () => {
  test("empty journal", () => {
    assert.equal(cancelledTrials([]).size, 0);
  });

  test("a running trial is not cancelled", () => {
    assert.equal(cancelledTrials([started(1)]).size, 0);
  });

  test("reverted: A → V → back to A (newest first, as the API sends it)", () => {
    const result = cancelledTrials([reverted(7), started(7)]);
    assert.deepEqual([...result], [[7, "reverted"]]);
  });

  test("replaced: A → V → K, the second trial names the first", () => {
    const result = cancelledTrials([started(9, 8), started(8)]);
    assert.deepEqual([...result], [[8, "replaced"]]);
  });

  test("replaced and then reverted: both trials cancelled, each with its reason", () => {
    // A → V (trial 1) → K (trial 2 replaces 1) → back to A (trial 2 reverted)
    const result = cancelledTrials([reverted(2), started(2, 1), started(1)]);
    assert.equal(result.get(1), "replaced");
    assert.equal(result.get(2), "reverted");
  });

  test("older events without replaced_trial_id", () => {
    const old = entry("trial_started", {
      trial_id: 3,
      from: "A",
      to: "V",
      source: "proposal",
      before_average: null,
    });
    assert.equal(cancelledTrials([old]).size, 0);
  });

  test("other events are ignored", () => {
    const praise = entry("praise", { form: "V", streak: 3, average: 90 });
    assert.equal(cancelledTrials([praise, started(4)]).size, 0);
  });
});
