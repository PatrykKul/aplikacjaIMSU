// Test of the course panel sentences ("Course panel statistics" in
// `learning-style/explain.ts`) with Node's test runner:
//   node --test src/features/teach/course-panel-text.test.mjs   (or: npm test)
// `explain.ts` imports other modules (`@/…`), so each imported TypeScript file
// is transpiled to a temporary .mjs file and the import paths are rewritten.

import assert from "node:assert/strict";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, describe, test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";

import ts from "typescript";

const src = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
let dir;
let text;

// --- Loader: TypeScript module with its local imports → temporary .mjs files ---

function resolveSource(specifier, from) {
  const base = specifier.startsWith("@/")
    ? path.join(src, specifier.slice(2))
    : path.resolve(path.dirname(from), specifier);
  const file = [`${base}.ts`, path.join(base, "index.ts")].find(existsSync);
  if (!file) {
    throw new Error(`Cannot resolve ${specifier} from ${from}`);
  }
  return file;
}

function emit(file, done = new Map()) {
  if (done.has(file)) {
    return done.get(file);
  }
  const out = path.join(dir, `${done.size}-${path.basename(file, ".ts")}.mjs`);
  done.set(file, out);
  const { outputText } = ts.transpileModule(readFileSync(file, "utf8"), {
    compilerOptions: {
      module: ts.ModuleKind.ESNext,
      target: ts.ScriptTarget.ES2020,
      verbatimModuleSyntax: false,
    },
  });
  // Type-only imports are gone after transpiling; the rest are local modules
  const code = outputText.replace(
    /(from\s+|import\s+)"((?:@\/|\.{1,2}\/)[^"]+)"/g,
    (_, keyword, specifier) =>
      `${keyword}${JSON.stringify(pathToFileURL(emit(resolveSource(specifier, file), done)).href)}`,
  );
  writeFileSync(out, code);
  return out;
}

before(async () => {
  dir = mkdtempSync(path.join(tmpdir(), "course-panel-text-"));
  const entry = emit(path.join(src, "features/learning-style/explain.ts"));
  text = await import(pathToFileURL(entry).href);
});

after(() => rmSync(dir, { recursive: true, force: true }));

// --- Numbers ---

describe("numbers", () => {
  test("one decimal with a Polish comma", () => {
    assert.equal(text.decimalText(2.1), "2,1");
    assert.equal(text.decimalText(1), "1,0");
    assert.equal(text.decimalText(3.25), "3,3");
  });

  test("too few data with n", () => {
    assert.equal(text.notEnoughDataText(2), "za mało danych (n = 2)");
  });

  test("K is called praktyczna", () => {
    assert.equal(text.panelFormName("K"), "praktyczna");
  });
});

// --- (4) Hardest lesson ---

const lesson = (overrides) => ({
  number: 3,
  title: "Miejsce zerowe",
  started: 7,
  passed: 4,
  pass_rate: 57,
  attempts_to_pass: 2.1,
  ...overrides,
});

describe("hardest lesson", () => {
  test("pass rate and average attempts", () => {
    assert.equal(
      text.hardestLessonText(lesson(), [lesson()]),
      "Najtrudniejsza jest lekcja 3 „Miejsce zerowe”: zaliczyło ją 4 z 7 uczniów (57%). Uczniowie, którzy ją zaliczyli, potrzebowali średnio 2,1 podejścia.",
    );
  });

  test("whole numbers of attempts take the plural", () => {
    const two = lesson({ attempts_to_pass: 2 });
    assert.match(text.hardestLessonText(two, [two]), /średnio 2 podejść\.$/);
    const one = lesson({ attempts_to_pass: 1 });
    assert.match(text.hardestLessonText(one, [one]), /średnio 1 podejścia\.$/);
  });

  test("one student passed", () => {
    const row = lesson({
      started: 3,
      passed: 1,
      pass_rate: 33,
      attempts_to_pass: 3,
    });
    assert.equal(
      text.hardestLessonText(row, [row]),
      "Najtrudniejsza jest lekcja 3 „Miejsce zerowe”: zaliczył ją 1 z 3 uczniów (33%). Uczeń, który ją zaliczył, potrzebował 3 podejść.",
    );
  });

  test("nobody passed", () => {
    const row = lesson({
      started: 5,
      passed: 0,
      pass_rate: 0,
      attempts_to_pass: null,
    });
    assert.equal(
      text.hardestLessonText(row, [row]),
      "Najtrudniejsza jest lekcja 3 „Miejsce zerowe”: nie zaliczył jej żaden z 5 uczniów, którzy ją rozpoczęli.",
    );
  });

  test("no hardest: no lessons, too few students, everybody passed", () => {
    assert.equal(
      text.hardestLessonText(null, []),
      "Kurs nie ma jeszcze opublikowanych lekcji.",
    );
    assert.equal(
      text.hardestLessonText(null, [{ started: 2 }, { started: 0 }]),
      "Za mało danych, żeby wskazać najtrudniejszą lekcję: żadnej lekcji nie rozpoczęło jeszcze 3 uczniów.",
    );
    assert.equal(
      text.hardestLessonText(null, [{ started: 3 }, { started: 1 }]),
      "Każdą lekcję z co najmniej 3 uczniami zaliczyli wszyscy, którzy ją rozpoczęli.",
    );
  });
});
