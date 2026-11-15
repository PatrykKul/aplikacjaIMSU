// Test of the stage 10 sentences in `explain.ts` with Node's test runner:
//   node --test src/features/learning-style/explain.test.mjs   (or: npm test)
// explain.ts imports two runtime modules (FORMS, plural); all three files are
// transpiled with TypeScript, the "@/..." paths rewritten to the temporary
// copies, and loaded as plain JavaScript.

import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, describe, test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import ts from "typescript";

const here = path.dirname(fileURLToPath(import.meta.url));
const src = path.resolve(here, "../..");
let dir;
let explain;

const MODULES = {
  "explain.mjs": "features/learning-style/explain.ts",
  "content-types.mjs": "features/content/types.ts",
  "plural.mjs": "shared/lib/plural.ts",
};
const PATHS = {
  "@/features/content/types": "./content-types.mjs",
  "@/shared/lib/plural": "./plural.mjs",
};

before(async () => {
  dir = mkdtempSync(path.join(tmpdir(), "explain-"));
  for (const [name, file] of Object.entries(MODULES)) {
    const source = readFileSync(path.join(src, file), "utf8");
    let { outputText } = ts.transpileModule(source, {
      compilerOptions: {
        module: ts.ModuleKind.ESNext,
        target: ts.ScriptTarget.ES2020,
      },
    });
    for (const [from, to] of Object.entries(PATHS)) {
      outputText = outputText.replaceAll(`"${from}"`, `"${to}"`);
    }
    assert.doesNotMatch(outputText, /from "@\//, `${file}: unmapped import`);
    writeFileSync(path.join(dir, name), outputText);
  }
  explain = await import(pathToFileURL(path.join(dir, "explain.mjs")).href);
});

after(() => rmSync(dir, { recursive: true, force: true }));

const row = (values = {}) => ({
  lessons: 0,
  attempts: 0,
  passed_lessons: 0,
  first_try_lessons: 0,
  first_try_passed: 0,
  first_try_rate: null,
  average: null,
  best: null,
  confirmed: false,
  percent: 33,
  ...values,
});

describe("formTableConclusion", () => {
  test("the example of the task: highest average, a form without results", () => {
    const forms = {
      V: row(),
      A: row({ first_try_lessons: 4, average: 84 }),
      K: row({ first_try_lessons: 2, average: 70 }),
    };
    assert.equal(
      explain.formTableConclusion(forms),
      "Najwyższa średnia: słuchowa 84% (4 lekcje). Praktyczna: 70% (2 lekcje). Wzrokowa: nie masz jeszcze wyników.",
    );
  });

  test("no results at all", () => {
    const forms = { V: row(), A: row(), K: row() };
    assert.equal(
      explain.formTableConclusion(forms),
      "Nie masz jeszcze wyników quizów w żadnej formie.",
    );
    assert.equal(
      explain.formTableConclusion(forms, "neutral"),
      "Brak wyników quizów w żadnej formie.",
    );
  });

  test("one form only: no 'highest', one lesson in the singular", () => {
    const forms = {
      V: row({ first_try_lessons: 1, average: 100 }),
      A: row(),
      K: row(),
    };
    assert.equal(
      explain.formTableConclusion(forms),
      "Średnia z pierwszych podejść: wzrokowa 100% (1 lekcja). Słuchowa i praktyczna: nie masz jeszcze wyników.",
    );
  });

  test("a tie of the highest average names both, in the order V, A, K", () => {
    const forms = {
      V: row({ first_try_lessons: 3, average: 60 }),
      A: row({ first_try_lessons: 5, average: 80 }),
      K: row({ first_try_lessons: 2, average: 80 }),
    };
    assert.equal(
      explain.formTableConclusion(forms, "neutral"),
      "Najwyższa średnia: słuchowa 80% (5 lekcji) i praktyczna 80% (2 lekcje). Wzrokowa: 60% (3 lekcje).",
    );
  });

  test("neutral voice for the teacher", () => {
    const forms = {
      V: row({ first_try_lessons: 2, average: 75 }),
      A: row({ first_try_lessons: 2, average: 90 }),
      K: row(),
    };
    assert.equal(
      explain.formTableConclusion(forms, "neutral"),
      "Najwyższa średnia: słuchowa 90% (2 lekcje). Wzrokowa: 75% (2 lekcje). Praktyczna: brak wyników.",
    );
  });
});

describe("statsSummaryItems", () => {
  test("numbers with Polish plural captions", () => {
    const items = explain.statsSummaryItems({
      passed_lessons: 5,
      attempts: 2,
      average: 84,
      counted: 4,
      streak: 1,
    });
    assert.deepEqual(items, [
      { value: "5", label: "zaliczonych lekcji" },
      { value: "2", label: "rozwiązane quizy" },
      { value: "84%", label: "średnia z pierwszych podejść (4 lekcje)" },
      { value: "1", label: "zaliczona lekcja z rzędu" },
    ]);
  });

  test("before the first quiz", () => {
    const items = explain.statsSummaryItems({
      passed_lessons: 0,
      attempts: 0,
      average: null,
      counted: 0,
      streak: 0,
    });
    assert.equal(items[2].value, "–");
    assert.equal(items[2].label, "średnia z pierwszych podejść");
    assert.equal(items[1].label, "rozwiązanych quizów");
  });
});

describe("table cells", () => {
  test("below the threshold and status words", () => {
    assert.equal(explain.tooFewText(1), "za mało danych (n = 1)");
    assert.equal(explain.formStatusText(true), "potwierdzona wynikami");
    assert.equal(explain.formStatusText(false), "tylko z ankiety");
    assert.equal(explain.activeStyleText(), "Twój styl");
    assert.equal(explain.formUiLabel("K"), "Praktyczna (K)");
  });
});
