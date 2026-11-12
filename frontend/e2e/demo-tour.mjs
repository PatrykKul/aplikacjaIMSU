// Walk through the demo show on every demo account and save a screenshot of each screen.
//
// Needs: backend on :8001 with fresh demo data (`python -m app.demo.seed --reset-students`),
// frontend on :3001, Playwright (not a project dependency):
//   npm i playwright && npx playwright install chromium   (in any folder)
//   set PLAYWRIGHT_MODULE=<that folder>\node_modules\playwright\index.js
//   node e2e/demo-tour.mjs [output dir]
// After the run: `--reset-students` again (the tour changes the demo accounts).

import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_MODULE ?? "playwright");

const APP = process.env.APP_URL ?? "http://localhost:3001";
const API = process.env.API_URL ?? "http://localhost:8001";
const PASSWORD = "Demo123!";
const OUT = path.resolve(process.argv[2] ?? "../docs/zrzuty-v3");
const DESKTOP = { width: 1440, height: 900 };
const PHONE = { width: 390, height: 844 };

mkdirSync(OUT, { recursive: true });
let shot = 0;
const problems = [];

// --- Helpers -------------------------------------------------------------------------------

async function snap(page, name) {
  shot += 1;
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(400);
  const file = path.join(OUT, `${String(shot).padStart(2, "0")}-${name}.png`);
  await page.screenshot({ path: file, fullPage: true });
  const overflow = await page.evaluate(
    () =>
      document.documentElement.scrollWidth >
      document.documentElement.clientWidth,
  );
  if (overflow) problems.push(`${name}: horizontal scroll`);
  console.log(`  ${path.basename(file)}`);
}

async function session(browser, email, viewport = DESKTOP) {
  const context = await browser.newContext({ viewport, locale: "pl-PL" });
  const page = await context.newPage();
  page.on("pageerror", (error) => problems.push(`${email}: ${error.message}`));
  page.on("response", (response) => {
    if (response.status() >= 500) {
      problems.push(`${email}: ${response.status()} ${response.url()}`);
    }
  });
  if (email) {
    await page.goto(`${APP}/login`);
    await page.getByLabel("E-mail").fill(email);
    await page.getByLabel("Hasło", { exact: true }).fill(PASSWORD);
    await page.getByRole("button", { name: "Zaloguj się" }).click();
    await page.waitForURL((url) => !url.pathname.startsWith("/login"));
  }
  return { context, page };
}

async function apiAs(email) {
  const login = await fetch(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password: PASSWORD }),
  });
  const cookie = login.headers.get("set-cookie").split(";")[0];
  return async (pathname) => {
    const response = await fetch(`${API}${pathname}`, { headers: { cookie } });
    if (!response.ok) throw new Error(`${pathname}: ${response.status}`);
    return response.json();
  };
}

/** Answer the drawn questions: `correct` of them right, the rest wrong. */
async function answerQuiz(page, key, correct) {
  const quiz = page.locator("form", {
    has: page.getByRole("button", { name: /Sprawdź|Odpowiedz/ }),
  });
  const questions = quiz.locator("fieldset");
  await questions.first().waitFor();
  const count = await questions.count();
  for (let index = 0; index < count; index += 1) {
    const fieldset = questions.nth(index);
    const legend = (await fieldset.locator("legend").innerText()).replace(
      /^\d+\.\s*/,
      "",
    );
    const question = key.find((item) => item.text === legend.trim());
    if (!question) throw new Error(`question not in the pool: ${legend}`);
    const right = question.answers.find(
      (answer) => answer.id === question.correct_answer_id,
    );
    const wrong = question.answers.find(
      (answer) => answer.id !== question.correct_answer_id,
    );
    const answer = index < correct ? right : wrong;
    // Exact text: "3" must not match the answer "−3"
    await fieldset
      .locator("label")
      .filter({ has: page.getByText(answer.text, { exact: true }) })
      .first()
      .click();
  }
  await page.getByRole("button", { name: "Sprawdź", exact: true }).click();
  await page.getByText("Co to zmieniło").first().waitFor();
}

// --- Tour ----------------------------------------------------------------------------------

const browser = await chromium.launch();
const teacherApi = await apiAs("nauczyciel.demo@imsu.pl");
const courses = await teacherApi("/courses");
const math = courses.find((course) => course.title.startsWith("Matematyka"));
const mathDetail = await teacherApi(`/courses/${math.id}`);
const zeroLesson = mathDetail.lessons.find((lesson) => lesson.number === 3);
const firstLesson = mathDetail.lessons.find((lesson) => lesson.number === 1);
const zeroKey = (await teacherApi(`/lessons/${zeroLesson.id}/quiz/edit`))
  .questions;
// D55: Programowanie belongs to its own teacher
const PROG_TEACHER = "nauczyciel.programowanie@imsu.pl";
const progApi = await apiAs(PROG_TEACHER);
const prog = (await progApi("/courses")).find((course) =>
  course.title.startsWith("Programowanie"),
);
const progDetail = await progApi(`/courses/${prog.id}`);
const progFirst = progDetail.lessons.find((lesson) => lesson.number === 1);
const adminApi = await apiAs("admin.demo@imsu.pl");
const progTeacher = (await adminApi("/users?role=teacher")).find(
  (user) => user.email === PROG_TEACHER,
);

/** Fails the run (without stopping it) when a check does not hold. */
function expect(condition, message) {
  if (!condition) problems.push(message);
}

/** Admin: pick a teacher in "Zmień właściciela" and go to the confirmation. */
async function changeOwner(page, course, option) {
  await page
    .getByRole("button", { name: `Zmień właściciela: ${course.title}` })
    .click();
  await page.getByRole("combobox").click();
  await page.getByRole("option", { name: option }).click();
}

console.log("Gość");
{
  const { context, page } = await session(browser, null);
  await page.goto(APP);
  await snap(page, "strona-startowa");
  await context.close();
}

console.log("uczen.nowy: ankieta, katalog, prośba o zapis");
{
  const { context, page } = await session(browser, "uczen.nowy@imsu.pl");
  await page.goto(`${APP}/courses`);
  await page.waitForURL(/\/survey/);
  await snap(page, "ola-ankieta-wymagana");
  const questions = page.locator("fieldset");
  const count = await questions.count();
  for (let index = 0; index < count; index += 1) {
    // Mostly the second answer, sometimes the first: a mixed but repeatable result
    const labels = questions.nth(index).locator("label");
    await labels.nth(index % 4 === 0 ? 0 : 1).click();
  }
  await page.getByRole("button", { name: "Zobacz wynik" }).click();
  await page.waitForURL(/\/survey\/result/);
  await snap(page, "ola-wynik-ankiety");
  const tie = page.getByRole("button", { name: "Wybieram ten styl" });
  if (await tie.isVisible().catch(() => false)) {
    await page.getByRole("radio").first().click();
    await tie.click();
    await snap(page, "ola-wybor-przy-remisie");
  }
  await page.goto(`${APP}/courses`);
  await snap(page, "ola-katalog");
  const english = page.locator("li", { hasText: "Angielski: Present Perfect" });
  await english.getByRole("button", { name: "Zapisz się" }).click();
  await english.getByText(/Prośba wysłana/).waitFor();
  await snap(page, "ola-prosba-wyslana");
  await context.close();
}

console.log("nauczyciel.nowy: czeka na zatwierdzenie");
{
  const { context, page } = await session(browser, "nauczyciel.nowy@imsu.pl");
  await page.goto(`${APP}/teach`);
  await page.waitForURL(/\/pending/);
  await snap(page, "piotr-czeka-na-zatwierdzenie");
  await context.close();
}

console.log("admin.demo: zatwierdzenie nauczyciela");
{
  const { context, page } = await session(browser, "admin.demo@imsu.pl");
  await page.goto(`${APP}/admin/users`);
  await page.getByRole("tab", { name: "Nauczyciele" }).click();
  await page.getByRole("button", { name: /Czekające/ }).click();
  await snap(page, "admin-czekajacy-nauczyciele");
  await page.getByRole("button", { name: "Zatwierdź" }).first().click();
  // The approved teacher leaves the "waiting" filter
  await page.getByRole("button", { name: /Czekające \(0\)/ }).waitFor();
  await page.getByRole("button", { name: /Wszyscy/ }).click();
  await page
    .locator("tr", { hasText: "Piotr" })
    .getByText("Zatwierdzone")
    .waitFor();
  await snap(page, "admin-nauczyciel-zatwierdzony");
  await page.goto(`${APP}/courses`);
  await snap(page, "admin-kursy");
  await context.close();
}

console.log(
  "admin.demo: zmiana właściciela Programowania na Annę i z powrotem",
);
{
  const { context, page } = await session(browser, "admin.demo@imsu.pl");
  await page.goto(`${APP}/courses`);
  await changeOwner(page, prog, /Anna Nowak/);
  await snap(page, "admin-zmiana-wlasciciela-wybor");
  await page.getByRole("button", { name: "Dalej" }).click();
  await snap(page, "admin-zmiana-wlasciciela-potwierdzenie");
  await page
    .getByRole("button", { name: "Zmień właściciela", exact: true })
    .click();
  const row = page.locator("li", { hasText: prog.title });
  await row.getByText(/^Anna Nowak ·/).waitFor();
  await snap(page, "admin-zmiana-wlasciciela-po");

  // Anna sees the course in her panel right away
  const anna = await session(browser, "nauczyciel.demo@imsu.pl");
  await anna.page.goto(`${APP}/teach`);
  await anna.page.getByText(prog.title).first().waitFor();
  await snap(anna.page, "anna-przejety-kurs-programowania");
  await anna.context.close();

  // And back to the teacher of Programowanie
  await changeOwner(page, prog, new RegExp(`\\(${PROG_TEACHER}\\)`));
  await page.getByRole("button", { name: "Dalej" }).click();
  await page
    .getByRole("button", { name: "Zmień właściciela", exact: true })
    .click();
  await row.getByText(`${progTeacher.display_name} ·`).waitFor();
  const restored = await adminApi(`/courses/${prog.id}`);
  expect(
    restored.owner.id === progTeacher.id,
    `Programowanie: owner ${restored.owner.id}, expected ${PROG_TEACHER}`,
  );
  await context.close();
}

console.log("nauczyciel.demo: kursy, edytor lekcji, panel kursu");
{
  const { context, page } = await session(browser, "nauczyciel.demo@imsu.pl");
  await page.goto(`${APP}/teach`);
  await snap(page, "anna-moje-kursy");
  await page.goto(`${APP}/teach/courses/${math.id}`);
  await snap(page, "anna-edytor-kursu");
  const editor = `${APP}/teach/courses/${math.id}/lessons/${zeroLesson.id}`;
  await page.goto(editor);
  await snap(page, "anna-lekcja-zarys-i-wnioski");
  for (const [tab, name] of [
    ["Wzrokowa (V)", "anna-lekcja-wersja-v"],
    ["Słuchowa (A)", "anna-lekcja-wersja-a"],
    ["Kinestetyczna (K)", "anna-lekcja-wersja-k"],
    ["Quiz (pula)", "anna-lekcja-pula-pytan"],
  ]) {
    await page.getByRole("tab", { name: tab }).click();
    await snap(page, name);
  }
  await page.goto(`${APP}/courses/${math.id}/lessons/${zeroLesson.id}`);
  await snap(page, "anna-podglad-lekcji");
  await page.goto(`${APP}/teach/courses/${math.id}/panel`);
  await snap(page, "anna-panel-kursu-przed");
  const request = page.locator("tr", { hasText: "Zosia Mazur" });
  await request.getByRole("button", { name: "Przyjmij" }).click();
  await page.waitForTimeout(800);
  await snap(page, "anna-panel-kursu-po-przyjeciu");
  await context.close();
}

console.log("uczen.zapis: podpowiedź z kursu");
{
  const { context, page } = await session(browser, "uczen.zapis@imsu.pl");
  await page.goto(`${APP}/courses`);
  await page.getByText(/Kontynuuj: Lekcja 1 – /).waitFor();
  await snap(page, "zosia-moje-kursy");
  await page.goto(`${APP}/courses/${math.id}`);
  await page.getByText(/najlepiej wypada/).waitFor();
  // D57: the first lesson starts, the second waits for it
  await page.getByRole("link", { name: /^Rozpocznij lekcję 1:/ }).waitFor();
  await page.getByText("Najpierw zalicz lekcję 1").first().waitFor();
  await snap(page, "zosia-kurs-z-podpowiedzia");
  await page.goto(`${APP}/courses/${math.id}/lessons/${firstLesson.id}`);
  await page.getByText(/Słuchowa \(Twój styl\)/).waitFor();
  await snap(page, "zosia-lekcja-1-wersja-a");
  // D58: several short recordings, each with a collapsed transcript
  const recordings = await page.locator("audio").count();
  const transcripts = page.locator("summary", { hasText: "Transkrypcja" });
  expect(recordings >= 2, `Zosia, lesson 1 (A): ${recordings} recordings`);
  expect(
    (await transcripts.count()) === recordings,
    "Zosia, lesson 1 (A): not every recording has a transcript",
  );
  // Opened from the keyboard: Enter on the focused <summary>
  await transcripts.first().focus();
  await page.keyboard.press("Enter");
  await transcripts.first().locator("xpath=..").locator("p").waitFor();
  await transcripts.first().scrollIntoViewIfNeeded();
  await snap(page, "zosia-lekcja-1-transkrypcja");
  await context.close();
}

console.log("uczen.demo: sugestia, zmiana formy, propozycja");
{
  const { context, page } = await session(browser, "uczen.demo@imsu.pl");
  await page.goto(`${APP}/profile`);
  await snap(page, "kuba-moj-styl-przed");
  await page.goto(`${APP}/courses/${math.id}`);
  await page.getByRole("link", { name: /^Powtórz lekcję 1:/ }).waitFor();
  await page.getByRole("link", { name: /lekcję 3:/ }).waitFor();
  await snap(page, "kuba-kurs");
  await page.goto(`${APP}/courses/${math.id}/lessons/${zeroLesson.id}`);
  await page.getByText(/Wzrokowa \(Twój styl\)/).waitFor();
  await snap(page, "kuba-lekcja-3-wersja-v");
  await answerQuiz(page, zeroKey, 2);
  await snap(page, "kuba-quiz-niezaliczony-sugestia");
  await page
    .getByRole("button", { name: /Przerób tę lekcję w formie słuchowej/ })
    .first()
    .click();
  await page
    .getByText(/Słuchowa \(wybrana dla tej lekcji\)/)
    .first()
    .waitFor();
  await snap(page, "kuba-lekcja-3-wersja-a");
  await answerQuiz(page, zeroKey, 4);
  await snap(page, "kuba-quiz-zaliczony-propozycja");
  await page.getByRole("button", { name: "Przełącz na stałe" }).first().click();
  await page.waitForTimeout(800);
  await snap(page, "kuba-po-przelaczeniu");
  await page.goto(`${APP}/profile`);
  await snap(page, "kuba-moj-styl-po");
  await page.goto(`${APP}/progress`);
  await snap(page, "kuba-moje-postepy");
  await context.close();
}

console.log("uczen.zmiana: okres próbny, wykres, dziennik");
{
  const { context, page } = await session(browser, "uczen.zmiana@imsu.pl");
  await page.goto(`${APP}/progress`);
  await snap(page, "marta-moje-postepy");
  await page.goto(`${APP}/profile`);
  await snap(page, "marta-moj-styl");
  await context.close();
}

console.log("uczen.zmiana: blok kodu w Programowaniu");
{
  const { context, page } = await session(browser, "uczen.zmiana@imsu.pl");
  await page.goto(`${APP}/courses/${prog.id}/lessons/${progFirst.id}`);
  await page
    .getByText(/^Forma:/)
    .first()
    .waitFor();
  // The version Marta gets (her style or her choice) must show code as code
  const code = page.locator(".rich-text pre").first();
  const found = await code.waitFor({ timeout: 10_000 }).then(
    () => true,
    () => false,
  );
  expect(found, "Programowanie, lesson 1: no code block in Marta's version");
  if (found) {
    const font = await code.evaluate((el) => getComputedStyle(el).fontFamily);
    expect(/mono/i.test(font), `code block font: ${font}`);
    await code.scrollIntoViewIfNeeded();
  }
  await snap(page, "marta-programowanie-blok-kodu");
  await context.close();
}

console.log("uczen3: styl A → V → A bez lekcji (cofnięcie, D60)");
{
  const { context, page } = await session(browser, "uczen3@imsu.pl");
  await page.goto(`${APP}/profile`);
  await snap(page, "szymon-moj-styl-a");
  for (const [label, message, name] of [
    ["Wzrokowa (V)", "Twój styl: wzrokowy (V)", "szymon-moj-styl-v"],
    [
      "Słuchowa (A)",
      "Twój styl: słuchowy (A)",
      "szymon-moj-styl-cofniety-do-a",
    ],
  ]) {
    await page
      .getByRole("radiogroup")
      .locator("label", { hasText: label })
      .click();
    await page.getByRole("button", { name: "Zmień styl", exact: true }).click();
    await page
      .getByRole("alertdialog")
      .getByRole("button", { name: "Zmień styl" })
      .click();
    await page.getByText(message).first().waitFor();
    await snap(page, name);
  }
  // The bug of 12.11: no new trial "V → A" without a baseline after the revert
  expect(
    (await page.getByText(/Okres próbny: nauka w formie słuchowej/).count()) ===
      0,
    "uczen3: a new trial started after the revert",
  );
  await page.goto(`${APP}/progress`);
  // The journal entry, not the hidden SVG <title> of the chart
  await page
    .getByText(/cofnięta przed pierwszą lekcją/)
    .filter({ visible: true })
    .first()
    .waitFor();
  await page
    .getByRole("cell", { name: "Zmiana stylu na V (ręcznie)" })
    .waitFor();
  expect(
    (await page.locator("svg text", { hasText: "cofnięta" }).count()) === 1,
    "uczen3: the chart has no struck-through marker",
  );
  await snap(page, "szymon-moje-postepy");
  await context.close();
}

console.log("nauczyciel.demo: szczegóły ucznia");
{
  const { context, page } = await session(browser, "nauczyciel.demo@imsu.pl");
  await page.goto(`${APP}/teach/courses/${math.id}/panel`);
  await snap(page, "anna-panel-kursu-po-pokazie");
  await page.getByRole("link", { name: "Kuba Wiśniewski" }).first().click();
  await page.waitForURL(/\/students\//);
  await snap(page, "anna-szczegoly-ucznia-kuba");
  await context.close();
}

console.log("Telefon (390 px)");
{
  const guest = await session(browser, null, PHONE);
  await guest.page.goto(APP);
  await snap(guest.page, "telefon-strona-startowa");
  await guest.context.close();
  const marta = await session(browser, "uczen.zmiana@imsu.pl", PHONE);
  await marta.page.goto(`${APP}/progress`);
  await snap(marta.page, "telefon-marta-moje-postepy");
  await marta.page.goto(`${APP}/courses/${math.id}`);
  await snap(marta.page, "telefon-marta-katalog-kursu");
  await marta.page.goto(`${APP}/courses/${prog.id}/lessons/${progFirst.id}`);
  await marta.page
    .locator(".rich-text pre")
    .first()
    .waitFor({ timeout: 10_000 })
    .catch(() => problems.push("phone: no code block in Marta's lesson"));
  await snap(marta.page, "telefon-marta-blok-kodu");
  await marta.context.close();
  const kuba = await session(browser, "uczen.demo@imsu.pl", PHONE);
  await kuba.page.goto(`${APP}/courses/${math.id}/lessons/${zeroLesson.id}`);
  await snap(kuba.page, "telefon-kuba-lekcja");
  await kuba.context.close();
}

await browser.close();
console.log(`\n${shot} zrzutów w ${OUT}`);
if (problems.length > 0) {
  console.log("Problemy:");
  for (const problem of problems) console.log(`  - ${problem}`);
  process.exitCode = 1;
}
