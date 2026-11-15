/**
 * The only place where codes and numbers from the backend become Polish
 * sentences (journal, suggestions, proposals, trials, praise, hints).
 * Used by the student's screens and by the teacher's view of a student.
 */
import { FORMS, type Form } from "@/features/content/types";
import type { HistoryEvent } from "@/features/progress/chart-data";
import type { TrialCancel } from "@/features/progress/journal-data";
import type {
  ClearedLesson,
  JournalEntry,
  Percentages,
  StatsSummary,
} from "@/features/progress/types";
import { plural } from "@/shared/lib/plural";

import type {
  Attention,
  CourseHint,
  FormStats,
  FormTable,
  LearningProfile,
  LessonRef,
  Praise,
  Proposal,
  ProposalEvidence,
  RetryStrength,
  RetrySuggestion,
  StyleSource,
  Trial,
  TrialResult,
} from "./types";

// --- Rules of the backend (`learning_style/rules.py`), shown to the student ---

export const PASS_THRESHOLD = 70;
export const STEP = 10;
export const TRIAL_LESSONS = 2;
export const HELPED_GAIN = 10;
export const REVERT_DROP = 10;

// Stage 10 (`learning_style/stats.py`, `rules.py`)
export const FIRST_TRY_MIN_LESSONS = 2;
export const ATTENTION_STREAK = 3;

// --- Names of forms and styles ---
// One name per form in the interface: wzrokowa / słuchowa / praktyczna (V / A / K).
// The older name of K is used only in the documentation.

/** "forma wzrokowa" */
const FORM_ADJ: Record<Form, string> = {
  V: "wzrokowa",
  A: "słuchowa",
  K: "praktyczna",
};

/** "w formie wzrokowej", "udział formy wzrokowej" */
const FORM_ADJ_LOC: Record<Form, string> = {
  V: "wzrokowej",
  A: "słuchowej",
  K: "praktycznej",
};

/** "Wersję wzrokową…", "formę wzrokową" */
const FORM_ADJ_ACC: Record<Form, string> = {
  V: "wzrokową",
  A: "słuchową",
  K: "praktyczną",
};

/** "styl wzrokowy" */
const STYLE_ADJ: Record<Form, string> = {
  V: "wzrokowy",
  A: "słuchowy",
  K: "praktyczny",
};

/** "powrót do stylu wzrokowego" */
const STYLE_ADJ_GEN: Record<Form, string> = {
  V: "wzrokowego",
  A: "słuchowego",
  K: "praktycznego",
};

export const STYLE_DESCRIPTIONS: Record<Form, string> = {
  V: "Najłatwiej uczysz się z obrazów, schematów, wykresów i filmów.",
  A: "Najłatwiej uczysz się, słuchając wyjaśnień i nagrań.",
  K: "Najłatwiej uczysz się, działając: przez ćwiczenia, przykłady i próby.",
};

/** "wzrokowa (V)" */
export function formName(form: Form): string {
  return `${FORM_ADJ[form]} (${form})`;
}

/** "Wzrokowa (V)" */
export function formLabel(form: Form): string {
  return capitalize(formName(form));
}

/** "wzrokowa" - the bare name of the form. */
export function formShort(form: Form): string {
  return FORM_ADJ[form];
}

/** "w formie wzrokowej" */
export function inForm(form: Form): string {
  return `w formie ${FORM_ADJ_LOC[form]}`;
}

/** "formy wzrokowej" */
function ofForm(form: Form): string {
  return `formy ${FORM_ADJ_LOC[form]}`;
}

/**
 * D57, the line above a lesson: "Wzrokowa (Twój styl)" or
 * "Słuchowa (wybrana dla tej lekcji)".
 */
export function lessonFormText(form: Form, chosen: boolean): string {
  return `${capitalize(FORM_ADJ[form])} (${chosen ? "wybrana dla tej lekcji" : "Twój styl"})`;
}

/** "wzrokowy (V)" */
export function styleName(form: Form): string {
  return `${STYLE_ADJ[form]} (${form})`;
}

export function styleSourceText(source: StyleSource | null): string {
  switch (source) {
    case "survey":
      return "z ankiety";
    case "tie_choice":
      return "wybrany przy remisie w ankiecie";
    case "manual":
      return "zmieniony ręcznie";
    case "proposal":
      return "po przyjęciu propozycji systemu";
    default:
      return "";
  }
}

// --- Numbers ---

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

/** "1 lekcja", "2 lekcje", "5 lekcji" */
export function lessonsText(count: number): string {
  return `${count} ${plural(count, "lekcja", "lekcje", "lekcji")}`;
}

/** "1 uczeń", "3 uczniów" */
export function studentsText(count: number): string {
  return `${count} ${plural(count, "uczeń", "uczniów", "uczniów")}`;
}

function percent(value: number | null | undefined): string {
  return value === null || value === undefined ? "–" : `${value}%`;
}

/** "V 45% · A 40% · K 15%" */
export function percentagesText(percentages: Percentages): string {
  return FORMS.map((form) => `${form} ${percentages[form]}%`).join(" · ");
}

/** "V 9 · A 8 · K 3" (survey points) */
export function pointsText(points: Percentages): string {
  return FORMS.map((form) => `${form} ${points[form]}`).join(" · ");
}

/** "Udział formy słuchowej: 47% → 57%." */
export function percentChangeText(
  form: Form,
  before: Percentages,
  after: Percentages,
): string {
  return `Udział ${ofForm(form)}: ${before[form]}% → ${after[form]}%.`;
}

/** "w 1 lekcji", "w 3 lekcjach" */
function inLessonsText(count: number): string {
  return count === 1 ? "w 1 lekcji" : `w ${count} lekcjach`;
}

// --- Quiz result ---

/** "4 z 5 (80%)" with the verdict. */
export function quizScoreText(
  correct: number,
  total: number,
  value: number,
  passed: boolean,
): string {
  return passed
    ? `Zaliczone: ${correct} z ${total} (${value}%)`
    : `Jeszcze niezaliczone: ${correct} z ${total} (${value}%). Zaliczenie od ${PASS_THRESHOLD}%`;
}

type ChangeData = {
  form: Form;
  counted: boolean;
  passed: boolean;
  percentages_before: Percentages;
  percentages_after: Percentages;
  unlocked_lesson: LessonRef | null;
  course_completed?: boolean;
};

/**
 * "Co to zmieniło", sentences: ["Udział formy słuchowej: 47% → 57%.",
 * "Lekcja 4 jest już otwarta."] or ["Procenty form bez zmian."].
 */
export function quizChangeParts(change: ChangeData): string[] {
  const { form, percentages_before: before, percentages_after: after } = change;
  const parts: string[] = [];
  if (!change.counted) {
    parts.push("Procenty form bez zmian.");
  } else if (before[form] === after[form]) {
    // R2: the form is already at its limit
    parts.push(
      change.passed
        ? `Udział ${ofForm(form)}: ${after[form]}%, to już najwyższa możliwa wartość.`
        : `Udział ${ofForm(form)}: ${after[form]}%, to już najniższa możliwa wartość.`,
    );
  } else {
    parts.push(percentChangeText(form, before, after));
  }
  if (change.unlocked_lesson) {
    parts.push(`Lekcja ${change.unlocked_lesson.number} jest już otwarta.`);
  }
  if (change.course_completed) {
    parts.push("Kurs ukończony.");
  }
  return parts;
}

/**
 * What the result did to the profile, without the mechanics (the rule with
 * numbers is in "Mój styl").
 */
export function quizChangeRule(
  counted: boolean,
  passed: boolean,
  form: Form,
): string {
  if (!counted) {
    return "To kolejne podejście do tej lekcji w tej formie. Profil zmienia tylko pierwsze.";
  }
  return passed
    ? `Ten wynik podniósł udział ${ofForm(form)} w Twoim profilu.`
    : `Ten wynik obniżył udział ${ofForm(form)} w Twoim profilu.`;
}

/** R4: "3 lekcje z rzędu zaliczone w formie wzrokowej, średni wynik 87%" */
export function praiseText(praise: Praise): string {
  return `${lessonsText(praise.streak)} z rzędu zaliczone ${inForm(praise.form)}, średni wynik ${praise.average}%`;
}

// --- R5: retry in another form ---

type Voice = "student" | "neutral";

const ORDINALS = ["pierwszym", "drugim", "trzecim"];

function surveyRank(form: Form, survey: Percentages): string | null {
  const sorted = [...FORMS].sort(
    (a, b) => survey[b] - survey[a] || FORMS.indexOf(a) - FORMS.indexOf(b),
  );
  return ORDINALS[sorted.indexOf(form)] ?? null;
}

/** Events and answers written before stage 10 have no `strength`. */
export function suggestionStrength(suggestion: RetrySuggestion): RetryStrength {
  return suggestion.strength ?? "strong";
}

/** R5 soft: the main action after the quiz. */
export const SOFT_RETRY_ACTION = "Rozwiąż jeszcze raz";

/**
 * R5 soft, the calm second option, split around its links:
 * after the quiz "Możesz też [przerobić tę lekcję w formie słuchowej]."; above
 * the lesson "Możesz [rozwiązać quiz jeszcze raz] albo [przerobić …]."
 */
export const SOFT_RETRY_TEXT = {
  afterQuiz: "Możesz też",
  inLesson: "Możesz",
  quizLink: "rozwiązać quiz jeszcze raz",
  or: "albo",
};

/** The link of the soft option: "przerobić tę lekcję w formie słuchowej" */
export function softSuggestionLink(form: Form): string {
  return `przerobić tę lekcję ${inForm(form)}`;
}

/** "Spróbuj tej lekcji w formie słuchowej" */
export function suggestionTitle(suggestion: RetrySuggestion): string {
  return `Spróbuj tej lekcji ${inForm(suggestion.suggested.form)}`;
}

/** "Przerób tę lekcję w formie słuchowej" */
export function suggestionAction(form: Form): string {
  return `Przerób tę lekcję ${inForm(form)}`;
}

/**
 * The reason with numbers, in full sentences, e.g. "W formie wzrokowej masz w
 * tym quizie 40%, w poprzedniej lekcji 40%. W formie słuchowej masz zaliczoną
 * lekcję „Wzór i wykres” (80%)."
 * `survey` (percentages of the survey) gives the place of the form in it.
 */
export function suggestionReason(
  suggestion: RetrySuggestion,
  options: { survey?: Percentages | null; voice?: Voice } = {},
): string {
  const { failed, suggested } = suggestion;
  const student = (options.voice ?? "student") === "student";

  const previous = failed.previous
    ? `, w poprzedniej lekcji ${failed.previous.percent}%`
    : "";
  const failedText = student
    ? `${capitalize(inForm(failed.form))} masz w tym quizie ${failed.percent}%${previous}.`
    : `${capitalize(inForm(failed.form))} wynik tego quizu to ${failed.percent}%${previous}.`;

  const where = capitalize(inForm(suggested.form));
  let suggestedText: string;
  if (suggested.reason === "confirmed") {
    suggestedText = suggested.best
      ? student
        ? `${where} masz zaliczoną lekcję „${suggested.best.lesson_title}” (${suggested.best.percent}%).`
        : `${where} lekcja „${suggested.best.lesson_title}” jest zaliczona na ${suggested.best.percent}%.`
      : `Forma ${FORM_ADJ[suggested.form]} jest potwierdzona wynikami, w profilu ma ${suggested.percent}%.`;
  } else {
    const rank = options.survey
      ? surveyRank(suggested.form, options.survey)
      : null;
    const survey = student ? "W Twojej ankiecie" : "W ankiecie";
    const place = rank
      ? `${survey} forma ${FORM_ADJ[suggested.form]} była na ${rank} miejscu (${suggested.survey_percent}%).`
      : `${survey} forma ${FORM_ADJ[suggested.form]} miała ${suggested.survey_percent}%.`;
    suggestedText = student
      ? `${place} Nie masz jeszcze wyników w tej formie.`
      : `${place} W tej formie nie ma jeszcze wyników.`;
  }
  return `${failedText} ${suggestedText}`;
}

// --- R6 / R7: proposals ---

/**
 * "W formie wzrokowej: 3 lekcje, średnio 53%. W formie słuchowej: 1 lekcja,
 * średnio 80%."
 */
export function proposalEvidenceText(evidence: ProposalEvidence): string {
  const parts: string[] = [];
  // Revert (R7): the drop of the average comes first, form statistics after it
  if (
    evidence.before_average !== undefined ||
    evidence.after_average !== undefined
  ) {
    parts.push(
      `Średnia przed zmianą: ${percent(evidence.before_average)}, po zmianie: ${percent(evidence.after_average)}.`,
    );
  }
  for (const side of [evidence.from, evidence.to]) {
    if (side) {
      parts.push(
        `${capitalize(inForm(side.form))}: ${lessonsText(side.lessons)}, średnio ${percent(side.average)}.`,
      );
    }
  }
  return parts.join(" ");
}

/** The question of the banner. */
export function proposalTitle(proposal: Proposal): string {
  return proposal.kind === "revert"
    ? `Po zmianie stylu wyniki są słabsze. Wrócić do stylu ${STYLE_ADJ_GEN[proposal.to]}?`
    : `${capitalize(inForm(proposal.to))} idzie Ci lepiej. Zmienić styl na ${STYLE_ADJ[proposal.to]}?`;
}

/** What accepting will do. */
export function proposalEffect(proposal: Proposal): string {
  const base = `Lekcje, które nie są jeszcze zaliczone, dostaniesz ${inForm(proposal.to)}. Procenty się nie zmienią.`;
  return proposal.kind === "revert"
    ? base
    : `${base} Po ${lessonsText(TRIAL_LESSONS)} w nowej formie zobaczysz, czy zmiana pomogła.`;
}

// --- R7: trial ---

/** "1 z 2 lekcji w nowej formie" */
export function trialProgressText(trial: Trial): string {
  return `${trial.done} z ${trial.needed} lekcji w nowej formie`;
}

/**
 * D60: no results in the previous form, e.g. "W formie wzrokowej nie było
 * wyników do porównania. Po 2 lekcjach w nowej formie pojawi się jej średnia".
 */
export function noBaselineText(from: Form): string {
  return `${capitalize(inForm(from))} nie było wyników do porównania. Po ${lessonsText(TRIAL_LESSONS)} w nowej formie pojawi się jej średnia`;
}

/** D60, a replaced trial keeps its baseline: "… średnia 80% w formie słuchowej" */
export function keptBaselineText(from: Form, before: number | null): string {
  return before === null
    ? noBaselineText(from)
    : `Do porównania zostaje średnia z poprzedniego okresu: ${before}% ${inForm(from)}`;
}

/** "Zmiana pomogła: średnia 40% → 90%" */
export function trialOutcomeText(
  result: TrialResult,
  before: number | null,
  after: number | null,
  from?: Form,
): string {
  switch (result) {
    case "helped":
      return `Zmiana pomogła: średnia ${percent(before)} → ${percent(after)}`;
    case "neutral":
      return `Bez wyraźnej różnicy: średnia ${percent(before)} → ${percent(after)}`;
    case "worse":
      return `Po zmianie wyniki są słabsze: średnia ${percent(before)} → ${percent(after)}`;
    case "no_baseline":
      return from
        ? `${capitalize(inForm(from))} nie było wyników do porównania. Średnia w nowej formie: ${percent(after)}`
        : `Średnia w nowej formie: ${percent(after)}`;
  }
}

/** The thresholds of R7 ("Mój styl" only: the place for the rules). */
export function trialRuleText(): string {
  return `Po ${lessonsText(TRIAL_LESSONS)} w nowej formie jej średnia jest porównywana z wcześniejszą. Wzrost o co najmniej ${HELPED_GAIN} punktów oznacza, że zmiana pomogła. Przy spadku o ${REVERT_DROP} punktów lub więcej pojawi się propozycja powrotu do poprzedniego stylu. Wynik pomiędzy to „bez wyraźnej różnicy”.`;
}

/** "Okres próbny stylu słuchowego (A): 1 z 2 lekcji w nowej formie. Średnia przed zmianą: 40%." */
export function trialStatusText(trial: Trial): string {
  if (trial.result) {
    return trialOutcomeText(
      trial.result,
      trial.before_average,
      trial.after_average,
      trial.from,
    );
  }
  const before =
    trial.before_average === null
      ? `${noBaselineText(trial.from)}.`
      : `Średnia przed zmianą: ${trial.before_average}% ${inForm(trial.from)}.`;
  return `${capitalize(trialProgressText(trial))}. ${before}`;
}

// --- R8: hint of the course ---

/** "W tym kursie najlepiej wypada forma słuchowa (średnio 85%, 3 uczniów)" */
export function hintText(hint: CourseHint): string {
  return `W tym kursie najlepiej wypada forma ${FORM_ADJ[hint.form]} (średnio ${hint.average}%, ${studentsText(hint.students)})`;
}

// --- R3: forms of the profile ---

/** "potwierdzona wynikami (2 lekcje, średnio 88%)" / "tylko z ankiety" */
export function formStatsText(stats: FormStats | undefined): string {
  if (!stats) {
    return "tylko z ankiety";
  }
  const numbers =
    stats.lessons > 0
      ? ` (${lessonsText(stats.lessons)}, średnio ${percent(stats.average)})`
      : "";
  if (stats.confirmed) {
    return `potwierdzona wynikami${numbers}`;
  }
  return stats.lessons > 0
    ? `jeszcze bez zaliczenia${numbers}`
    : "tylko z ankiety";
}

// --- R10: locked lesson ---

export function lockedLessonText(number: number): string {
  return `Najpierw zalicz lekcję ${number}`;
}

// --- R6: cleared choices of the form after a change of the style ---

/** "Wcześniejszy wybór formy usunięty w 2 lekcjach („A”, „B”), obowiązuje w nich teraz forma słuchowa." */
export function clearedLessonsText(cleared: ClearedLesson[], to: Form): string {
  if (cleared.length === 0) {
    return "";
  }
  const titles = cleared.map((lesson) => `„${lesson.lesson_title}”`).join(", ");
  return `Wcześniejszy wybór formy usunięty ${inLessonsText(cleared.length)} (${titles}), obowiązuje w ${cleared.length === 1 ? "niej" : "nich"} teraz forma ${FORM_ADJ[to]}.`;
}

// --- D60: a change of the style undone before the first lesson ---

/** "Zmiana na styl wzrokowy (V) cofnięta przed pierwszą lekcją, znów obowiązuje styl słuchowy (A)" */
export function styleChangeRevertedText(from: Form, to: Form): string {
  return `Zmiana na styl ${styleName(from)} cofnięta przed pierwszą lekcją, znów obowiązuje styl ${styleName(to)}`;
}

// --- Stage 10: statistics of "Moje postępy" ---

export type SummaryItem = { value: string; label: string };

/** One row of 4 numbers: passed lessons, solved quizzes, average, streak. */
export function statsSummaryItems(summary: StatsSummary): SummaryItem[] {
  const { passed_lessons, attempts, average, counted, streak } = summary;
  return [
    {
      value: String(passed_lessons),
      label: plural(
        passed_lessons,
        "zaliczona lekcja",
        "zaliczone lekcje",
        "zaliczonych lekcji",
      ),
    },
    {
      value: String(attempts),
      label: plural(
        attempts,
        "rozwiązany quiz",
        "rozwiązane quizy",
        "rozwiązanych quizów",
      ),
    },
    {
      value: percent(average),
      label:
        counted > 0
          ? `średnia z pierwszych podejść (${lessonsText(counted)})`
          : "średnia z pierwszych podejść",
    },
    {
      value: String(streak),
      label: plural(
        streak,
        "zaliczona lekcja z rzędu",
        "zaliczone lekcje z rzędu",
        "zaliczonych lekcji z rzędu",
      ),
    },
  ];
}

/** A cell below the data threshold: "za mało danych (n = 1)". */
export function tooFewText(n: number): string {
  return `za mało danych (n = ${n})`;
}

/** Status of a form in words (R3). */
export function formStatusText(confirmed: boolean): string {
  return confirmed ? "potwierdzona wynikami" : "tylko z ankiety";
}

/** Next to the active style in the table of forms. */
export function activeStyleText(voice: Voice = "student"): string {
  return voice === "student" ? "Twój styl" : "styl ucznia";
}

/**
 * One sentence under the table of forms, only facts from it, e.g.
 * "Najwyższa średnia: słuchowa 84% (4 lekcje). Wzrokowa: 70% (2 lekcje).
 * Praktyczna: nie masz jeszcze wyników."
 */
export function formTableConclusion(
  forms: FormTable,
  voice: Voice = "student",
): string {
  const student = voice === "student";
  const withAverage = FORMS.filter((form) => forms[form].average !== null);
  if (withAverage.length === 0) {
    return student
      ? "Nie masz jeszcze wyników quizów w żadnej formie."
      : "Brak wyników quizów w żadnej formie.";
  }
  const averageOf = (form: Form) => forms[form].average ?? 0;
  const describe = (form: Form) =>
    `${averageOf(form)}% (${lessonsText(forms[form].first_try_lessons)})`;

  // Highest average first; a tie keeps the order V, A, K
  const sorted = [...withAverage].sort(
    (a, b) =>
      averageOf(b) - averageOf(a) || FORMS.indexOf(a) - FORMS.indexOf(b),
  );
  const top = sorted.filter((form) => averageOf(form) === averageOf(sorted[0]));
  const rest = sorted.filter((form) => !top.includes(form));
  const without = FORMS.filter((form) => forms[form].average === null);

  const lead =
    withAverage.length === 1
      ? "Średnia z pierwszych podejść"
      : "Najwyższa średnia";
  const parts = [
    `${lead}: ${top.map((form) => `${FORM_ADJ[form]} ${describe(form)}`).join(" i ")}.`,
    ...rest.map((form) => `${capitalize(FORM_ADJ[form])}: ${describe(form)}.`),
  ];
  if (without.length > 0) {
    const names = capitalize(without.map((form) => FORM_ADJ[form]).join(" i "));
    parts.push(
      `${names}: ${student ? "nie masz jeszcze wyników" : "brak wyników"}.`,
    );
  }
  return parts.join(" ");
}

// --- Stage 10, R12: a series of failed counted results ---

/** "Trzy ostatnie lekcje poniżej progu (55%, 40%, 50%)." - also for the teacher. */
export function attentionSeries(attention: Attention): string {
  const percents = attention.results
    .map((result) => `${result.percent}%`)
    .join(", ");
  if (attention.streak === ATTENTION_STREAK) {
    return `Trzy ostatnie lekcje poniżej progu (${percents}).`;
  }
  const lessons = plural(
    attention.streak,
    "ostatnia lekcja",
    "ostatnie lekcje",
    "ostatnich lekcji",
  );
  return `${attention.streak} ${lessons} poniżej progu, trzy najnowsze: ${percents}.`;
}

/**
 * The message for the student: "Trzy ostatnie lekcje poniżej progu
 * (55%, 40%, 50%). Spróbuj innej formy albo poproś nauczyciela o pomoc."
 */
export function attentionText(attention: Attention): string {
  return `${attentionSeries(attention)} Spróbuj innej formy albo poproś nauczyciela o pomoc.`;
}

// --- The teacher's view of a student ---

export type SummaryLine = { label: string; text: string };

/** Style and its source, an open proposal and the trial, in a neutral voice. */
export function profileSummaryLines(profile: LearningProfile): SummaryLine[] {
  const lines: SummaryLine[] = [];
  if (!profile.survey_completed) {
    lines.push({ label: "Styl", text: "uczeń nie wypełnił jeszcze ankiety" });
  } else if (!profile.style) {
    lines.push({
      label: "Styl",
      text: "remis w ankiecie, uczeń jeszcze nie wybrał stylu",
    });
  } else {
    const source = styleSourceText(profile.style_source);
    lines.push({
      label: "Styl",
      text: source
        ? `${styleName(profile.style)}, ${source}`
        : styleName(profile.style),
    });
  }
  if (profile.open_proposal) {
    const { kind, to, evidence } = profile.open_proposal;
    const evidenceText = proposalEvidenceText(evidence);
    lines.push({
      label: "Otwarta propozycja",
      text: `${kind === "revert" ? "powrót do stylu" : "zmiana stylu na"} ${styleName(to)}${evidenceText ? `. ${evidenceText}` : ""}`,
    });
  }
  if (profile.trial) {
    lines.push({
      label: profile.trial.result ? "Ostatni okres próbny" : "Okres próbny",
      text: `${styleName(profile.trial.from)} → ${styleName(profile.trial.to)}: ${trialStatusText(profile.trial)}`,
    });
  }
  return lines;
}

// --- D62: chart and table of "Moje postępy" ---

/** Under the X axis: "Ankieta", "L1 · A". */
export function historyAxisLabel(event: HistoryEvent): string {
  switch (event.kind) {
    case "survey":
      return "Ankieta";
    case "quiz":
      return event.lessonNumber !== null
        ? `L${event.lessonNumber} · ${event.form}`
        : `Quiz · ${event.form}`;
    default:
      return "Zmiana";
  }
}

/** Column "Zdarzenie": "Quiz: Pętla for, forma A, 100%", "Zmiana stylu na V (ręcznie)". */
export function historyEventText(event: HistoryEvent): string {
  switch (event.kind) {
    case "survey":
      return "Ankieta";
    case "quiz":
      return `Quiz${event.lessonTitle ? `: ${event.lessonTitle}` : ""}, forma ${event.form}, ${event.percent}%`;
    case "tie":
      return `Wybór stylu przy remisie: ${event.style}`;
    case "style":
      return event.source === "manual"
        ? `Zmiana stylu na ${event.style} (ręcznie)`
        : event.source === "proposal"
          ? `Zmiana stylu na ${event.style} (propozycja systemu)`
          : `Zmiana stylu na ${event.style}`;
    case "revert":
      return `Zmiana cofnięta, znów styl ${event.style}`;
    case "other":
      return "Zmiana procentów";
  }
}

/** Label of a vertical marker: "styl V". */
export function styleMarkerText(style: Form): string {
  return `styl ${style}`;
}

// --- Decision journal ---

function proposalName(kind: "switch" | "revert", to: Form): string {
  return kind === "revert"
    ? `powrotu do stylu ${STYLE_ADJ_GEN[to]} (${to})`
    : `zmiany stylu na ${styleName(to)}`;
}

function joinSentences(...parts: string[]): string {
  return parts.filter(Boolean).join(" ");
}

const JOURNAL_LABELS: Record<JournalEntry["type"], string> = {
  survey_completed: "Ankieta",
  tie_resolved: "Wybór stylu",
  quiz_attempt: "Quiz",
  retry_suggestion: "Sugestia",
  lesson_form_changed: "Forma lekcji",
  proposal_created: "Propozycja",
  proposal_accepted: "Zmiana stylu",
  proposal_rejected: "Propozycja",
  proposal_expired: "Propozycja",
  manual_style_change: "Zmiana stylu",
  style_change_reverted: "Zmiana stylu",
  trial_started: "Okres próbny",
  trial_finished: "Okres próbny",
  praise: "Pochwała",
  attention_needed: "Wymaga uwagi",
};

/** Short kind of the entry, e.g. "Quiz", "Sugestia". */
export function journalLabel(entry: JournalEntry): string {
  return JOURNAL_LABELS[entry.type] ?? "Zdarzenie";
}

/** What the journal knows from other entries (see `progress/journal-data.ts`). */
export type JournalContext = {
  /** Trials cancelled later, by `trial_id`. */
  cancelledTrials?: Map<number, TrialCancel>;
};

const TRIAL_CANCEL_TEXT: Record<TrialCancel, string> = {
  reverted: "Anulowany: zmiana stylu cofnięta przed pierwszą lekcją.",
  replaced: "Anulowany: przed pierwszą lekcją styl zmieniony ponownie.",
};

/** One entry of the journal as sentences; neutral voice (also for the teacher). */
export function journalText(
  entry: JournalEntry,
  context: JournalContext = {},
): string {
  switch (entry.type) {
    case "survey_completed": {
      const { percentages, style, tie_styles } = entry.data;
      return joinSentences(
        `Ankieta: ${percentagesText(percentages)}.`,
        style
          ? `Styl startowy: ${styleName(style)}.`
          : `Remis (${tie_styles.join(", ")}), styl do wyboru.`,
      );
    }
    case "tie_resolved":
      return `Wybór stylu przy remisie (${entry.data.tie_styles.join(", ")}): ${styleName(entry.data.style)}.`;
    case "quiz_attempt": {
      const data = entry.data;
      return joinSentences(
        `Quiz ${inForm(data.form)}: ${data.percent}%, ${data.passed ? "zaliczony" : "niezaliczony"}.`,
        ...quizChangeParts(data),
      );
    }
    case "retry_suggestion":
      return joinSentences(
        suggestionStrength(entry.data) === "soft"
          ? `Sugestia: rozwiązać quiz jeszcze raz albo przerobić lekcję ${inForm(entry.data.suggested.form)}.`
          : `Sugestia: przerobić lekcję ${inForm(entry.data.suggested.form)}.`,
        suggestionReason(entry.data, { voice: "neutral" }),
      );
    case "lesson_form_changed":
      return `Forma lekcji: ${FORM_ADJ[entry.data.from]} → ${FORM_ADJ[entry.data.to]} (${entry.data.source === "suggestion" ? "według sugestii" : "wybór ręczny"}).`;
    case "proposal_created":
      return joinSentences(
        `Propozycja ${proposalName(entry.data.kind, entry.data.to)}.`,
        proposalEvidenceText(entry.data.evidence),
      );
    case "proposal_accepted":
      return joinSentences(
        `Przyjęta propozycja: styl ${styleName(entry.data.from)} → ${styleName(entry.data.to)}.`,
        clearedLessonsText(entry.data.cleared_lessons, entry.data.to),
      );
    case "proposal_rejected":
      return `Odrzucona propozycja ${proposalName(entry.data.kind, entry.data.to)}.`;
    case "proposal_expired":
      return `Propozycja ${proposalName(entry.data.kind, entry.data.to)} wygasła, bo jej warunek przestał być spełniony.`;
    case "manual_style_change":
      return joinSentences(
        `Ręczna zmiana stylu: ${styleName(entry.data.from)} → ${styleName(entry.data.to)}.`,
        entry.data.superseded_proposal_id
          ? "Otwarta propozycja zmiany stylu została zamknięta."
          : "",
        clearedLessonsText(entry.data.cleared_lessons, entry.data.to),
      );
    case "style_change_reverted":
      return joinSentences(
        `${styleChangeRevertedText(entry.data.from, entry.data.to)}.`,
        "Okres próbny anulowany, nowy się nie zaczyna.",
        clearedLessonsText(entry.data.cleared_lessons, entry.data.to),
      );
    case "trial_started": {
      const { trial_id, from, to, before_average, replaced_trial_id } =
        entry.data;
      const cancel = context.cancelledTrials?.get(trial_id);
      return joinSentences(
        `Okres próbny stylu ${STYLE_ADJ_GEN[to]} (${to}): ${lessonsText(TRIAL_LESSONS)}.`,
        replaced_trial_id
          ? `Zastępuje okres bez lekcji. ${keptBaselineText(from, before_average)}.`
          : before_average === null
            ? `${noBaselineText(from)}.`
            : `Średnia przed zmianą: ${before_average}% ${inForm(from)}.`,
        cancel ? TRIAL_CANCEL_TEXT[cancel] : "",
      );
    }
    case "praise":
      return `Pochwała: ${praiseText(entry.data)}.`;
    case "attention_needed": {
      const results = entry.data.results
        .map((result) => `„${result.lesson_title}” ${result.percent}%`)
        .join(", ");
      return joinSentences(
        `${capitalize(lessonsText(entry.data.streak))} z rzędu poniżej progu: ${results}.`,
        "Wskazówka po tej serii: inna forma lekcji albo pomoc nauczyciela.",
      );
    }
    case "trial_finished":
      return joinSentences(
        `Koniec okresu próbnego stylu ${STYLE_ADJ_GEN[entry.data.to]} (${entry.data.to}).`,
        `${trialOutcomeText(entry.data.result, entry.data.before_average, entry.data.after_average, entry.data.from)}.`,
        entry.data.result === "worse"
          ? `Propozycja powrotu do stylu ${STYLE_ADJ_GEN[entry.data.from]}.`
          : "",
      );
    default: {
      // A type added on the server later: show the code rather than nothing
      const unknown = entry as { type: string };
      return `Zdarzenie: ${unknown.type}.`;
    }
  }
}

// --- Course panel statistics (teacher, stage 10; `learning_style/stats.py`, `assessment/stats.py`) ---

export const LESSON_MIN_STUDENTS = 3;
export const MATRIX_MIN_RESULTS = 2;
export const FORM_GAP = 20;
export const QUESTION_MIN_DRAWS = 5;
export const HARD_BELOW = 40;
export const EASY_ABOVE = 90;

/** Name of a form in the course panel: "praktyczna" for K. */
export function panelFormName(form: Form): string {
  return FORM_ADJ[form];
}

/** "za mało danych (n = 2)" */
export function notEnoughDataText(n: number): string {
  return `za mało danych (n = ${n})`;
}

/** "2,1": one decimal with a Polish comma. */
export function decimalText(value: number): string {
  return value.toFixed(1).replace(".", ",");
}

/** "lekcja 3 „Miejsce zerowe”" */
function panelLessonName(lesson: { number: number; title: string }): string {
  return `lekcja ${lesson.number} „${lesson.title}”`;
}

/** "1 podejścia", "2 podejść", "2,1 podejścia" (genitive, after "średnio"). */
function attemptsGenitive(value: number): string {
  if (!Number.isInteger(value)) {
    return `${decimalText(value)} podejścia`;
  }
  return `${value} ${plural(value, "podejścia", "podejść", "podejść")}`;
}

type HardestLesson = {
  number: number;
  title: string;
  started: number;
  passed: number;
  pass_rate: number | null;
  attempts_to_pass: number | null;
};

/** The sentence under "Które lekcje sprawiają trudność" (`hardest`). */
export function hardestLessonText(
  hardest: HardestLesson | null,
  lessons: { started: number }[],
): string {
  if (hardest === null) {
    if (lessons.length === 0) {
      return "Kurs nie ma jeszcze opublikowanych lekcji.";
    }
    return lessons.some((lesson) => lesson.started >= LESSON_MIN_STUDENTS)
      ? `Każdą lekcję z co najmniej ${LESSON_MIN_STUDENTS} uczniami zaliczyli wszyscy, którzy ją rozpoczęli.`
      : `Za mało danych, żeby wskazać najtrudniejszą lekcję: żadnej lekcji nie rozpoczęło jeszcze ${LESSON_MIN_STUDENTS} uczniów.`;
  }
  const name = panelLessonName(hardest);
  const { started, passed } = hardest;
  if (passed === 0) {
    return `Najtrudniejsza jest ${name}: nie zaliczył jej żaden z ${started} uczniów, którzy ją rozpoczęli.`;
  }
  const verb = passed === 1 ? "zaliczył" : "zaliczyło";
  const rate = hardest.pass_rate === null ? "" : ` (${hardest.pass_rate}%)`;
  const head = `Najtrudniejsza jest ${name}: ${verb} ją ${passed} z ${started} uczniów${rate}.`;
  if (hardest.attempts_to_pass === null) {
    return head;
  }
  const attempts = attemptsGenitive(hardest.attempts_to_pass);
  return passed === 1
    ? `${head} Uczeń, który ją zaliczył, potrzebował ${attempts}.`
    : `${head} Uczniowie, którzy ją zaliczyli, potrzebowali średnio ${attempts}.`;
}

/** "trudne" / "łatwe" / "w normie"; below 5 draws "za mało danych (n = 3)". */
export function questionRatingText(
  rating: "hard" | "easy" | "normal" | null,
  drawn: number,
): string {
  switch (rating) {
    case "hard":
      return "trudne";
    case "easy":
      return "łatwe";
    case "normal":
      return "w normie";
    default:
      return notEnoughDataText(drawn);
  }
}

/** "6 pytań, w tym 2 trudne"; a lesson without a quiz: "bez quizu". */
export function questionSummaryText(
  questions: { rating: "hard" | "easy" | "normal" | null }[],
): string {
  const count = questions.length;
  if (count === 0) {
    return "bez quizu";
  }
  const all = `${count} ${plural(count, "pytanie", "pytania", "pytań")}`;
  const hard = questions.filter(
    (question) => question.rating === "hard",
  ).length;
  return hard === 0
    ? all
    : `${all}, w tym ${hard} ${plural(hard, "trudne", "trudne", "trudnych")}`;
}

type MatrixCellLike = { average: number | null; n: number };

/** "88% · 4"; below 2 results the cell shows a dash (`average` is null). */
export function matrixCellText(cell: MatrixCellLike): string | null {
  return cell.average === null ? null : `${cell.average}% · ${cell.n}`;
}

type FormGapLike = {
  number: number;
  title: string;
  best: { form: Form; average: number; n: number };
  worst: { form: Form; average: number; n: number };
};

/** One lesson whose forms differ by at least 20 points. */
export function formGapText(gap: FormGapLike): string {
  const { best, worst } = gap;
  return (
    `W lekcji ${gap.number} „${gap.title}” forma ${FORM_ADJ[best.form]} ma średnio ${best.average}% (n = ${best.n}), ` +
    `a ${FORM_ADJ[worst.form]} ${worst.average}% (n = ${worst.n}). ` +
    `Sprawdź wersję ${FORM_ADJ_ACC[worst.form]} tej lekcji.`
  );
}

/** Sentences under "W jakiej formie działa każda lekcja". */
export function matrixConclusions(
  matrix: { cells: Record<Form, MatrixCellLike> }[],
  gaps: FormGapLike[],
): string[] {
  if (gaps.length > 0) {
    return gaps.map(formGapText);
  }
  if (matrix.length === 0) {
    return ["Kurs nie ma jeszcze opublikowanych lekcji."];
  }
  const comparable = matrix.filter(
    (row) =>
      FORMS.filter((form) => row.cells[form].average !== null).length >= 2,
  ).length;
  if (comparable === 0) {
    return [
      `Za mało wyników, żeby porównać formy: średnia w komórce pojawia się od ${MATRIX_MIN_RESULTS} wyników.`,
    ];
  }
  return [
    comparable === matrix.length
      ? "Formy działają podobnie we wszystkich lekcjach."
      : `Formy działają podobnie we wszystkich lekcjach, które da się porównać (${comparable} z ${matrix.length}).`,
  ];
}

/** R12 at the student in the course table: "wymaga uwagi: 55%, 40%, 50%". */
export function attentionNoteText(attention: {
  results: { percent: number }[];
}): string {
  const results = attention.results.map((result) => `${result.percent}%`);
  return `wymaga uwagi: ${results.join(", ")}`;
}
