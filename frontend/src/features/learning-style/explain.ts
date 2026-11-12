/**
 * The only place where codes and numbers from the backend become Polish
 * sentences (journal, suggestions, proposals, trials, praise, hints).
 * Used by the student's screens and by the teacher's view of a student.
 */
import { FORMS, type Form } from "@/features/content/types";
import type {
  ClearedLesson,
  JournalEntry,
  Percentages,
} from "@/features/progress/types";
import { plural } from "@/shared/lib/plural";

import type {
  CourseHint,
  FormStats,
  LessonRef,
  Praise,
  Proposal,
  ProposalEvidence,
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

// --- Names of forms and styles ---

/** "forma wzrokowa" */
const FORM_ADJ: Record<Form, string> = {
  V: "wzrokowa",
  A: "słuchowa",
  K: "kinestetyczna",
};

/** "w formie wzrokowej" */
const FORM_ADJ_LOC: Record<Form, string> = {
  V: "wzrokowej",
  A: "słuchowej",
  K: "kinestetycznej",
};

/** "Wzrokowe 45% → 55%" (materials in this form) */
const FORM_PLURAL: Record<Form, string> = {
  V: "Wzrokowe",
  A: "Słuchowe",
  K: "Kinestetyczne",
};

/** "styl wzrokowy" */
const STYLE_ADJ: Record<Form, string> = {
  V: "wzrokowy",
  A: "słuchowy",
  K: "kinestetyczny",
};

/** "powrót do stylu wzrokowego" */
const STYLE_ADJ_GEN: Record<Form, string> = {
  V: "wzrokowego",
  A: "słuchowego",
  K: "kinestetycznego",
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

/** "Wzrokowe" - short name in lists of numbers. */
export function formShort(form: Form): string {
  return FORM_PLURAL[form];
}

/** "w formie wzrokowej" */
export function inForm(form: Form): string {
  return `w formie ${FORM_ADJ_LOC[form]}`;
}

/** "Wzrokowej (A)" for "Przerabiasz tę lekcję w formie: …" */
export function inFormLabel(form: Form): string {
  return `${capitalize(FORM_ADJ_LOC[form])} (${form})`;
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

/** "Słuchowe 47% → 57%" */
export function percentChangeText(
  form: Form,
  before: Percentages,
  after: Percentages,
): string {
  return `${FORM_PLURAL[form]} ${before[form]}% → ${after[form]}%`;
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
    : `Jeszcze nie: ${correct} z ${total} (${value}%) – zaliczenie od ${PASS_THRESHOLD}%`;
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
 * "Co to zmieniło": ["Słuchowe 47% → 57%", "Lekcja 4 odblokowana"]
 * or ["To kolejne podejście w tej formie – procenty bez zmian"].
 */
export function quizChangeParts(change: ChangeData): string[] {
  const { form, percentages_before: before, percentages_after: after } = change;
  const parts: string[] = [];
  if (!change.counted) {
    parts.push("To kolejne podejście w tej formie – procenty bez zmian");
  } else if (before[form] === after[form]) {
    // R2: the form is already at its limit
    parts.push(
      change.passed
        ? `${FORM_PLURAL[form]} ${after[form]}% – to już maksimum`
        : `${FORM_PLURAL[form]} ${after[form]}% – to już minimum`,
    );
  } else {
    parts.push(percentChangeText(form, before, after));
  }
  if (change.unlocked_lesson) {
    parts.push(`Lekcja ${change.unlocked_lesson.number} odblokowana`);
  }
  if (change.course_completed) {
    parts.push("Kurs ukończony");
  }
  return parts;
}

/** Why the percentages changed (or not), for the result of a quiz. */
export function quizChangeRule(counted: boolean, passed: boolean): string {
  if (!counted) {
    return "Procenty zmienia tylko pierwsze podejście w danej formie w danej lekcji.";
  }
  return passed
    ? `Pierwsze podejście w tej formie zaliczone: forma +${STEP} punktów, pozostałe dwie oddają je proporcjonalnie.`
    : `Pierwsze podejście w tej formie niezaliczone: forma −${STEP} punktów, pozostałe dwie dostają je proporcjonalnie.`;
}

/** R4: "3 lekcje z rzędu zaliczone w formie wzrokowej, średnio 87%" */
export function praiseText(praise: Praise): string {
  return `${lessonsText(praise.streak)} z rzędu zaliczone ${inForm(praise.form)}, średnio ${praise.average}%`;
}

// --- R5: retry in another form ---

type Voice = "student" | "neutral";

const ORDINALS = ["pierwsze", "drugie", "trzecie"];

function surveyRank(form: Form, survey: Percentages): string | null {
  const sorted = [...FORMS].sort(
    (a, b) => survey[b] - survey[a] || FORMS.indexOf(a) - FORMS.indexOf(b),
  );
  return ORDINALS[sorted.indexOf(form)] ?? null;
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
 * The reason with numbers, e.g. "Wzrokowe: ten quiz 40%, poprzednia lekcja 40%.
 * Słuchowe zaliczyłeś w lekcji „Wzór i wykres” na 80%."
 * `survey` (percentages of the survey) lets us say which place the form had.
 */
export function suggestionReason(
  suggestion: RetrySuggestion,
  options: { survey?: Percentages | null; voice?: Voice } = {},
): string {
  const { failed, suggested } = suggestion;
  const student = (options.voice ?? "student") === "student";

  let failedText = `${FORM_PLURAL[failed.form]}: ten quiz ${failed.percent}%`;
  if (failed.previous) {
    failedText += `, poprzednia lekcja ${failed.previous.percent}%`;
  }
  failedText += ".";

  const name = FORM_PLURAL[suggested.form];
  let suggestedText: string;
  if (suggested.reason === "confirmed") {
    suggestedText = suggested.best
      ? student
        ? `${name} zaliczyłeś w lekcji „${suggested.best.lesson_title}” na ${suggested.best.percent}%.`
        : `${name}: lekcja „${suggested.best.lesson_title}” zaliczona na ${suggested.best.percent}%.`
      : `${name} są potwierdzone wynikami (${suggested.percent}%).`;
  } else {
    const rank = options.survey
      ? surveyRank(suggested.form, options.survey)
      : null;
    const where = student ? "w Twojej ankiecie" : "w ankiecie";
    const place = rank
      ? `${name} były ${rank} ${where} (${suggested.survey_percent}%)`
      : `${name} miały ${where} ${suggested.survey_percent}%`;
    suggestedText = `${place}, nie mamy jeszcze o nich wyników – warto sprawdzić.`;
  }
  return `${failedText} ${suggestedText}`;
}

// --- R6 / R7: proposals ---

/** "Wzrokowe: 3 lekcje, średnio 53% · Słuchowe: 1 lekcja, średnio 80%" */
export function proposalEvidenceText(evidence: ProposalEvidence): string {
  const parts: string[] = [];
  for (const side of [evidence.from, evidence.to]) {
    if (side) {
      parts.push(
        `${FORM_PLURAL[side.form]}: ${lessonsText(side.lessons)}, średnio ${percent(side.average)}`,
      );
    }
  }
  if (parts.length > 0) {
    return parts.join(" · ");
  }
  if (
    evidence.before_average !== undefined ||
    evidence.after_average !== undefined
  ) {
    return `Średnia przed zmianą ${percent(evidence.before_average)}, po zmianie ${percent(evidence.after_average)}`;
  }
  return "";
}

/** The question of the banner. */
export function proposalTitle(proposal: Proposal): string {
  return proposal.kind === "revert"
    ? `Po zmianie stylu wyniki są słabsze – wrócić do stylu ${STYLE_ADJ_GEN[proposal.to]}?`
    : `Lepiej idzie Ci ${inForm(proposal.to)} – przełączyć styl na stałe?`;
}

/** What accepting will do. */
export function proposalEffect(proposal: Proposal): string {
  const base = `Lekcje, których jeszcze nie zaliczyłeś, będą ${inForm(proposal.to)}.`;
  return proposal.kind === "revert"
    ? `${base} Procenty się nie zmienią.`
    : `${base} Procenty się nie zmienią, a przez ${lessonsText(TRIAL_LESSONS)} sprawdzimy, czy zmiana pomogła.`;
}

// --- R7: trial ---

/** "1 z 2 lekcji w nowej formie" */
export function trialProgressText(trial: Trial): string {
  return `${trial.done} z ${trial.needed} lekcji w nowej formie`;
}

/** "Zmiana pomogła: średnia 40% → 90%" */
export function trialOutcomeText(
  result: TrialResult,
  before: number | null,
  after: number | null,
): string {
  switch (result) {
    case "helped":
      return `Zmiana pomogła: średnia ${percent(before)} → ${percent(after)}`;
    case "neutral":
      return `Bez wyraźnej różnicy: średnia ${percent(before)} → ${percent(after)}`;
    case "worse":
      return `Po zmianie wyniki są słabsze: średnia ${percent(before)} → ${percent(after)}`;
    case "no_baseline":
      return `Średnia w nowej formie: ${percent(after)}`;
  }
}

/** The thresholds of R7 in one sentence. */
export function trialRuleText(): string {
  return `Po ${TRIAL_LESSONS} lekcjach w nowej formie porównujemy średnią z wcześniejszą: wzrost o co najmniej ${HELPED_GAIN} punktów – zmiana pomogła; spadek o ${REVERT_DROP} lub więcej – zaproponujemy powrót; pomiędzy – bez wyraźnej różnicy.`;
}

/** "Okres próbny stylu słuchowego (A): 1 z 2 lekcji w nowej formie. Średnia przed zmianą: 40%." */
export function trialStatusText(trial: Trial): string {
  if (trial.result) {
    return trialOutcomeText(
      trial.result,
      trial.before_average,
      trial.after_average,
    );
  }
  const before =
    trial.before_average === null
      ? "Nie ma wcześniejszych wyników do porównania."
      : `Średnia przed zmianą: ${trial.before_average}%.`;
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

/** "Wybory formy wyczyszczone w 2 lekcjach („A”, „B”) – obowiązuje teraz forma słuchowa." */
export function clearedLessonsText(cleared: ClearedLesson[], to: Form): string {
  if (cleared.length === 0) {
    return "";
  }
  const titles = cleared.map((lesson) => `„${lesson.lesson_title}”`).join(", ");
  return `Wybory formy wyczyszczone ${inLessonsText(cleared.length)} (${titles}) – obowiązuje teraz forma ${FORM_ADJ[to]}.`;
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
  trial_started: "Okres próbny",
  trial_finished: "Okres próbny",
};

/** Short kind of the entry, e.g. "Quiz", "Sugestia". */
export function journalLabel(entry: JournalEntry): string {
  return JOURNAL_LABELS[entry.type] ?? "Zdarzenie";
}

/** One entry of the journal as sentences; neutral voice (also for the teacher). */
export function journalText(entry: JournalEntry): string {
  switch (entry.type) {
    case "survey_completed": {
      const { percentages, style, tie_styles } = entry.data;
      return joinSentences(
        `Ankieta: ${percentagesText(percentages)}.`,
        style
          ? `Styl startowy: ${styleName(style)}.`
          : `Remis (${tie_styles.join(", ")}) – styl do wyboru.`,
      );
    }
    case "tie_resolved":
      return `Wybór stylu przy remisie (${entry.data.tie_styles.join(", ")}): ${styleName(entry.data.style)}.`;
    case "quiz_attempt": {
      const data = entry.data;
      return joinSentences(
        `Quiz ${inForm(data.form)}: ${data.percent}% – ${data.passed ? "zaliczony" : "niezaliczony"}.`,
        `${quizChangeParts(data).join(" · ")}.`,
      );
    }
    case "retry_suggestion":
      return joinSentences(
        `Sugestia: przerobić lekcję ${inForm(entry.data.suggested.form)}.`,
        suggestionReason(entry.data, { voice: "neutral" }),
      );
    case "lesson_form_changed":
      return `Forma lekcji: ${FORM_ADJ[entry.data.from]} → ${FORM_ADJ[entry.data.to]} (${entry.data.source === "suggestion" ? "według sugestii" : "wybór ręczny"}).`;
    case "proposal_created":
      return joinSentences(
        `Propozycja ${proposalName(entry.data.kind, entry.data.to)}.`,
        proposalEvidenceText(entry.data.evidence)
          ? `${proposalEvidenceText(entry.data.evidence)}.`
          : "",
      );
    case "proposal_accepted":
      return joinSentences(
        `Przyjęta propozycja: styl ${styleName(entry.data.from)} → ${styleName(entry.data.to)}.`,
        clearedLessonsText(entry.data.cleared_lessons, entry.data.to),
      );
    case "proposal_rejected":
      return `Odrzucona propozycja ${proposalName(entry.data.kind, entry.data.to)}.`;
    case "proposal_expired":
      return `Propozycja ${proposalName(entry.data.kind, entry.data.to)} wygasła – jej warunek przestał obowiązywać.`;
    case "manual_style_change":
      return joinSentences(
        `Ręczna zmiana stylu: ${styleName(entry.data.from)} → ${styleName(entry.data.to)}.`,
        clearedLessonsText(entry.data.cleared_lessons, entry.data.to),
      );
    case "trial_started":
      return joinSentences(
        `Okres próbny stylu ${STYLE_ADJ_GEN[entry.data.to]} (${entry.data.to}): ${lessonsText(TRIAL_LESSONS)}.`,
        entry.data.before_average === null
          ? "Brak wcześniejszych wyników do porównania."
          : `Średnia przed zmianą: ${entry.data.before_average}%.`,
      );
    case "trial_finished":
      return joinSentences(
        `Koniec okresu próbnego stylu ${STYLE_ADJ_GEN[entry.data.to]} (${entry.data.to}).`,
        `${trialOutcomeText(entry.data.result, entry.data.before_average, entry.data.after_average)}.`,
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
